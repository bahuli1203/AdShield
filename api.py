"""
AdShield FastAPI Backend
Wraps the existing analysis pipeline and serves frame images.
Run: .\\venv\\Scripts\\python api.py
Port: 8000
"""
import os
import sys
import uuid
import json
import shutil
import asyncio
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse

# ── Paths ──────────────────────────────────────────────────────────────────
BASE_DIR    = Path(__file__).parent
UPLOADS_DIR = BASE_DIR / "uploads"
FRAMES_DIR  = BASE_DIR / "frames"
RESULTS_DIR = BASE_DIR / "results"
ANNOTATED_DIR = RESULTS_DIR / "annotated"

for d in [UPLOADS_DIR, FRAMES_DIR, RESULTS_DIR, ANNOTATED_DIR]:
    d.mkdir(exist_ok=True)

# ── FastAPI App ─────────────────────────────────────────────────────────────
app = FastAPI(title="AdShield API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve frame images statically at /frames/<filename>
app.mount("/frames",    StaticFiles(directory=str(FRAMES_DIR)),    name="frames")
app.mount("/annotated", StaticFiles(directory=str(ANNOTATED_DIR)), name="annotated")


@app.get("/health")
def health():
    return {"status": "ok", "service": "AdShield API"}


@app.post("/analyse")
async def analyse_video(
    file: Optional[UploadFile] = File(None),
    url:  Optional[str]        = Form(None),
    frame_sample_rate:    float = Form(1.0),
    violation_threshold:  float = Form(0.45),
    use_object:   bool = Form(True),
    use_nsfw:     bool = Form(True),
    use_scene:    bool = Form(True),
    use_motion:   bool = Form(True),
    use_action:   bool = Form(True),
    use_anomaly:  bool = Form(True),
    mask_faces:   bool = Form(True),
    use_audio:    bool = Form(True),
):
    """
    Accept a video file upload or YouTube URL, run the full AdShield analysis,
    and return results with frame image URLs.
    """
    import config
    from modules.frame_extractor  import FrameExtractor
    from modules.object_detector  import ObjectDetector
    from modules.nsfw_detector    import NSFWDetector
    from modules.scene_classifier import SceneClassifier
    from modules.face_processor   import FaceProcessor
    from modules.score_aggregator import ScoreAggregator
    from modules.report_generator import ReportGenerator
    from modules.optical_flow     import OpticalFlowAnalyzer
    from modules.action_recognizer import ActionRecognizer
    from modules.anomaly_detector  import AnomalyDetector
    from modules.audio_analyzer    import AudioAnalyzer

    # ── Resolve video path ──────────────────────────────────────────────────
    if file:
        ext  = Path(file.filename).suffix
        dest = UPLOADS_DIR / f"{uuid.uuid4().hex}{ext}"
        with open(dest, "wb") as f:
            shutil.copyfileobj(file.file, f)
        video_path = str(dest)
    elif url:
        from modules.video_downloader import download_video_from_url
        try:
            video_path = download_video_from_url(url, str(UPLOADS_DIR))
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Download failed: {e}")
    else:
        raise HTTPException(status_code=400, detail="Provide a file or URL")

    config.VIOLATION_THRESHOLD = violation_threshold

    # ── Init modules ────────────────────────────────────────────────────────
    frame_extractor = FrameExtractor(video_path, str(FRAMES_DIR), sample_rate=frame_sample_rate)
    obj_det    = ObjectDetector()              if use_object else None
    nsfw_det   = NSFWDetector()               if use_nsfw   else None
    scene_clf  = SceneClassifier()            if use_scene  else None
    face_proc  = FaceProcessor()
    flow_anal  = OpticalFlowAnalyzer(motion_threshold=config.MOTION_THRESHOLD) if use_motion else None
    action_rec = ActionRecognizer()           if use_action else None
    anomaly_det = AnomalyDetector()           if use_anomaly else None
    audio_anal  = AudioAnalyzer()             if use_audio else None
    score_agg  = ScoreAggregator()
    report_gen = ReportGenerator(results_dir=str(RESULTS_DIR))

    # ── Extract frames ──────────────────────────────────────────────────────
    try:
        frames_meta = frame_extractor.extract()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Frame extraction failed: {e}")

    if not frames_meta:
        raise HTTPException(status_code=400, detail="No frames extracted from video")

    # ── Extract audio profile ───────────────────────────────────────────────
    audio_segments = []
    if audio_anal:
        try:
            audio_segments = audio_anal.process_video(video_path, str(RESULTS_DIR))
        except Exception as e:
            print(f"Audio analysis failed: {e}")

    all_res = []

    for i, fm in enumerate(frames_meta):
        fp = fm["frame_path"]

        b_obj = {"violation_detected": False, "confidence": 0.0, "detections": [], "contextual_hits": [], "annotated_frame_path": fp}
        if obj_det:
            try: b_obj = obj_det.analyze(fp, str(ANNOTATED_DIR))
            except: pass

        annotated_path = b_obj.get("annotated_frame_path", fp)

        b_nsfw = {"violation_detected": False, "confidence": 0.0, "categories": []}
        if nsfw_det:
            try: b_nsfw = nsfw_det.analyze(fp)
            except: pass

        b_scene = {"top_class": "Unknown", "confidence": 0.0, "is_flagged": False, "reason": ""}
        if scene_clf:
            try: b_scene = scene_clf.analyze(fp)
            except: pass

        b_motion = {"motion_score": 0.0, "mean_magnitude": 0.0, "is_high_motion": False}
        if flow_anal:
            try: b_motion = flow_anal.analyze(fp)
            except: pass

        b_face = {"faces_detected": 0, "processed_frame_path": annotated_path}
        try:
            b_face = face_proc.process(annotated_path, mask=mask_faces)
            annotated_path = b_face.get("processed_frame_path", annotated_path)
        except: pass

        b_action = {"violation_detected": False, "confidence": 0.0, "action": "Normal", "annotated_frame_path": annotated_path}
        if action_rec:
            try:
                b_action = action_rec.analyze(annotated_path, str(ANNOTATED_DIR))
                annotated_path = b_action.get("annotated_frame_path", annotated_path)
            except: pass

        b_audio = {"violation_detected": False, "confidence": 0.0, "matched_words": [], "text": ""}
        timestamp_sec = fm["timestamp"]
        for seg in audio_segments:
            # Add small 1-second buffer to the tail so the flag stays active on screen
            if seg["start"] <= timestamp_sec <= (seg["end"] + 1.0):
                b_audio["violation_detected"] = True
                b_audio["confidence"] = seg["confidence"]
                b_audio["matched_words"].extend(w for w in seg["matched_words"] if w not in b_audio["matched_words"])
                b_audio["text"] = seg["text"]

        try:
            b_agg = score_agg.aggregate(b_obj, b_nsfw, b_scene, b_motion, b_action, b_audio)
        except Exception as e:
            print(f"Aggregation failed: {e}")
            b_agg = {"final_score": 0.0, "risk_level": "SAFE", "violation_reasons": [], "signals_fired": 0, "component_scores": {}}

        all_res.append({
            "frame_index":   fm["frame_index"],
            "timestamp":     fm["timestamp"],
            "timestamp_str": fm["timestamp_str"],
            "frame_path":    fp,
            "annotated_frame_path": annotated_path,
            # ── URL paths for React frontend ──
            "frame_url":     f"/frames/{Path(fp).name}",
            "annotated_url": f"/annotated/{Path(annotated_path).name}" if annotated_path != fp else f"/frames/{Path(fp).name}",
            "object_detection":    {k: v for k, v in b_obj.items()   if "path" not in k},
            "nsfw_detection":      b_nsfw,
            "scene_classification":b_scene,
            "optical_flow":        b_motion,
            "action_recognition":  {k: v for k, v in b_action.items() if "path" not in k},
            "audio_analysis":      b_audio,
            "face_processing":     {"faces_detected": b_face.get("faces_detected", 0)},
            "aggregated":          b_agg,
        })

    # ── Anomaly detection ───────────────────────────────────────────────────
    if anomaly_det:
        try: anomaly_det.analyze_timeline(all_res)
        except: pass

    # ── Report ──────────────────────────────────────────────────────────────
    try:
        report = report_gen.generate(all_res, video_path)
    except:
        report = {}

    # ── Build timeline & signals ────────────────────────────────────────────
    timeline = [
        {"time": r["timestamp"], "score": round(r["aggregated"]["final_score"], 4), "timestamp": r["timestamp_str"]}
        for r in all_res
    ]

    signals = {
        "objectHit": any(r["object_detection"].get("violation_detected") for r in all_res),
        "nsfwHit":   any(r["nsfw_detection"].get("violation_detected")   for r in all_res),
        "sceneHit":  any(r["scene_classification"].get("is_flagged")     for r in all_res),
        "motionHit": any(r["optical_flow"].get("is_high_motion")         for r in all_res),
        "actionHit": any(r["action_recognition"].get("violation_detected") for r in all_res),
        "anomalyHit":any(r["aggregated"].get("is_anomaly")               for r in all_res),
        "audioHit":  any(r["audio_analysis"].get("violation_detected")   for r in all_res),
    }

    flagged_frames = [r for r in all_res if r["aggregated"]["final_score"] >= violation_threshold]
    flagged_segs   = report.get("flagged_segments", [])

    return {
        "overallRisk":     report.get("overall_risk", "SAFE"),
        "finalScore":      round(max((r["aggregated"]["final_score"] for r in all_res), default=0.0), 4),
        "framesAnalyzed":  len(all_res),
        "flaggedFrames":   len(flagged_frames),
        "summary":         report.get("summary_text", ""),
        "signals":         signals,
        "timeline":        timeline,
        "flaggedSegments": [
            {
                "start":     f"{s['start']:.1f}s",
                "end":       f"{s['end']:.1f}s",
                "duration":  f"{s['end']-s['start']:.1f}s",
                "peakScore": round(s["peak_score"], 4),
                "risk":      ("HIGH RISK" if s["peak_score"] >= 0.75 else "VIOLATION" if s["peak_score"] >= 0.45 else "BORDERLINE"),
                "reasons":   " | ".join(set(reason for idx in range(s["start_idx"], s["end_idx"]+1) for reason in all_res[idx]["aggregated"]["violation_reasons"]))[:200],
            }
            for s in flagged_segs
        ],
        "frames": [
            {
                "index":       r["frame_index"],
                "timestamp":   r["timestamp_str"],
                "finalScore":  round(r["aggregated"]["final_score"], 4),
                "riskLevel":   r["aggregated"].get("risk_level", "SAFE"),
                "frameUrl":    r["frame_url"],
                "annotatedUrl":r["annotated_url"],
                "severity":    r["object_detection"].get("severity", "none"),
                "label":       (r["object_detection"]["detections"][0]["class"] + " " + str(round(r["object_detection"]["detections"][0]["confidence"]*100)) + "%" if r["object_detection"].get("detections") else r["aggregated"]["violation_reasons"][0][:50] if r["aggregated"]["violation_reasons"] else ""),
                "violationReasons": r["aggregated"]["violation_reasons"],
                "detections":  r["object_detection"].get("detections", []),
            }
            for r in all_res
        ],
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)

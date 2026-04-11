import streamlit as st
import os
import json
from PIL import Image
import pandas as pd

import config
from modules.frame_extractor import FrameExtractor
from modules.object_detector import ObjectDetector
from modules.nsfw_detector import NSFWDetector
from modules.scene_classifier import SceneClassifier
from modules.face_processor import FaceProcessor
from modules.score_aggregator import ScoreAggregator
from modules.report_generator import ReportGenerator
from modules.video_downloader import download_video_from_url
from modules.optical_flow import OpticalFlowAnalyzer
from modules.audio_analyzer import AudioAnalyzer
from modules.action_recognizer import ActionRecognizer
from modules.anomaly_detector import AnomalyDetector

# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="AdShield — Policy Violation Detector",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─────────────────────────────────────────────
# CUSTOM CSS
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}

.risk-badge {
    display: inline-block;
    padding: 5px 16px;
    border-radius: 999px;
    font-weight: 700;
    font-size: 0.9rem;
    letter-spacing: 0.04em;
}
.risk-safe       { background:#d1fae5; color:#065f46; }
.risk-borderline { background:#fef9c3; color:#78350f; }
.risk-violation  { background:#ffedd5; color:#9a3412; }
.risk-high       { background:#fee2e2; color:#7f1d1d; }

.bar-track {
    background:#e5e7eb;
    border-radius:999px;
    height:10px;
    overflow:hidden;
    margin-top:4px;
}
.ts-label { font-size:0.73rem; color:#9ca3af; margin-bottom:2px; }
h2 { font-size:1.3rem !important; }
h3 { font-size:1.1rem !important; }

.module-tag {
    display:inline-block;
    font-size:0.72rem;
    padding:2px 8px;
    border-radius:6px;
    background:#1e293b;
    color:#94a3b8;
    margin:2px;
}
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────
def risk_badge(risk: str) -> str:
    cls  = {"SAFE":"risk-safe","BORDERLINE":"risk-borderline","VIOLATION":"risk-violation","HIGH RISK":"risk-high"}.get(risk,"risk-safe")
    em   = {"SAFE":"✅","BORDERLINE":"⚠️","VIOLATION":"🔴","HIGH RISK":"🚨"}.get(risk,"")
    return f"<span class='risk-badge {cls}'>{em} {risk}</span>"

def score_bar(score: float) -> str:
    pct = int(score * 100)
    color = "#10b981" if score < 0.3 else "#f59e0b" if score < 0.45 else "#f97316" if score < 0.75 else "#ef4444"
    return (f"<div class='bar-track'><div style='width:{pct}%;height:100%;"
            f"background:{color};border-radius:999px;'></div></div>")

def fmt_pct(v: float) -> str:
    return f"{v:.0%}"

def _log_error(results_dir, msg):
    try:
        with open(os.path.join(results_dir, "error_log.txt"), "a") as f:
            f.write(msg + "\n")
    except Exception:
        pass


# ─────────────────────────────────────────────
# ANALYSIS RUNNER
# ─────────────────────────────────────────────
def run_analysis(video_path: str, cfg: dict):
    proj_dir      = os.path.dirname(os.path.abspath(__file__))
    frames_dir    = os.path.join(proj_dir, "frames")
    results_dir   = os.path.join(proj_dir, "results")
    annotated_dir = os.path.join(results_dir, "annotated")
    for d in [frames_dir, results_dir, annotated_dir]:
        os.makedirs(d, exist_ok=True)

    status = st.empty()
    status.info("⚙️  Loading AI models…")

    # Init all modules
    frame_extractor  = FrameExtractor(video_path, frames_dir, sample_rate=cfg["sample_rate"])
    obj_det          = ObjectDetector()                if cfg["use_object"] else None
    nsfw_det         = NSFWDetector()                  if cfg["use_nsfw"]   else None
    scene_clf        = SceneClassifier()               if cfg["use_scene"]  else None
    face_proc        = FaceProcessor()
    flow_analyzer    = OpticalFlowAnalyzer(motion_threshold=config.MOTION_THRESHOLD) if cfg["use_motion"] else None
    audio_analyzer   = AudioAnalyzer()                if cfg["use_audio"]  else None
    action_rec       = ActionRecognizer()             if cfg["use_action"] else None
    anomaly_det      = AnomalyDetector()              if cfg["use_anomaly"] else None
    score_agg        = ScoreAggregator()
    report_gen       = ReportGenerator(results_dir=results_dir)

    # ── Audio analysis (whole video, once) ────
    audio_result = {"available": False, "transcript": "", "flagged_words": [],
                    "categories": [], "violation_detected": False, "confidence": 0.0}
    if audio_analyzer and audio_analyzer.available:
        status.info("🎵  Transcribing audio with Whisper… (this may take a minute)")
        try:
            audio_result = audio_analyzer.analyze(video_path)
        except Exception as e:
            _log_error(results_dir, f"AudioAnalyzer: {e}")

    # ── Frame extraction ───────────────────────
    status.info("📹  Extracting frames from video…")
    if flow_analyzer:
        flow_analyzer.reset()

    try:
        frames_meta = frame_extractor.extract()
    except Exception as e:
        st.error(f"Could not read video: {e}")
        return None

    total = len(frames_meta)
    if total == 0:
        st.error("No frames extracted. Please check the video file.")
        return None

    bar     = st.progress(0)
    all_res = []

    for i, fm in enumerate(frames_meta):
        fp = fm["frame_path"]
        status.info(f"🔬  Frame **{i+1}/{total}** — `{fm['timestamp_str']}`")

        # Object detection
        b_obj = {"violation_detected": False, "confidence": 0.0, "detections": [], "annotated_frame_path": fp}
        if obj_det:
            try:
                b_obj = obj_det.analyze(fp, annotated_dir)
            except Exception as e:
                _log_error(results_dir, f"ObjDet frame {i}: {e}")

        annotated_path = b_obj.get("annotated_frame_path", fp)

        # NSFW
        b_nsfw = {"violation_detected": False, "confidence": 0.0, "categories": []}
        if nsfw_det:
            try:
                b_nsfw = nsfw_det.analyze(fp)
            except Exception:
                pass

        # Scene
        b_scene = {"top_class": "Unknown", "confidence": 0.0, "is_flagged": False, "reason": ""}
        if scene_clf:
            try:
                b_scene = scene_clf.analyze(fp)
            except Exception:
                pass

        # Optical flow
        b_motion = {"motion_score": 0.0, "mean_magnitude": 0.0, "is_high_motion": False, "flow_frame_path": fp}
        if flow_analyzer:
            try:
                b_motion = flow_analyzer.analyze(fp)
            except Exception:
                pass

        # Face masking
        b_face = {"faces_detected": 0, "processed_frame_path": annotated_path}
        try:
            b_face = face_proc.process(annotated_path, mask=cfg["mask_faces"])
            annotated_path = b_face.get("processed_frame_path", annotated_path)
        except Exception:
            pass

        # Action Recognition
        b_action = {"violation_detected": False, "confidence": 0.0, "action": "Normal", "annotated_frame_path": annotated_path}
        if action_rec:
            try:
                b_action = action_rec.analyze(annotated_path, annotated_dir)
                annotated_path = b_action.get("annotated_frame_path", annotated_path)
            except Exception:
                pass

        # Score — pass audio + motion + action into aggregator
        try:
            b_agg = score_agg.aggregate(b_obj, b_nsfw, b_scene, audio_result, b_motion, b_action)
        except Exception:
            b_agg = {
                "final_score": 0.0, "risk_level": "SAFE",
                "violation_reasons": [],
                "component_scores": {"object_detection": 0.0, "nsfw_detection": 0.0,
                                     "scene_classification": 0.0, "audio": 0.0, "motion": 0.0, "action": 0.0}
            }

        all_res.append({
            "frame_index": fm["frame_index"],
            "timestamp": fm["timestamp"],
            "timestamp_str": fm["timestamp_str"],
            "frame_path": fm["frame_path"],
            "annotated_frame_path": annotated_path,
            "object_detection": b_obj,
            "nsfw_detection": b_nsfw,
            "scene_classification": b_scene,
            "optical_flow": b_motion,
            "action_recognition": b_action,
            "face_processing": b_face,
            "aggregated": b_agg,
        })
        bar.progress((i + 1) / total)

    # ── Post-processing: Anomaly Detection ────
    if anomaly_det:
        status.info("🧮  Running statistical anomaly detector…")
        try:
            anomaly_stats = anomaly_det.analyze_timeline(all_res)
        except Exception as e:
            _log_error(results_dir, f"AnomalyDetector: {e}")

    # ── Report ────────────────────────────────
    status.info("📝  Generating report…")
    try:
        report = report_gen.generate(all_res, video_path)
    except Exception as e:
        _log_error(results_dir, f"Report: {e}")
        report = {}

    status.empty()
    bar.empty()

    return {"frames": all_res, "report": report, "audio": audio_result}


# ─────────────────────────────────────────────
# SESSION STATE
# ─────────────────────────────────────────────
for key, default in [
    ("analysis_complete", False),
    ("results", {}),
    ("downloaded_url", ""),
    ("downloaded_video_path", ""),
]:
    if key not in st.session_state:
        st.session_state[key] = default


# ─────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────
c1, c2 = st.columns([1, 11])
c1.markdown("<div style='font-size:3rem;line-height:1.1'>🛡️</div>", unsafe_allow_html=True)
c2.markdown("## AdShield — Ad Policy Violation Detector")
c2.markdown("<p style='color:#6b7280;margin-top:-8px'>Multimodal AI content moderation: object detection · NSFW · scene analysis · audio transcription · motion anomaly</p>", unsafe_allow_html=True)
st.divider()


# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ Analysis Settings")
    sample_rate = st.slider("Frame sample rate (s)", 0.5, 5.0, 1.0, 0.5,
                            help="Lower = more frames analysed = slower but more thorough")
    violation_thresh = st.slider("Violation threshold", 0.2, 0.8, 0.45, 0.05,
                                 help="Score above this marks a violation")
    config.VIOLATION_THRESHOLD = violation_thresh

    st.markdown("---")
    st.markdown("### 🔬 AI Modules")
    use_object = st.toggle("🎯 Object Detection (weapons, drugs…)", value=True)
    use_nsfw   = st.toggle("🔞 NSFW Content Detection", value=True)
    use_scene  = st.toggle("🎬 Scene Classification", value=True)
    use_audio  = st.toggle("🎵 Audio Transcription & Analysis", value=True)
    use_motion = st.toggle("🌊 Optical Flow Motion Analysis", value=True)
    use_action = st.toggle("🤺 Action Recognition (Poses)", value=True)
    use_anomaly = st.toggle("🧮 Statistical Anomaly Detector", value=True)
    mask_faces = st.toggle("😷 Blur Faces for Privacy", value=True)

    st.markdown("---")
    with st.expander("ℹ️ How AdShield works"):
        st.markdown("""
**5 AI models run in parallel per frame:**

| Module | Detects |
|---|---|
| 🎯 YOLOv8 | Weapons, bottles, syringes |
| 🔞 NudeNet | Adult / explicit content |
| 🎬 MobileNetV2 | Risky scene contexts |
| 🎵 Whisper | Profanity, hate speech, drug references |
| 🌊 Optical Flow | Violent / chaotic motion spikes |
| 🤺 MediaPipe | Aggressive human actions & fighting stances |
| 🧮 Statistics | Z-Score based temporal anomaly detection |

**Risk levels:**
- ✅ SAFE — No violations
- ⚠️ BORDERLINE — Marginal concerns
- 🔴 VIOLATION — Policy breach
- 🚨 HIGH RISK — Severe violation
        """)


# ─────────────────────────────────────────────
# TABS
# ─────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs([
    "📤 Upload & Analyse",
    "📊 Results Dashboard",
    "🔎 Frame Inspector",
    "🎵 Audio Analysis",
])


# ══════════════════════════════════════════════
# TAB 1 — UPLOAD & ANALYSE
# ══════════════════════════════════════════════
with tab1:
    if st.session_state.analysis_complete:
        report = st.session_state.results["report"]
        risk   = report.get("overall_risk", "UNKNOWN")
        audio  = st.session_state.results.get("audio", {})

        if risk == "SAFE":
            st.success("✅ Analysis complete — this video appears **SAFE**.")
        elif risk == "BORDERLINE":
            st.warning("⚠️ Analysis complete — **borderline** content detected. Manual review recommended.")
        else:
            st.error(f"🚨 Analysis complete — **{risk}** detected. This video likely violates ad policies.")

        st.markdown(f"**Summary:** {report.get('summary_text', '')}")

        # Audio quick-summary
        if audio.get("available") and audio.get("violation_detected"):
            st.error(f"🎵 Audio violations: {', '.join(audio.get('categories', []))} — words: *{', '.join(audio.get('flagged_words', [])[:6])}*")
        elif audio.get("available"):
            st.success("🎵 Audio transcript is clean — no policy keywords detected.")

        if st.button("🔄 Analyse another video", use_container_width=True):
            st.session_state.analysis_complete = False
            st.session_state.results = {}
            st.session_state.downloaded_url = ""
            st.session_state.downloaded_video_path = ""
            st.rerun()

    else:
        source = st.radio(
            "Video source",
            ["📁 Upload a file", "🌐 Social media URL (YouTube · TikTok · Instagram · X)"],
            horizontal=True
        )
        st.markdown("")

        uploads_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads")
        os.makedirs(uploads_dir, exist_ok=True)
        temp_video_path = None

        if source == "📁 Upload a file":
            uploaded = st.file_uploader("Drop your video (MP4, AVI, MOV, MKV)",
                                        type=["mp4", "avi", "mov", "mkv"],
                                        label_visibility="collapsed")
            if uploaded:
                temp_video_path = os.path.join(uploads_dir, uploaded.name)
                with open(temp_video_path, "wb") as f:
                    f.write(uploaded.read())
                sz = os.path.getsize(temp_video_path) / (1024 * 1024)
                st.success(f"📎 **{uploaded.name}** ({sz:.1f} MB) — ready")
        else:
            url_input = st.text_input("Paste URL", placeholder="https://www.youtube.com/watch?v=…")

            with st.expander("🍪 YouTube cookie fix (needed if you get a bot error)", expanded=False):
                st.caption("YouTube blocks anonymous downloads. Pick the browser you use for YouTube — yt-dlp reads its cookies. No passwords are shared.")
                cookie_browser = st.selectbox("Browser", ["None (no cookies)", "chrome", "firefox", "edge", "brave", "opera"])
                selected_browser = None if cookie_browser.startswith("None") else cookie_browser

            if url_input:
                already_dl = (
                    st.session_state.downloaded_url == url_input
                    and st.session_state.downloaded_video_path
                    and os.path.exists(st.session_state.downloaded_video_path)
                )
                if already_dl:
                    temp_video_path = st.session_state.downloaded_video_path
                    st.success(f"✅ Downloaded: **{os.path.basename(temp_video_path)}**")
                else:
                    if st.button("⬇️ Download Video", use_container_width=True):
                        with st.spinner("Fetching video…"):
                            try:
                                dl_path = download_video_from_url(url_input, uploads_dir, cookies_browser=selected_browser)
                                st.session_state.downloaded_video_path = dl_path
                                st.session_state.downloaded_url = url_input
                                st.rerun()
                            except Exception as e:
                                st.error(str(e))

                if st.session_state.downloaded_url == url_input and st.session_state.downloaded_video_path:
                    temp_video_path = st.session_state.downloaded_video_path

        if temp_video_path:
            st.markdown("")
            _, btn_col, _ = st.columns([1, 2, 1])
            with btn_col:
                if st.button("🔍 Start Analysis", type="primary", use_container_width=True):
                    cfg = {
                        "sample_rate": sample_rate,
                        "mask_faces": mask_faces,
                        "use_object": use_object,
                        "use_nsfw":   use_nsfw,
                        "use_scene":  use_scene,
                        "use_audio":  use_audio,
                        "use_motion": use_motion,
                        "use_action": use_action,
                        "use_anomaly": use_anomaly,
                    }
                    results = run_analysis(temp_video_path, cfg)
                    if results:
                        st.session_state.results = results
                        st.session_state.analysis_complete = True
                        st.rerun()


# ══════════════════════════════════════════════
# TAB 2 — RESULTS DASHBOARD
# ══════════════════════════════════════════════
with tab2:
    if not st.session_state.analysis_complete:
        st.info("📤 Analyse a video first to see results.")
    else:
        report = st.session_state.results["report"]
        frames = st.session_state.results.get("frames", [])
        audio  = st.session_state.results.get("audio", {})
        risk   = report.get("overall_risk", "SAFE")

        # ── Metrics ─────────────────────────
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("🎞️ Frames Analysed", report["total_frames"])
        m2.metric("🚩 Flagged Frames",  report["flagged_frames"])
        m3.metric("📈 Violation Rate",  f"{report['violation_rate']:.1f}%")
        with m4:
            st.markdown("**Overall Risk**")
            st.markdown(risk_badge(risk), unsafe_allow_html=True)

        # ── Module status tags ───────────────
        st.markdown("")
        tags = []
        if any(f["object_detection"]["violation_detected"] for f in frames):
            tags.append("🎯 Object Hit")
        if any(f["nsfw_detection"]["violation_detected"] for f in frames):
            tags.append("🔞 NSFW Hit")
        if any(f["scene_classification"]["is_flagged"] for f in frames):
            tags.append("🎬 Scene Hit")
        if audio.get("violation_detected"):
            tags.append("🎵 Audio Hit")
        if any(f.get("optical_flow", {}).get("is_high_motion") for f in frames):
            tags.append("🌊 Motion Hit")
        if any(f.get("action_recognition", {}).get("violation_detected") for f in frames):
            tags.append("🤺 Action Hit")
        if any(f["aggregated"].get("is_anomaly") for f in frames):
            tags.append("🧮 Stats Anomaly")
        if tags:
            st.markdown(" ".join(f"<span class='module-tag'>{t}</span>" for t in tags), unsafe_allow_html=True)

        st.divider()

        # ── Timeline chart ───────────────────
        st.markdown("### 📉 Violation Score Timeline")
        st.caption("Each point = one frame. Dashed lines = threshold boundaries.")
        if os.path.exists(report.get("timeline_chart_path", "")):
            st.image(Image.open(report["timeline_chart_path"]), use_container_width=True)

        st.divider()

        # ── Flagged segments ─────────────────
        st.markdown("### 🚨 Flagged Segments")
        segments = report.get("flagged_segments", [])

        if not segments and not audio.get("violation_detected"):
            st.success("✅ No violation segments detected.")
        else:
            if segments:
                rows = []
                for seg in segments:
                    reasons = set()
                    for idx in range(seg["start_idx"], seg["end_idx"] + 1):
                        reasons.update(frames[idx]["aggregated"]["violation_reasons"])
                    ps = seg["peak_score"]
                    seg_risk = "🚨 HIGH RISK" if ps >= 0.75 else "🔴 VIOLATION" if ps >= 0.45 else "⚠️ BORDERLINE"
                    rows.append({
                        "Start": f"{seg['start']:.1f}s",
                        "End": f"{seg['end']:.1f}s",
                        "Duration": f"{(seg['end'] - seg['start']):.1f}s",
                        "Peak Score": f"{ps:.0%}",
                        "Risk": seg_risk,
                        "Reasons": " | ".join(list(reasons)[:3]) if reasons else "—",
                    })
                st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

            if audio.get("violation_detected"):
                st.warning(
                    f"🎵 **Audio violation** — categories: {', '.join(audio.get('categories', []))} "
                    f"| flagged words: *{', '.join(audio.get('flagged_words', [])[:8])}*"
                )

        st.divider()

        # ── Top flagged frames gallery ────────
        st.markdown("### 🖼️ Most Concerning Frames")
        top6 = sorted(
            [f for f in frames if f["aggregated"]["final_score"] >= config.VIOLATION_THRESHOLD],
            key=lambda x: x["aggregated"]["final_score"], reverse=True
        )[:6]

        if not top6:
            st.success("✅ No individually flagged frames.")
        else:
            cols = st.columns(3)
            for i, f in enumerate(top6):
                with cols[i % 3]:
                    try:
                        st.image(Image.open(f["annotated_frame_path"]), use_container_width=True)
                    except Exception:
                        st.image(Image.open(f["frame_path"]), use_container_width=True)
                    score = f["aggregated"]["final_score"]
                    r_lvl = f["aggregated"]["risk_level"]
                    st.markdown(
                        f"<div class='ts-label'>⏱ {f['timestamp_str']}</div>"
                        f"{risk_badge(r_lvl)} <code>{fmt_pct(score)}</code>",
                        unsafe_allow_html=True
                    )
                    reasons = f["aggregated"]["violation_reasons"]
                    if reasons:
                        st.caption(f"↳ {reasons[0][:80]}")
                    st.markdown("")

        st.divider()

        # ── Export ───────────────────────────
        st.markdown("### 📥 Export Report")
        export_data = {
            "summary": report,
            "audio_analysis": audio,
            "frames": [
                {
                    "frame_index": f["frame_index"],
                    "timestamp": f["timestamp"],
                    "timestamp_str": f["timestamp_str"],
                    "aggregated": f["aggregated"],
                    "object_detection": {k: v for k, v in f["object_detection"].items() if k != "annotated_frame_path"},
                    "nsfw_detection": f["nsfw_detection"],
                    "scene_classification": f["scene_classification"],
                    "optical_flow": {k: v for k, v in f.get("optical_flow", {}).items() if "path" not in k},
                    "action_recognition": {k: v for k, v in f.get("action_recognition", {}).items() if "path" not in k},
                }
                for f in frames
            ]
        }
        json_str = json.dumps(export_data, indent=2)
        st.download_button(
            "⬇️ Download Full Report (JSON)",
            data=json_str,
            file_name="adshield_report.json",
            mime="application/json",
            use_container_width=True,
        )


# ══════════════════════════════════════════════
# TAB 3 — FRAME INSPECTOR
# ══════════════════════════════════════════════
with tab3:
    if not st.session_state.analysis_complete:
        st.info("📤 Analyse a video first to inspect frames.")
    else:
        frames = st.session_state.results["frames"]

        st.markdown("### 🔎 Frame-by-Frame Inspector")
        idx = st.slider("Frame", 0, len(frames) - 1, 0, format="Frame %d")
        f   = frames[idx]
        agg = f["aggregated"]
        score, risk = agg["final_score"], agg["risk_level"]

        h1, h2, h3 = st.columns([2, 2, 4])
        h1.metric("⏱ Timestamp", f["timestamp_str"])
        h2.metric("📊 Score",    fmt_pct(score))
        with h3:
            st.markdown("**Risk Level**")
            st.markdown(risk_badge(risk), unsafe_allow_html=True)
        st.markdown(score_bar(score), unsafe_allow_html=True)
        st.markdown("")

        img1, img2 = st.columns(2)
        with img1:
            st.markdown("**Original Frame**")
            try:    st.image(Image.open(f["frame_path"]), use_container_width=True)
            except: st.warning("Original frame unavailable.")
        with img2:
            st.markdown("**Annotated / Processed Frame**")
            try:    st.image(Image.open(f["annotated_frame_path"]), use_container_width=True)
            except: st.warning("Processed frame unavailable.")

        # Flow visualisation
        flow = f.get("optical_flow", {})
        if flow.get("is_high_motion") and os.path.exists(flow.get("flow_frame_path", "")):
            with st.expander("🌊 Optical Flow Visualisation (high-motion frame)"):
                st.image(Image.open(flow["flow_frame_path"]), use_container_width=True,
                         caption=f"Mean magnitude: {flow['mean_magnitude']:.2f} | Score: {fmt_pct(flow['motion_score'])}")

        st.divider()

        if agg["violation_reasons"]:
            st.markdown("**⚠️ Violation reasons:**")
            for r in agg["violation_reasons"]:
                st.markdown(f"- {r}")
        else:
            st.success("✅ No policy violations on this frame.")

        with st.expander("🔬 Full AI Model Breakdown", expanded=False):
            d1, d2, d3 = st.columns(3)

            with d1:
                st.markdown("**🎯 Object Detection**")
                obj = f["object_detection"]
                if obj["violation_detected"]:
                    st.error(f"Violation — confidence {fmt_pct(obj['confidence'])}")
                    for d in obj.get("detections", []):
                        st.write(f"- **{d['class']}** {fmt_pct(d['confidence'])}")
                else:
                    st.success("Clean")

            with d2:
                st.markdown("**🔞 NSFW**")
                nsfw = f["nsfw_detection"]
                if nsfw["violation_detected"]:
                    st.error(f"NSFW — {fmt_pct(nsfw['confidence'])}")
                    for c in nsfw.get("categories", []):
                        st.write(f"- {c}")
                else:
                    st.success("Clean")

            with d3:
                st.markdown("**🎬 Scene**")
                sc = f["scene_classification"]
                st.write(f"`{sc.get('top_class','N/A')}` — {fmt_pct(sc.get('confidence',0))}")
                if sc.get("is_flagged"): st.error(sc.get("reason","Flagged"))
                else: st.success("Safe scene")

            st.markdown("---")
            fc1, fc2 = st.columns(2)
            with fc1:
                st.markdown("**🌊 Optical Flow**")
                if flow:
                    st.write(f"Mean Magnitude: {flow.get('mean_magnitude',0):.2f}")
                    st.write(f"High Motion: {'🚨 YES' if flow.get('is_high_motion') else '✅ NO'}")
            with fc2:
                st.markdown("**🤺 Action / Pose**")
                action = f.get("action_recognition", {})
                if action and action.get("violation_detected"):
                    st.error(f"{action.get('action')} — {fmt_pct(action.get('confidence'))}")
                else:
                    st.success("Safe pose")

            st.markdown("---")
            cs = agg.get("component_scores", {})
            st.markdown("**Weighted component scores**")
            s1, s2, s3, s4, s5, s6 = st.columns(6)
            s1.metric("Object",  fmt_pct(cs.get("object_detection", 0)))
            s2.metric("NSFW",    fmt_pct(cs.get("nsfw_detection", 0)))
            s3.metric("Scene",   fmt_pct(cs.get("scene_classification", 0)))
            s4.metric("Audio",   fmt_pct(cs.get("audio", 0)))
            s5.metric("Motion",  fmt_pct(cs.get("motion", 0)))
            s6.metric("Action",  fmt_pct(cs.get("action", 0)))

            if agg.get("is_anomaly") is not None:
                st.markdown("---")
                st.markdown("**🧮 Statistical Anomaly (Z-Score)**")
                az1, az2 = st.columns(2)
                z = agg.get("z_score", 0.0)
                az1.metric("Current Z-Score", f"{z:+.2f}σ")
                if agg.get("is_anomaly"):
                    az2.error("🚨 Statistical Outline Spike Detected")
                else:
                    az2.success("Normal within video baseline")

        # ── Navigate flagged frames ──────────
        flagged = [i for i, fr in enumerate(frames) if fr["aggregated"]["final_score"] >= config.VIOLATION_THRESHOLD]
        if flagged:
            st.markdown(f"**Navigate flagged frames** ({len(flagged)} total)")
            prev_fl = [i for i in flagged if i < idx]
            next_fl = [i for i in flagged if i > idx]
            n1, _, n3 = st.columns([2, 1, 2])
            with n1:
                if prev_fl and st.button(f"← Prev flagged (frame {prev_fl[-1]})"):
                    st.rerun()
            with n3:
                if next_fl and st.button(f"Next flagged (frame {next_fl[0]}) →"):
                    st.rerun()


# ══════════════════════════════════════════════
# TAB 4 — AUDIO ANALYSIS
# ══════════════════════════════════════════════
with tab4:
    if not st.session_state.analysis_complete:
        st.info("📤 Analyse a video first to see audio results.")
    else:
        audio = st.session_state.results.get("audio", {})

        st.markdown("### 🎵 Audio Transcription & Policy Analysis")

        if not audio.get("available"):
            st.warning("⚠️ Audio analysis was disabled or Whisper is not installed. Run `pip install openai-whisper` and enable the module in the sidebar.")
        else:
            a1, a2 = st.columns([1, 2])
            with a1:
                st.metric("Violation Detected", "🚨 YES" if audio.get("violation_detected") else "✅ NO")
                st.metric("Audio Risk Score",   fmt_pct(audio.get("confidence", 0)))

            with a2:
                cats = audio.get("categories", [])
                words = audio.get("flagged_words", [])
                if cats:
                    st.error(f"**Categories flagged:** {', '.join(cats)}")
                    st.error(f"**Specific words/phrases:** {', '.join(words)}")
                else:
                    st.success("No policy-violating keywords found in the audio.")

            st.divider()
            st.markdown("### 📜 Full Transcript")
            transcript = audio.get("transcript", "").strip()

            if transcript:
                # Highlight banned words in the transcript
                highlighted = transcript
                for word in audio.get("flagged_words", []):
                    highlighted = highlighted.replace(
                        word, f"**:red[{word}]**"
                    )
                st.markdown(highlighted)
            else:
                st.info("No speech was detected in this video, or the audio track is silent.")

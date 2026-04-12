import os
import cv2
from ultralytics import YOLO

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config


class ObjectDetector:
    def __init__(self):
        self.model = YOLO(config.YOLO_MODEL)

        # Tiered class sets with their own confidence thresholds
        self.critical_classes    = set(c.lower() for c in config.YOLO_CRITICAL_CLASSES)
        self.high_risk_classes   = set(c.lower() for c in config.YOLO_HIGH_RISK_CLASSES)
        self.contextual_classes  = set(c.lower() for c in config.CONTEXTUAL_OBJECT_CLASSES)

        self.critical_conf    = config.YOLO_CRITICAL_CONFIDENCE    # 0.12
        self.high_risk_conf   = config.YOLO_HIGH_RISK_CONFIDENCE   # 0.20
        self.contextual_conf  = config.YOLO_CONTEXTUAL_CONFIDENCE  # 0.30

        # Feed all classes into YOLO-World so it knows what vocabulary to search for
        all_classes = list(
            self.critical_classes | self.high_risk_classes | self.contextual_classes
        )
        try:
            self.model.set_classes(all_classes)
        except AttributeError:
            pass  # Fallback for standard YOLOv8 models

    def analyze(self, frame_path: str, annotated_dir: str) -> dict:
        """
        Tiered YOLO-World object detection:
        - CRITICAL  (conf ≥ 0.12): firearms, blades, syringes → hard violation + high score
        - HIGH_RISK (conf ≥ 0.20): cigarettes, drugs → hard violation + medium score
        - CONTEXTUAL(conf ≥ 0.30): bottles, bats → soft penalty only, no hard violation
        """
        result_dict = {
            "violation_detected": False,
            "confidence": 0.0,
            "severity": "none",           # 'critical' | 'high_risk' | 'contextual' | 'none'
            "detections": [],             # hard violations (critical + high_risk)
            "contextual_hits": [],        # soft hits
            "annotated_frame_path": frame_path,
        }

        os.makedirs(annotated_dir, exist_ok=True)

        try:
            # Run with the lowest possible threshold — we filter per-tier ourselves
            results = self.model(frame_path, verbose=False, conf=self.critical_conf)
            frame = cv2.imread(frame_path)
            if frame is None:
                return result_dict

            max_conf    = 0.0
            top_severity = "none"   # tracks worst severity seen this frame

            for r in results:
                for box in r.boxes:
                    cls_id     = int(box.cls[0].item())
                    conf       = float(box.conf[0].item())
                    class_name = self.model.names[cls_id]
                    cls_lower  = class_name.lower()
                    x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())

                    # ── TIER 1: CRITICAL ──────────────────────────────────────
                    if cls_lower in self.critical_classes and conf >= self.critical_conf:
                        result_dict["violation_detected"] = True
                        max_conf = max(max_conf, conf)
                        top_severity = "critical"

                        result_dict["detections"].append({
                            "class": class_name,
                            "confidence": round(conf, 4),
                            "severity": "critical",
                            "bbox": [x1, y1, x2 - x1, y2 - y1],
                        })

                        # Thick red box with bright label
                        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 220), 3)
                        label = f"CRITICAL: {class_name} {conf:.0%}"
                        lw, lh = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)[0]
                        cv2.rectangle(frame, (x1, max(y1-lh-10, 0)), (x1+lw+6, max(y1, lh+10)), (0, 0, 220), -1)
                        cv2.putText(frame, label, (x1+3, max(y1-5, lh+3)),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

                    # ── TIER 2: HIGH RISK ─────────────────────────────────────
                    elif cls_lower in self.high_risk_classes and conf >= self.high_risk_conf:
                        result_dict["violation_detected"] = True
                        max_conf = max(max_conf, conf * 0.85)   # slight penalty factor vs critical
                        if top_severity != "critical":
                            top_severity = "high_risk"

                        result_dict["detections"].append({
                            "class": class_name,
                            "confidence": round(conf, 4),
                            "severity": "high_risk",
                            "bbox": [x1, y1, x2 - x1, y2 - y1],
                        })

                        # Orange box
                        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 120, 255), 2)
                        label = f"HIGH RISK: {class_name} {conf:.0%}"
                        lw, lh = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.55, 2)[0]
                        cv2.rectangle(frame, (x1, max(y1-lh-8, 0)), (x1+lw+4, max(y1, lh+8)), (0, 120, 255), -1)
                        cv2.putText(frame, label, (x1+2, max(y1-4, lh+2)),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 2)

                    # ── TIER 3: CONTEXTUAL ────────────────────────────────────
                    elif cls_lower in self.contextual_classes and conf >= self.contextual_conf:
                        result_dict["contextual_hits"].append({
                            "class": class_name,
                            "confidence": round(conf, 4),
                        })

                        # Yellow thin dashed-style box
                        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 200, 255), 1)
                        cv2.putText(frame, f"CTX: {class_name} {conf:.0%}", (x1, max(y1-5, 10)),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.40, (0, 200, 255), 1)

            # Assign severity and final confidence
            result_dict["severity"]   = top_severity
            result_dict["confidence"] = round(max_conf, 4)

            # Save annotated frame
            base_name      = os.path.basename(frame_path)
            prefix         = "crit_" if top_severity == "critical" else \
                             "risk_" if top_severity == "high_risk" else \
                             "ctx_"  if result_dict["contextual_hits"] else "safe_"
            annotated_path = os.path.join(annotated_dir, f"{prefix}{base_name}")
            cv2.imwrite(annotated_path, frame)
            result_dict["annotated_frame_path"] = annotated_path

        except Exception as e:
            print(f"ObjectDetector error on {frame_path}: {e}")

        return result_dict

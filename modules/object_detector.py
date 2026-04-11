import os
import cv2
from ultralytics import YOLO

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config


class ObjectDetector:
    def __init__(self):
        self.model = YOLO(config.YOLO_MODEL)   # auto-downloads on first run
        self.banned_classes = set(c.lower() for c in config.BANNED_OBJECT_CLASSES)
        self.contextual_classes = set(c.lower() for c in config.CONTEXTUAL_OBJECT_CLASSES)
        self.min_conf = config.YOLO_MIN_CONFIDENCE

    def analyze(self, frame_path: str, annotated_dir: str) -> dict:
        """
        Runs YOLOv8 object detection. Filters for banned and contextual classes.
        Returns highest violation confidence and list of all detections.
        """
        result_dict = {
            "violation_detected": False,
            "confidence": 0.0,
            "detections": [],
            "annotated_frame_path": frame_path,
        }

        os.makedirs(annotated_dir, exist_ok=True)

        try:
            results = self.model(frame_path, verbose=False, conf=self.min_conf)
            frame = cv2.imread(frame_path)
            if frame is None:
                return result_dict

            max_conf = 0.0
            has_violation = False

            for r in results:
                for box in r.boxes:
                    cls_id     = int(box.cls[0].item())
                    conf       = float(box.conf[0].item())
                    class_name = self.model.names[cls_id]
                    cls_lower  = class_name.lower()

                    if conf < self.min_conf:
                        continue

                    x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                    is_banned      = cls_lower in self.banned_classes
                    is_contextual  = cls_lower in self.contextual_classes

                    if is_banned:
                        has_violation = True
                        max_conf = max(max_conf, conf)
                        result_dict["detections"].append({
                            "class": class_name,
                            "confidence": round(conf, 4),
                            "severity": "banned",
                            "bbox": [x1, y1, x2 - x1, y2 - y1],
                        })
                        # Red thick box + filled label background
                        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 220), 3)
                        label = f"BANNED: {class_name} {conf:.0%}"
                        lw, lh = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.55, 2)[0]
                        cv2.rectangle(frame, (x1, max(y1-lh-8, 0)), (x1+lw+4, max(y1, lh+8)), (0, 0, 220), -1)
                        cv2.putText(frame, label, (x1+2, max(y1-4, lh+2)),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 2)

                    elif is_contextual:
                        # Orange thin box — contextual only
                        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 140, 255), 1)
                        cv2.putText(frame, f"{class_name} {conf:.0%}", (x1, max(y1-6, 10)),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.42, (0, 140, 255), 1)

                    else:
                        # Green thin box — safe object
                        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 200, 60), 1)
                        cv2.putText(frame, f"{class_name} {conf:.0%}", (x1, max(y1-6, 10)),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.38, (0, 200, 60), 1)

            if has_violation:
                base_name      = os.path.basename(frame_path)
                annotated_path = os.path.join(annotated_dir, f"obj_{base_name}")
                cv2.imwrite(annotated_path, frame)
                result_dict["violation_detected"] = True
                result_dict["confidence"]         = round(max_conf, 4)
                result_dict["annotated_frame_path"] = annotated_path
            else:
                # Still save annotated frame showing all green boxes (useful for demo)
                base_name      = os.path.basename(frame_path)
                annotated_path = os.path.join(annotated_dir, f"safe_{base_name}")
                cv2.imwrite(annotated_path, frame)
                result_dict["annotated_frame_path"] = annotated_path

        except Exception as e:
            print(f"ObjectDetector error on {frame_path}: {e}")

        return result_dict

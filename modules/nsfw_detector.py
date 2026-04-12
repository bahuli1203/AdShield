import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config


class NSFWDetector:
    def __init__(self):
        self.available = False
        self.violation_labels = set(getattr(config, "NSFW_VIOLATION_LABELS", [
            "FEMALE_GENITALIA_EXPOSED", "MALE_GENITALIA_EXPOSED", 
            "FEMALE_BREAST_EXPOSED", "ANUS_EXPOSED", "BUTTOCKS_EXPOSED"
        ]))
        self.threshold = config.NSFW_CONFIDENCE_THRESHOLD   # 0.40

        try:
            from nudenet import NudeDetector
            self.detector  = NudeDetector()
            self.available = True
        except ImportError:
            print("Warning: NudeNet not installed. NSFW detection will be skipped.")
        except Exception as e:
            print(f"Warning: NudeNet init error: {e}")

    def analyze(self, frame_path: str) -> dict:
        """
        Runs NudeNet NSFW detection.
        - Uses explicit violation list (NSFW_VIOLATION_LABELS) rather than guessing against safe lists.
        - Fixes bug where 'FEMALE_BREAST_COVERED' would repeatedly trigger false violations.
        """
        result_dict = {
            "violation_detected": False,
            "confidence": 0.0,
            "categories": [],
            "raw_detections": [],    # all detections for debugging
        }

        if not self.available:
            return result_dict

        try:
            detections = self.detector.detect(frame_path)
            max_conf   = 0.0
            categories = set()

            for det in detections:
                score = float(det["score"])
                label = det["class"]

                # Always store raw for debugging visibility in JSON export
                result_dict["raw_detections"].append({
                    "label": label, "score": round(score, 4)
                })

                # Check if it is explicitly an explicit violation
                if label in self.violation_labels and score >= self.threshold:
                    categories.add(label)
                    max_conf = max(max_conf, score)

            if categories:
                result_dict["violation_detected"] = True
                result_dict["confidence"]         = round(max_conf, 4)
                result_dict["categories"]         = sorted(categories)

        except Exception as e:
            print(f"NSFWDetector error on {frame_path}: {e}")

        return result_dict

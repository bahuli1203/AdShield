import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config


class NSFWDetector:
    def __init__(self):
        self.available = False
        self.safe_labels = set(config.NSFW_SAFE_LABELS)
        self.threshold   = config.NSFW_CONFIDENCE_THRESHOLD   # 0.40

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
        - Uses config.NSFW_CONFIDENCE_THRESHOLD (0.40) instead of hardcoded 0.5
        - Filters out safe/benign NudeNet labels defined in config.NSFW_SAFE_LABELS
        - Returns all non-safe detections above threshold
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

                # Skip benign labels
                if label in self.safe_labels:
                    continue

                # Flag if above threshold
                if score >= self.threshold:
                    categories.add(label)
                    max_conf = max(max_conf, score)

            if categories:
                result_dict["violation_detected"] = True
                result_dict["confidence"]         = round(max_conf, 4)
                result_dict["categories"]         = sorted(categories)

        except Exception as e:
            print(f"NSFWDetector error on {frame_path}: {e}")

        return result_dict

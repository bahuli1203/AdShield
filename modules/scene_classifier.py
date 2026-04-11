import numpy as np


class SceneClassifier:
    def __init__(self):
        self.available = False
        try:
            import tensorflow as tf
            from tensorflow.keras.applications.mobilenet_v2 import (
                MobileNetV2, preprocess_input, decode_predictions
            )
            from tensorflow.keras.preprocessing import image

            self.model             = MobileNetV2(weights='imagenet')
            self.preprocess_input  = preprocess_input
            self.decode_predictions = decode_predictions
            self.image             = image
            self.available         = True

            # Import flag keywords from config so we have one source of truth
            import sys, os
            sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            import config
            self.flag_keywords = config.SCENE_FLAG_KEYWORDS

        except ImportError:
            print("Warning: TensorFlow not installed. Scene classification will be skipped.")
        except Exception as e:
            print(f"Warning: SceneClassifier init error: {e}")

    def analyze(self, frame_path: str) -> dict:
        """
        Runs MobileNetV2 scene classification.
        Uses top-10 predictions (more coverage) and a large keyword list.
        Returns flag status, confidence, and the matching reason.
        """
        result_dict = {
            "top_class": "Unknown",
            "confidence": 0.0,
            "all_predictions": [],
            "is_flagged": False,
            "reason": "",
        }

        if not self.available:
            return result_dict

        try:
            img = self.image.load_img(frame_path, target_size=(224, 224))
            x   = self.image.img_to_array(img)
            x   = np.expand_dims(x, axis=0)
            x   = self.preprocess_input(x)

            preds   = self.model.predict(x, verbose=False)
            decoded = self.decode_predictions(preds, top=10)[0]   # top-10 for coverage

            top_pred = decoded[0]
            result_dict["top_class"]  = top_pred[1]
            result_dict["confidence"] = round(float(top_pred[2]), 4)
            result_dict["all_predictions"] = [
                {"class": cn, "confidence": round(float(sc), 4)}
                for _, cn, sc in decoded
            ]

            is_flagged  = False
            flag_hits   = []
            flag_conf   = 0.0

            for _, class_name, score in decoded:
                class_desc = class_name.lower().replace("_", " ")
                for keyword in self.flag_keywords:
                    if keyword in class_desc:
                        is_flagged = True
                        flag_hits.append(f"{keyword} → '{class_name}' ({score:.0%})")
                        flag_conf = max(flag_conf, float(score))

            if is_flagged:
                result_dict["is_flagged"]  = True
                result_dict["confidence"]  = round(flag_conf, 4)   # use flagged-class confidence
                result_dict["reason"]      = "Scene contains: " + " | ".join(flag_hits[:4])

        except Exception as e:
            print(f"SceneClassifier error on {frame_path}: {e}")

        return result_dict

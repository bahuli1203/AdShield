import os
import sys

# Import config for flag keywords
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

class SceneClassifier:
    def __init__(self):
        self.available = False
        try:
            from transformers import CLIPProcessor, CLIPModel
            from PIL import Image
            import torch
            
            self.Image = Image
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
            print(f"Loading CLIP Scene Classifier on {self.device}...")
            
            # Load CLIP model
            self.model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32").to(self.device)
            self.processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
            
            # Setup semantic prompts
            self.prompts = [
                "a photo of people fighting or physical combat",
                "a photo of someone holding a weapon or knife",
                "a photo of an explosion, fire, or warfare",
                "a photo of adult content or nudity",
                "a photo of illegal drugs or drug use",
                "a photo of alcohol or drinking",
                "a safe commercial advertisement",
                "a normal everyday scene",
                "a portrait or conversation"
            ]
            
            self.unsafe_prompts = [
                "a photo of people fighting or physical combat",
                "a photo of someone holding a weapon or knife",
                "a photo of an explosion, fire, or warfare",
                "a photo of adult content or nudity",
                "a photo of illegal drugs or drug use",
                "a photo of alcohol or drinking"
            ]
            
            self.available = True
        except ImportError:
            print("Warning: transformers or torch not installed. Scene classification skipped.")
        except Exception as e:
            print(f"Warning: SceneClassifier init error: {e}")

    def analyze(self, frame_path: str) -> dict:
        """
        Uses OpenAI's CLIP zero-shot model to infer semantic context,
        eliminating the brittle string-matching of ImageNet classes.
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
            image = self.Image.open(frame_path)
            
            # Process inputs
            inputs = self.processor(text=self.prompts, images=image, return_tensors="pt", padding=True)
            
            import torch
            inputs = {k: v.to(self.device) if isinstance(v, torch.Tensor) else v for k, v in inputs.items()}
            
            outputs = self.model(**inputs)
            logits_per_image = outputs.logits_per_image
            probs = logits_per_image.softmax(dim=1).cpu().detach().numpy()[0]
            
            # Map probabilities to prompts
            pred_scores = [(self.prompts[i], probs[i]) for i in range(len(self.prompts))]
            pred_scores.sort(key=lambda x: x[1], reverse=True)
            
            top_pred = pred_scores[0]
            result_dict["top_class"] = top_pred[0]
            result_dict["confidence"] = round(float(top_pred[1]), 4)
            result_dict["all_predictions"] = [
                {"class": p[0], "confidence": round(float(p[1]), 4)}
                for p in pred_scores
            ]
            
            is_flagged = False
            flag_conf = 0.0
            reasons = []
            
            for p, score in pred_scores:
                if p in self.unsafe_prompts and score >= 0.20: # Lowered threshold because softmax is spread across more classes
                    is_flagged = True
                    flag_conf = max(flag_conf, score)
                    reasons.append(f"{p} ({score:.0%})")
                    
            if is_flagged:
                result_dict["is_flagged"] = True
                result_dict["confidence"] = round(float(flag_conf), 4)
                result_dict["reason"] = "Scene context suggests: " + " | ".join(reasons)

        except Exception as e:
            print(f"SceneClassifier error on {frame_path}: {e}")

        return result_dict

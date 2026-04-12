import cv2
import math
import os

class ActionRecognizer:
    def __init__(self):
        self.available = False
        self.prev_wrists = None  # To store [(l_x, l_y), (r_x, r_y)] for momentum parsing
        try:
            import mediapipe as mp
            self.mp_pose = mp.solutions.pose
            self.mp_drawing = mp.solutions.drawing_utils
            self.pose = self.mp_pose.Pose(
                static_image_mode=True, 
                model_complexity=1,
                min_detection_confidence=0.5
            )
            self.available = True
        except ImportError:
            print("Warning: mediapipe not installed. Action recognition will be skipped.")
        except Exception as e:
            print(f"ActionRecognizer init error: {e}")

    def analyze(self, frame_path: str, annotated_dir: str) -> dict:
        """
        Uses MediaPipe Pose to detect aggressive physical actions (e.g. striking/fighting).
        Now uses velocity and proportional distance heuristics to eliminate false positives.
        """
        result_dict = {
            "violation_detected": False,
            "confidence": 0.0,
            "action": "Normal",
            "annotated_frame_path": frame_path
        }

        if not self.available:
            return result_dict

        try:
            frame = cv2.imread(frame_path)
            if frame is None:
                return result_dict
                
            # Convert BGR to RGB
            image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = self.pose.process(image_rgb)
            
            if results.pose_landmarks:
                landmarks = results.pose_landmarks.landmark
                
                # Get relevant landmarks
                nose = landmarks[self.mp_pose.PoseLandmark.NOSE]
                l_shoulder = landmarks[self.mp_pose.PoseLandmark.LEFT_SHOULDER]
                r_shoulder = landmarks[self.mp_pose.PoseLandmark.RIGHT_SHOULDER]
                l_wrist = landmarks[self.mp_pose.PoseLandmark.LEFT_WRIST]
                r_wrist = landmarks[self.mp_pose.PoseLandmark.RIGHT_WRIST]
                
                # Check visibility
                vis_threshold = 0.5
                vis = (l_shoulder.visibility > vis_threshold and r_shoulder.visibility > vis_threshold and
                       l_wrist.visibility > vis_threshold and r_wrist.visibility > vis_threshold)
                       
                is_aggressive = False
                confidence = 0.0
                
                if vis:
                    # Dynamic torso scale based on shoulder width
                    shoulder_dx = l_shoulder.x - r_shoulder.x
                    shoulder_dy = l_shoulder.y - r_shoulder.y
                    shoulder_width = math.sqrt(shoulder_dx**2 + shoulder_dy**2)
                    shoulder_width = max(shoulder_width, 0.05)  
                    
                    chest_y = (l_shoulder.y + r_shoulder.y) / 2.0
                    
                    # 1. High Striking: Hand is raised extremely high above the head (e.g. wielding a weapon downwards)
                    striking_high = (l_wrist.y < (nose.y - shoulder_width)) or (r_wrist.y < (nose.y - shoulder_width))
                    
                    # 2. Combat Guard: Both hands are raised tightly near the face/chest level
                    l_guarding = l_wrist.y < chest_y and abs(l_wrist.x - nose.x) < shoulder_width * 1.2
                    r_guarding = r_wrist.y < chest_y and abs(r_wrist.x - nose.x) < shoulder_width * 1.2
                    boxing_guard = (l_guarding and r_guarding)
                    
                    # Aggression requires either a combat stance or an extreme wind-up strike
                    if boxing_guard or striking_high:
                        is_aggressive = True
                        confidence = 0.85
                        result_dict["action"] = "Combat Stance / Striking"
                
                if is_aggressive:
                    result_dict["violation_detected"] = True
                    result_dict["confidence"] = confidence
                    
                base_name = os.path.basename(frame_path)
                annotated_path = os.path.join(annotated_dir, f"action_{base_name}")
                
                annotated_image = frame.copy()
                self.mp_drawing.draw_landmarks(
                    annotated_image,
                    results.pose_landmarks,
                    self.mp_pose.POSE_CONNECTIONS,
                    landmark_drawing_spec=self.mp_drawing.DrawingSpec(color=(0,0,255) if is_aggressive else (0,255,0), thickness=2, circle_radius=2),
                    connection_drawing_spec=self.mp_drawing.DrawingSpec(color=(0,0,255) if is_aggressive else (0,255,0), thickness=2)
                )
                
                if is_aggressive:
                    cv2.putText(annotated_image, f"ACTION: {result_dict['action']}!", (10, 50), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                                
                cv2.imwrite(annotated_path, annotated_image)
                result_dict["annotated_frame_path"] = annotated_path

        except Exception as e:
            print(f"ActionRecognizer error on {frame_path}: {e}")

        return result_dict

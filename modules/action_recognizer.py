import cv2
import math

class ActionRecognizer:
    def __init__(self):
        self.available = False
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
        Uses MediaPipe Pose to detect aggressive physical actions (e.g. fighting stance).
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
                    # Heuristic 1: Raised fists (Fighting Stance)
                    # Wrists are above or at shoulder level, and close to each other / body center
                    wrists_above_shoulders = (l_wrist.y < l_shoulder.y) or (r_wrist.y < r_shoulder.y)
                    
                    # Calculate distance from wrists to nose
                    dx_l = l_wrist.x - nose.x
                    dy_l = l_wrist.y - nose.y
                    dist_l = math.sqrt(dx_l**2 + dy_l**2)
                    
                    dx_r = r_wrist.x - nose.x
                    dy_r = r_wrist.y - nose.y
                    dist_r = math.sqrt(dx_r**2 + dy_r**2)
                    
                    # If hands are raised and brought close to face -> fighting guard
                    if wrists_above_shoulders and (dist_l < 0.25 or dist_r < 0.25):
                        is_aggressive = True
                        confidence = 0.85
                        result_dict["action"] = "Aggressive Stance / Fighting Position"
                
                if is_aggressive:
                    result_dict["violation_detected"] = True
                    result_dict["confidence"] = confidence
                    
                # Always draw landmarks for visual effect
                import os
                base_name = os.path.basename(frame_path)
                annotated_path = os.path.join(annotated_dir, f"action_{base_name}")
                
                # Draw skeleton
                annotated_image = frame.copy()
                self.mp_drawing.draw_landmarks(
                    annotated_image,
                    results.pose_landmarks,
                    self.mp_pose.POSE_CONNECTIONS,
                    landmark_drawing_spec=self.mp_drawing.DrawingSpec(color=(0,0,255) if is_aggressive else (0,255,0), thickness=2, circle_radius=2),
                    connection_drawing_spec=self.mp_drawing.DrawingSpec(color=(0,0,255) if is_aggressive else (0,255,0), thickness=2)
                )
                
                if is_aggressive:
                    cv2.putText(annotated_image, f"ACTION: {result_dict['action']}", (10, 50), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                                
                cv2.imwrite(annotated_path, annotated_image)
                result_dict["annotated_frame_path"] = annotated_path

        except Exception as e:
            print(f"ActionRecognizer error on {frame_path}: {e}")

        return result_dict

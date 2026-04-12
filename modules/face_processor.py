import cv2
import os

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

class FaceProcessor:
    def __init__(self):
        self.available = False
        try:
            import mediapipe as mp
            self.mp_face_detection = mp.solutions.face_detection
            # model_selection=1 handles faces farther away as well as close-up
            self.face_detection = self.mp_face_detection.FaceDetection(
                model_selection=1, min_detection_confidence=0.5
            )
            self.available = True
        except ImportError:
            print("Warning: mediapipe not installed. Face processing will be skipped.")
        except Exception as e:
            print(f"Failed to load mediapipe face detection: {e}")

    def process(self, frame_path: str, mask=True) -> dict:
        """
        Detects faces in the frame using MediaPipe and applies a dynamically scaled blur mask.
        Returns the number of detected faces and the path to the newly processed frame.
        """
        result_dict = {
            "faces_detected": 0,
            "processed_frame_path": frame_path 
        }

        if not self.available:
            return result_dict

        try:
            frame = cv2.imread(frame_path)
            if frame is None:
                return result_dict

            # MediaPipe expects RGB format images
            image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = self.face_detection.process(image_rgb)
            
            faces = []
            img_h, img_w, _ = frame.shape
            
            if results.detections:
                for detection in results.detections:
                    bboxC = detection.location_data.relative_bounding_box
                    x_min = int(bboxC.xmin * img_w)
                    y_min = int(bboxC.ymin * img_h)
                    width = int(bboxC.width * img_w)
                    height = int(bboxC.height * img_h)
                    
                    # Prevent coordinates from bleeding out of frame boundaries
                    x = max(0, x_min)
                    y = max(0, y_min)
                    w = min(img_w - x, width)
                    h = min(img_h - y, height)
                    
                    if w > 0 and h > 0:
                        faces.append((x, y, w, h))

            result_dict["faces_detected"] = len(faces)

            if len(faces) > 0 and mask:
                for (x, y, w, h) in faces:
                    roi = frame[y:y+h, x:x+w]
                    
                    # Completely dynamic blur scalar. The blur kernel will always be roughly 60% of the face width.
                    # This prevents the program from crashing on tiny faces and prevents huge faces from remaining readable.
                    blur_val = max(3, int(w * 0.6))
                    
                    # OpenCV blur algorithms mandate odd numbers
                    if blur_val % 2 == 0:
                        blur_val += 1
                        
                    blurred_roi = cv2.GaussianBlur(roi, (blur_val, blur_val), 0)
                    
                    # Lock the successfully blurred subset back down into our main frame structure
                    frame[y:y+h, x:x+w] = blurred_roi

                base_name = os.path.basename(frame_path)
                processed_dir = os.path.join(os.path.dirname(frame_path), "processed")
                if not os.path.exists(processed_dir):
                    os.makedirs(processed_dir)
                    
                processed_path = os.path.join(processed_dir, f"masked_{base_name}")
                cv2.imwrite(processed_path, frame)
                result_dict["processed_frame_path"] = processed_path

        except Exception as e:
            print(f"Error in FaceProcessor: {e}")

        return result_dict

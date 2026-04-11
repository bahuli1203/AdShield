import cv2
import os
import urllib.request
import sys

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

class FaceProcessor:
    def __init__(self):
        assets_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")
        if not os.path.exists(assets_dir):
            os.makedirs(assets_dir)
            
        self.cascade_path = os.path.join(assets_dir, "haarcascade_frontalface_default.xml")
        
        # Download Haar cascade if not exists
        if not os.path.exists(self.cascade_path):
            print("Downloading face cascade classifier...")
            url = "https://raw.githubusercontent.com/opencv/opencv/master/data/haarcascades/haarcascade_frontalface_default.xml"
            try:
                urllib.request.urlretrieve(url, self.cascade_path)
            except Exception as e:
                print(f"Failed to download Haar cascade: {e}")
                
        # Initialize classifier
        try:
            self.face_cascade = cv2.CascadeClassifier(self.cascade_path)
        except Exception as e:
            print(f"Failed to load face cascade: {e}")
            self.face_cascade = None

    def process(self, frame_path: str, mask=True) -> dict:
        """
        Detects faces in the frame. If mask=True, applies a blur to the faces.
        Returns the number of detected faces and the path to the annotated frame.
        """
        result_dict = {
            "faces_detected": 0,
            "processed_frame_path": frame_path 
        }

        if self.face_cascade is None or self.face_cascade.empty():
            return result_dict

        try:
            frame = cv2.imread(frame_path)
            if frame is None:
                return result_dict

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = self.face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))

            result_dict["faces_detected"] = len(faces)

            if len(faces) > 0 and mask:
                for (x, y, w, h) in faces:
                    # Extract the region of interest (ROI)
                    roi = frame[y:y+h, x:x+w]
                    
                    # Apply Gaussian blur
                    blur_val = config.FACE_MASK_BLUR
                    # Ensure blur values are odd
                    if blur_val % 2 == 0:
                        blur_val += 1
                        
                    blurred_roi = cv2.GaussianBlur(roi, (blur_val, blur_val), 0)
                    
                    # Place the blurred ROI back into the original image
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

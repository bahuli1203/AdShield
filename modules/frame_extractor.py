import cv2
import os

class FrameExtractor:
    def __init__(self, video_path, output_dir, sample_rate=1, output_width=640):
        self.video_path = video_path
        self.output_dir = output_dir
        self.sample_rate = sample_rate
        self.output_width = output_width
        
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

    def extract(self) -> list[dict]:
        """
        Extracts frames from video and returns metadata list.
        """
        cap = cv2.VideoCapture(self.video_path)
        if not cap.isOpened():
            raise Exception(f"Failed to open video file: {self.video_path}")

        fps = cap.get(cv2.CAP_PROP_FPS)
        # Ensure fps is valid
        if fps <= 0:
            fps = 30.0 
            
        frame_interval = max(1, int(fps * self.sample_rate))
        
        frames_metadata = []
        frame_idx = 0
        extracted_count = 0

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            if frame_idx % frame_interval == 0:
                timestamp = frame_idx / fps
                
                # Format timestamp as HH:MM:SS
                hours = int(timestamp // 3600)
                minutes = int((timestamp % 3600) // 60)
                seconds = int(timestamp % 60)
                timestamp_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"

                # Resize frame
                h, w = frame.shape[:2]
                new_width = self.output_width
                new_height = int((new_width / w) * h)
                resized_frame = cv2.resize(frame, (new_width, new_height))

                frame_filename = f"frame_{extracted_count:04d}.jpg"
                frame_path = os.path.join(self.output_dir, frame_filename)
                
                cv2.imwrite(frame_path, resized_frame)

                frames_metadata.append({
                    "frame_index": extracted_count,
                    "timestamp": timestamp,
                    "timestamp_str": timestamp_str,
                    "frame_path": frame_path
                })
                
                extracted_count += 1
                if extracted_count % 10 == 0:
                    print(f"Extracted {extracted_count} frames...")

            frame_idx += 1

        cap.release()
        
        # Return sorted list by timestamp (it's naturally sorted but let's be explicit)
        frames_metadata.sort(key=lambda x: x["timestamp"])
        return frames_metadata

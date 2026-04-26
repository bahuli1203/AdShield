import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config


class AudioAnalyzer:
    def __init__(self):
        self.available = False
        print("Audio Analysis is disabled.")

    def process_video(self, video_path: str, temp_dir: str) -> list:
        """Audio analysis is disabled. Returns empty list."""
        return []

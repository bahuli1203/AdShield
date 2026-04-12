import os
import re
import sys
import moviepy.editor as mp
import whisper

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config


class AudioAnalyzer:
    def __init__(self):
        self.available = False
        self.profanity_list = getattr(config, "PROFANITY_LIST", [
            "fuck", "shit", "bitch", "cunt", "slut", "whore", 
            "asshole", "nigger", "faggot", "retard"
        ])
        
        try:
            print("Loading Whisper base model for Audio Analysis...")
            self.model = whisper.load_model("base")
            self.available = True
        except Exception as e:
            print(f"Warning: Whisper init error, audio analysis will be skipped: {e}")

    def process_video(self, video_path: str, temp_dir: str) -> list:
        """
        Extracts audio from video, runs Whisper transcription, and checks for profanity.
        Returns a list of violating segments:
        [
          {"start": 1.2, "end": 4.5, "matched_words": ["fuck", "bitch"], "text": "...", "confidence": 0.85}
        ]
        """
        if not self.available:
            return []

        # Extract audio track to temporary file
        os.makedirs(temp_dir, exist_ok=True)
        audio_path = os.path.join(temp_dir, "temp_audio.wav")
        video_clip = None

        try:
            video_clip = mp.VideoFileClip(video_path)
            if video_clip.audio is None:
                return [] # No audio track in video
            
            # Suppress moviepy output logs to avoid terminal clutter
            video_clip.audio.write_audiofile(audio_path, logger=None)
            
            # Run Whisper Transcription
            result = self.model.transcribe(audio_path, word_timestamps=False)
            segments = result.get("segments", [])
            
            violations = []
            
            for seg in segments:
                start_time = seg.get("start", 0.0)
                end_time = seg.get("end", 0.0)
                text = seg.get("text", "").lower()
                
                matched_words = []
                for word in self.profanity_list:
                    # Using regex word boundary to find exact matches, preventing 'shitty' from matching 'hit'
                    pattern = r'\b' + re.escape(word.lower()) + r'\b'
                    if re.search(pattern, text):
                        matched_words.append(word)
                    elif word.lower() in text and len(word) > 5: # Fallback for aggressive concatenated words
                        matched_words.append(word)
                        
                if matched_words:
                    # Deduplicate matched words
                    matched_words = list(set(matched_words))
                    violations.append({
                        "start": round(start_time, 2),
                        "end": round(end_time, 2),
                        "matched_words": matched_words,
                        "text": seg.get("text", "").strip(),
                        "confidence": 0.95  # Strict text match implies very high confidence of occurrence
                    })

            return violations
            
        except Exception as e:
            print(f"AudioAnalyzer error on {video_path}: {e}")
            return []
            
        finally:
            if video_clip is not None:
                try: video_clip.close()
                except: pass
            # Clean up temp file
            if os.path.exists(audio_path):
                try:
                    os.remove(audio_path)
                except:
                    pass

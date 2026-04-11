"""
Audio Analyzer using OpenAI Whisper (offline, no API key required).
Transcribes video audio and flags banned keywords for ad policy violations.
"""
import os
import re
import subprocess
import tempfile


# ── Keyword lists ──────────────────────────────────────────────────────────
PROFANITY_WORDS = [
    "fuck", "shit", "bitch", "asshole", "bastard", "damn", "crap",
    "dick", "cock", "pussy", "cunt", "motherfucker", "faggot", "retard",
    "nigger", "nigga", "whore", "slut"
]

VIOLENCE_WORDS = [
    "kill", "murder", "assault", "rape", "shoot", "stab", "bomb",
    "attack", "destroy", "massacre", "genocide", "torture", "execute"
]

DRUG_WORDS = [
    "cocaine", "heroin", "meth", "methamphetamine", "weed", "marijuana",
    "cannabis", "ecstasy", "lsd", "crack", "fentanyl", "opioid",
    "overdose", "drug dealer", "get high", "smoke weed"
]

ALCOHOL_PROMO_WORDS = [
    "get drunk", "shots", "beer", "vodka", "whiskey", "tequila", "alcohol"
]

HATE_WORDS = [
    "nazi", "terrorist", "extremist", "jihad", "white supremacy",
    "ethnic cleansing", "hate speech"
]

ALL_BANNED = set(PROFANITY_WORDS + VIOLENCE_WORDS + DRUG_WORDS + ALCOHOL_PROMO_WORDS + HATE_WORDS)


class AudioAnalyzer:
    def __init__(self):
        self.available = False
        self.model = None
        try:
            import whisper
            # Load tiny model — fast, runs offline, no API key
            self.model = whisper.load_model("tiny")
            self.available = True
            print("✅ Whisper audio model loaded (tiny)")
        except ImportError:
            print("⚠️  openai-whisper not installed. Audio analysis will be skipped.")
        except Exception as e:
            print(f"⚠️  Could not load Whisper model: {e}")

    def analyze(self, video_path: str) -> dict:
        """
        Extracts audio from the video, transcribes it with Whisper,
        and flags banned keywords.

        Returns:
            {
                "available": bool,
                "transcript": str,
                "flagged_words": [str],
                "categories": [str],       # e.g. ["profanity", "violence"]
                "violation_detected": bool,
                "confidence": float        # 0.0 – 1.0 based on number of hits
            }
        """
        if not self.available:
            return {
                "available": False,
                "transcript": "",
                "flagged_words": [],
                "categories": [],
                "violation_detected": False,
                "confidence": 0.0,
            }

        try:
            # Whisper can handle mp4 directly (uses ffmpeg internally)
            result = self.model.transcribe(video_path, fp16=False)
            transcript = result.get("text", "").strip()
            words_lower = transcript.lower()

            flagged = []
            categories = set()

            for word in PROFANITY_WORDS:
                if word in words_lower:
                    flagged.append(word)
                    categories.add("profanity")

            for word in VIOLENCE_WORDS:
                if word in words_lower:
                    flagged.append(word)
                    categories.add("violence")

            for word in DRUG_WORDS:
                if word in words_lower:
                    flagged.append(word)
                    categories.add("drugs")

            for word in ALCOHOL_PROMO_WORDS:
                if word in words_lower:
                    flagged.append(word)
                    categories.add("alcohol promotion")

            for word in HATE_WORDS:
                if word in words_lower:
                    flagged.append(word)
                    categories.add("hate speech")

            violation = len(flagged) > 0
            # Each flagged word contributes ~0.15 confidence, capped at 1.0
            confidence = min(len(flagged) * 0.15, 1.0)

            return {
                "available": True,
                "transcript": transcript,
                "flagged_words": list(set(flagged)),
                "categories": list(categories),
                "violation_detected": violation,
                "confidence": round(confidence, 4),
            }

        except Exception as e:
            print(f"AudioAnalyzer error: {e}")
            return {
                "available": True,
                "transcript": "",
                "flagged_words": [],
                "categories": [],
                "violation_detected": False,
                "confidence": 0.0,
            }

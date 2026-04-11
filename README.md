<div align="center">
  <img src="https://img.icons8.com/color/124/protection-mask.png" alt="AdShield Logo" width="100"/>

  # 🛡️ AdShield: Google Ads Policy Violation Detector
  
  **Track:** AI/ML + OpenCV  
  *A comprehensive multimodal AI pipeline for detecting ad policy violations in video content at scale.*

  [![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
  [![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=flat&logo=Streamlit&logoColor=white)](https://streamlit.io)
  [![YOLOv8](https://img.shields.io/badge/YOLOv8-Ultralytics-green.svg)](https://github.com/ultralytics/ultralytics)
  [![OpenAI Whisper](https://img.shields.io/badge/Whisper-OpenAI-black.svg)](https://github.com/openai/whisper)
</div>

---

## 🎯 The Problem
With the rapid growth of video platforms, enforcing content guidelines is critical. Videos may violate policies through the presence of prohibited objects, unsafe visual content, manipulated scenes, or restricted language.

## 🚀 Our Solution: AdShield
AdShield is a fully automated, frame-by-frame multimodal validation pipeline. Instead of relying on a single model, AdShield fuses **7 independent data signals** to calculate a precise risk score and flag violations.

### 🧠 Core AI Modules
1. **🎯 Object Detection (YOLOv8s):** Detects banned objects (weapons, alcohol, syringes) using highly optimized bounding boxes.
2. **🔞 NSFW Detection (NudeNet):** Identifies explicit content while intelligently filtering out safe skin exposure.
3. **🎬 Scene Classification (MobileNetV2):** Analyzes the environment context to flag risky scenes like explosions, fire, or prisons.
4. **🎵 Audio NLP Analysis (OpenAI Whisper):** Fully offline speech-to-text to catch profanity, hate speech, and drug references.
5. **🌊 Optical Flow (OpenCV):** Dense optical flow (Farneback) analysis to catch sudden chaotic/violent motion anomalies in the absence of obvious objects.
6. **🤺 Action Recognition (MediaPipe):** Uses skeletal landmark tracking to identify aggressive physical stances and gestures.
7. **🧮 Statistical Anomaly Detection (Z-Score):** Analyzes the full timestamped risk pipeline to catch mathematical outliers.

### ✨ Additional Features
- **🌐 Built-in Social Downloader:** Drop a link from YouTube, TikTok, Instagram, or X and download it seamlessly via `yt-dlp`.
- **😷 Privacy Masking:** Compliant face tracking and Gaussian blur.
- **📊 Real-time Dashboard:** Streamlit UI with timelines, frame-by-frame scrubbers, and JSON report payload exports.

---

## 🛠️ Quick Start

### 1. Requirements
- Python 3.9+
- Windows/Linux/MacOS

### 2. Installation
Clone the repository and install the dependencies:
```bash
python -m venv venv
# Windows
.\venv\Scripts\activate
# Mac/Linux
source venv/bin/activate

pip install -r requirements.txt
```

*Note: The YOLOv8, NudeNet, and Whisper `tiny` models will automatically download on their first run. No API keys are required; everything runs 100% locally and offline.*

### 3. Run the Dashboard
```bash
streamlit run app.py
```

The Web UI will be automatically served at `http://localhost:8501`.

---

## 📁 Project Structure

```text
policy_detector/
├── app.py                     # Main Streamlit Dashboard & UI
├── config.py                  # Thresholds, class filters, & architecture rules
├── requirements.txt           # Deployment dependencies
├── modules/
│   ├── object_detector.py     # YOLOv8 implementation
│   ├── nsfw_detector.py       # NudeNet implementation
│   ├── scene_classifier.py    # MobileNetV2 architecture
│   ├── audio_analyzer.py      # Whisper NLP transcript
│   ├── optical_flow.py        # OpenCV motion detection
│   ├── action_recognizer.py   # MediaPipe skeletal tracking
│   ├── anomaly_detector.py    # Z-Score mathematics
│   ├── face_processor.py      # Haar Cascades masking
│   ├── score_aggregator.py    # Weighted fusion engine
│   ├── video_downloader.py    # yt-dlp social media pull
│   └── report_generator.py    # JSON payload builder
└── frames/ & results/         # Auto-generated processing dirs
```

## 🧮 How Scoring Works
AdShield employs a **Weighted Corroboration Engine**.
- Each AI module operates independently on a single frame.
- Scores are combined recursively based on weights defined in `config.py`.
- **Multi-Signal Boost:** If two or more independent detectors flag a frame (e.g. YOLO sees a knife + MediaPipe sees an aggressive stance), the system automatically boosts the confidence score mathematically.
- The video is segmented, and peak scores determine if a segment is `SAFE`, `BORDERLINE`, `VIOLATION`, or `HIGH RISK`.

---
*Built for the 24-Hour AI/ML OpenCV Hackathon.*

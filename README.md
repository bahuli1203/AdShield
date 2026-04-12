<div align="center">
  <img src="https://img.icons8.com/color/124/protection-mask.png" alt="AdShield Logo" width="100"/>

  # 🛡️ AdShield: Google Ads Policy Violation Detector
  
  **Track:** AI/ML + OpenCV  
  *A comprehensive full-stack, multimodal AI pipeline for detecting ad policy violations in video content at scale.*

  [![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
  [![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=flat&logo=fastapi)](https://fastapi.tiangolo.com/)
  [![React](https://img.shields.io/badge/React-20232A?style=flat&logo=react&logoColor=61DAFB)](https://react.dev)
  [![Vite](https://img.shields.io/badge/Vite-B73BFE?style=flat&logo=vite&logoColor=FFD62E)](https://vitejs.dev)
  [![YOLO-World](https://img.shields.io/badge/YOLO--World-Ultralytics-green.svg)](https://github.com/ultralytics/ultralytics)
  [![OpenAI CLIP](https://img.shields.io/badge/CLIP-OpenAI-black.svg)](https://github.com/openai/CLIP)
</div>

---

## 🎯 The Problem
With the rapid growth of video platforms, enforcing content guidelines is critical. Videos may violate policies through the presence of prohibited objects, unsafe visual content, manipulated scenes, or restricted language.

## 🚀 Our Solution: AdShield
AdShield is a fully automated, frame-by-frame multimodal validation pipeline. Instead of relying on a single model, AdShield fuses **7 independent data signals** to calculate a precise risk score and flag violations mathematically.

### 🧠 Core AI Modules
1. **🎯 Object Detection (YOLO-World):** Detects banned objects (weapons, alcohol, syringes) using highly optimized zero-shot bounding boxes.
2. **🔞 NSFW Detection (NudeNet):** Identifies explicit content while intelligently filtering out safe skin exposure with strict thresholds.
3. **🎬 Scene Classification (OpenAI CLIP):** Zero-shot contextual understanding to flag risky environments like combat zones or fires.
4. **🎵 Audio NLP Analysis (OpenAI Whisper):** Fully offline speech-to-text NLP analysis to accurately catch profanity and hate speech exactly when it is spoken.
5. **🌊 Optical Flow (OpenCV):** Dense optical flow (Farneback) analysis bounds violent motion anomalies and chaotic camera shakes.
6. **🤺 Action Recognition (MediaPipe):** Uses skeletal landmark geometry to mathematically identify aggressive physical stances and combat guards.
7. **🧮 Statistical Anomaly Detection (Z-Score):** Analyzes the full timestamped timeline mathematically to catch sudden severity outliers.

### ✨ Additional Features
- **🌐 Built-in Social Downloader:** Drop a link from YouTube, TikTok, Instagram, or X and download the MP4 seamlessly via `yt-dlp`.
- **😷 Privacy Masking:** Compliant OpenCV Haar Cascade face tracking and Gaussian blurring.
- **📊 React Dashboard:** A highly interactive UI powered by Vite and Framer Motion, featuring synchronized video timelines, transparent AI logs, and frame-by-frame evidence scrubbing.

---

## 🛠️ Quick Start

### 1. Requirements
- Python 3.9+
- Node.js & npm (for the React Frontend)
- Windows/Linux/MacOS

### 2. Backend Installation (FastAPI)
The backend requires substantial memory to download and load the PyTorch/Ultralytics machine learning models upon the first run.
```bash
# Clone the repository
git clone https://github.com/bahuli1203/AdShield.git
cd AdShield

# Create a virtual environment and install dependencies
python -m venv venv

# Windows
.\venv\Scripts\activate
# Mac/Linux
source venv/bin/activate

# Install requirements
pip install -r requirements.txt
```

### 3. Frontend Installation (React/Vite)
```bash
# Open a second terminal window
cd frontend
npm install
```

### 4. Run the Full Stack App
You must run both the backend and frontend simultaneously.

**Terminal 1 (Backend):**
```bash
python api.py
```
*The FastAPI REST server starts at `http://localhost:8000`*

**Terminal 2 (Frontend):**
```bash
npm run dev
```
*The AdShield React UI will be automatically served at `http://localhost:5173`*

---

## 📁 Project Structure

```text
AdShield/
├── api.py                     # Main FastAPI application & execution loop
├── config.py                  # Math thresholds, object classes & global weights
├── requirements.txt           # Python backend dependencies
├── frontend/                  # React + Vite UI Application
│   ├── src/components/        # Dashboard, Timeline, and Video Player code
│   └── package.json           # Node dependencies
├── modules/
│   ├── object_detector.py     # YOLO-World integration
│   ├── nsfw_detector.py       # NudeNet implementation
│   ├── scene_classifier.py    # OpenAI CLIP architecture
│   ├── audio_analyzer.py      # OpenAI Whisper audio profanity extraction
│   ├── optical_flow.py        # OpenCV motion detection
│   ├── action_recognizer.py   # MediaPipe skeletal geometry analysis
│   ├── anomaly_detector.py    # Mathematical spikes & Z-Scores
│   ├── face_processor.py      # GDPR compliance & masking
│   ├── score_aggregator.py    # Weighted fusion engine & Overrides
│   └── report_generator.py    # Final payload builder
└── frames/ & results/         # Auto-generated image processing directories
```

## 🧮 How Scoring Works
AdShield employs a custom **Weighted Corroboration Engine**:
- Each AI module operates entirely independently on the 1-second video frame.
- Scores are combined recursively based on the global decimal weights governed exclusively by `config.py`.
- **Explicit Breach Guarantees:** Catching an unsafe object (e.g., a knife) or a Whisper profanity slur ("fuck") forces an automatic override math multiplier, permanently throwing the segment into a **High Risk** flag.
- **Multi-Signal Boost:** If two or more independent detectors flag a frame (e.g., YOLO sees a bat + MediaPipe geometry sees a strike), the system automatically mathematically boosts the risk confidence score to confirm a violation.

---
*Built for the 24-Hour AI/ML OpenCV Hackathon.*

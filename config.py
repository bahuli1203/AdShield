# ─────────────────────────────────────────────
# Configuration File
# ─────────────────────────────────────────────

FRAME_SAMPLE_RATE = 1          # Extract 1 frame per second
VIOLATION_THRESHOLD = 0.45     # Score above this = violation flagged
HIGH_RISK_THRESHOLD = 0.75     # Score above this = high risk (red)
MAX_VIDEO_SIZE_MB = 500
FACE_MASK_BLUR = 35            # Blur kernel size (must be odd)
OUTPUT_FRAME_WIDTH = 640       # Resize frames for processing

# ─── YOLO ────────────────────────────────────
# yolov8n.pt = fastest but least accurate (nano)
# yolov8s.pt = better accuracy, still fast     ← recommended
# yolov8m.pt = best accuracy, slower           (use if GPU available)
YOLO_MODEL = "yolov8s.pt"
YOLO_MIN_CONFIDENCE = 0.35     # Ignore detections below this confidence

# ─── Banned COCO-80 classes ──────────────────
# NOTE: COCO-80 does NOT include "gun", "pistol", "rifle", "cigarette", "syringe".
# These are NOT in the COCO dataset — do not add them or they will never match.
# For firearms/drugs, a custom-trained model would be required (future upgrade).
# Classes below ARE present in COCO-80 and WILL trigger correctly:
BANNED_OBJECT_CLASSES = [
    # Sharp weapons
    "knife",
    "scissors",
    # Alcohol containers (bottle includes any bottle; wine glass, beer glass not in COCO)
    "bottle",
    "wine glass",
    "cup",          # used to hold alcohol — contextual flag
    # Sports/recreation items that can double as weapons
    "baseball bat",
    "sports ball",  # context-dependent — lower weight
    "tennis racket",
]

# Classes to flag but at lower severity (contextual — not outright banned)
CONTEXTUAL_OBJECT_CLASSES = [
    "cell phone",  # distracted driving context
    "laptop",
    "remote",
]

# ─── Scene classification ─────────────────────
# Keywords matched against ImageNet class names (1000 classes).
# Broad matching: if ANY top-5 prediction contains one of these substrings, it flags.
SCENE_FLAG_KEYWORDS = [
    # Weapons / violence
    "rifle", "revolver", "assault", "gun", "pistol", "cannon", "missile",
    "knife", "dagger", "sword", "saber", "cleaver", "hatchet", "axe",
    "grenade", "bomb", "explosion", "warplane", "tank",
    # Blood / gore
    "blood", "wound", "injury",
    # Drugs / smoking
    "cigarette", "smoking", "pipe", "hookah", "syringe", "hypodermic",
    # Alcohol / bars
    "alcohol", "beer", "wine", "liquor", "brewery", "distillery",
    "cocktail", "bartender",
    # Fire / hazard
    "fire", "flame", "smoke", "volcano", "burning",
    # Adult content  
    "bikini", "brassiere", "lingerie", "miniskirt",
    # Gang / crime
    "prison", "jail", "handcuff", "holster",
]

# ─── NSFW ──────────────────────────────────────
# Lower threshold = more sensitive (more true positives, more false positives)
NSFW_CONFIDENCE_THRESHOLD = 0.40   # Was 0.5 — catch more borderline NSFW

# NudeNet labels that are NOT considered violations (too generic / benign)
NSFW_SAFE_LABELS = [
    "FACE_FEMALE", "FACE_MALE",
    "ARMPITS_EXPOSED", "ARMPITS_COVERED",
    "FEET_EXPOSED", "FEET_COVERED",
    "BELLY_COVERED",
    "BELLY_EXPOSED",      # Removed from safe — belly exposed can be contextual, but too noisy
]

# ─── Score weights ────────────────────────────
# Each component score is multiplied by its weight before summing.
# Max possible sum: if obj+nsfw both fire at 1.0 → 0.70+0.70 = 1.40 → capped at 1.0
SCORE_WEIGHTS = {
    "object_detection":    0.75,
    "nsfw_detection":      0.75,
    "scene_classification": 0.35,
    "audio":               0.55,
    "motion":              0.20,
    "action_recognition":  0.60,
}

# Multi-signal boost: when ≥2 different detectors fire, add this bonus
MULTI_SIGNAL_BOOST = 0.10

# ─── Motion ──────────────────────────────────
MOTION_THRESHOLD = 6.0     # Lowered from 8.0 → catches more sudden/violent motion

# ─── Whisper ──────────────────────────────────
WHISPER_MODEL = "tiny"     # tiny | base | small  (no API key needed, fully offline)

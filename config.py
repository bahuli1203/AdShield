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
# Upgraded to YOLO-World (Zero-Shot) - allows custom text classes to be accurately mapped
YOLO_MODEL = "yolov8s-worldv2.pt"
YOLO_MIN_CONFIDENCE = 0.15     # Custom text classes sometimes have naturally lower confidence limits

# ─── YOLO-World Severity Tiers ───────────────
# Each tier has its own confidence threshold.
# CRITICAL: Very low threshold → catch it even if YOLO is slightly unsure.
# HIGH_RISK: Medium threshold → needs reasonable confidence.
# CONTEXTUAL: Standard threshold → soft penalty only, not a hard violation.

YOLO_CRITICAL_CLASSES = [
    # Firearms — most severe, catch with high sensitivity
    "handgun",
    "pistol",
    "shotgun",
    "assault rifle",
    "machine gun",
    "firearm",
    # Bladed weapons
    "knife",
    "machete",
    "sword",
    "blade",
    # Drugs paraphernalia
    "syringe",
    "hypodermic needle",
    # Violence symbols
    "grenade",
    "bomb",
    "explosive device",
]
YOLO_CRITICAL_CONFIDENCE = 0.12   # Low threshold — these are so dangerous, catch even uncertain detections

YOLO_HIGH_RISK_CLASSES = [
    # Smoking / tobacco
    "cigarette",
    "cigar",
    "vape",
    "smoking pipe",
    # Drug substances
    "cannabis",
    "marijuana",
    "cocaine",
    # Dangerous objects
    "brass knuckles",
    "taser",
    "whip",
]
YOLO_HIGH_RISK_CONFIDENCE = 0.20   # Medium threshold

# Backwards compatibility — aggregator and old code still reference these
BANNED_OBJECT_CLASSES = YOLO_CRITICAL_CLASSES + YOLO_HIGH_RISK_CLASSES

# Classes to flag but at lower severity (soft contextual penalty only)
CONTEXTUAL_OBJECT_CLASSES = [
    "bottle",
    "wine glass",
    "beer can",
    "alcohol bottle",
    "baseball bat",
    "axe",
]
YOLO_CONTEXTUAL_CONFIDENCE = 0.30  # Higher threshold — only flag if clearly visible

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
NSFW_CONFIDENCE_THRESHOLD = 0.30   # Dropped to 0.30 to allow high-sensitivity slider settings to work

# NudeNet explicit labels that constitute a definitive violation
NSFW_VIOLATION_LABELS = [
    "FEMALE_GENITALIA_EXPOSED",
    "MALE_GENITALIA_EXPOSED",
    "FEMALE_BREAST_EXPOSED",
    "ANUS_EXPOSED",
    "BUTTOCKS_EXPOSED"
]

# ─── Score weights ────────────────────────────
# Each component score is multiplied by its weight before summing.
# Max possible sum: if obj+nsfw both fire at 1.0 → 0.70+0.70 = 1.40 → capped at 1.0
SCORE_WEIGHTS = {
    "object_detection":    0.75,
    "nsfw_detection":      0.75,
    "scene_classification": 0.35,
    "motion":              0.20,
    "action_recognition":  0.60,
}

# Multi-signal boost: when ≥2 different detectors fire, add this bonus
MULTI_SIGNAL_BOOST = 0.10

# ─── Motion ──────────────────────────────────
MOTION_THRESHOLD = 6.0     # Lowered from 8.0 → catches more sudden/violent motion



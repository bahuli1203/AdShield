import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config


class ScoreAggregator:
    def __init__(self):
        self.weights     = config.SCORE_WEIGHTS
        self.multi_boost = config.MULTI_SIGNAL_BOOST

    def aggregate(self, object_result, nsfw_result, scene_result,
                  motion_result=None, action_result=None, audio_result=None) -> dict:
        """
        Combines all model results into one final weighted violation score.

        Key improvements over v1:
        - Contextual object hits contribute a softer score (0.35x penalty) not a full ban.
        - NSFW and Object scores are individually clamped at 0.95 to prevent a single
          detector dominating the final score (avoids 100% false confidence from one model).
        - Bonus corroboration boost is now proportional and capped.
        - Scene classifier has a confidence gate: low-confidence CLIP predictions are
          dampened before being added to the final sum.
        """
        w = self.weights

        # ── Extract raw scores ──────────────────────────────────────────────
        obj_score    = object_result.get("confidence",   0.0) if object_result.get("violation_detected") else 0.0
        nsfw_score   = nsfw_result.get("confidence",     0.0) if nsfw_result.get("violation_detected")   else 0.0
        scene_score  = scene_result.get("confidence",    0.0) if scene_result.get("is_flagged")           else 0.0
        motion_score = motion_result.get("motion_score", 0.0) if (motion_result and motion_result.get("is_high_motion")) else 0.0
        action_score = action_result.get("confidence",   0.0) if (action_result and action_result.get("violation_detected")) else 0.0
        audio_score  = audio_result.get("confidence",    0.0) if (audio_result and audio_result.get("violation_detected")) else 0.0

        # Severity-aware object boost: critical detections (firearms, blades) get a 1.25x multiplier
        obj_severity = object_result.get("severity", "none")
        if obj_severity == "critical":
            obj_score = min(obj_score * 1.25, 0.95)
        elif obj_severity == "high_risk":
            obj_score = min(obj_score * 1.10, 0.95)

        # ── Contextual object penalty (e.g. bottle, cup visible but not outright banned) ──
        ctx_obj_score = 0.0
        if object_result.get("contextual_hits"):
            ctx_count = len(object_result.get("contextual_hits", []))
            ctx_obj_score = min(0.25, ctx_count * 0.08)   # soft penalty, max 0.25

        # ── Per-detector clamping ───────────────────────────────────────────
        obj_score    = min(obj_score,    1.0)
        nsfw_score   = min(nsfw_score,   1.0)
        audio_score  = min(audio_score,  1.0)
        scene_score  = min(scene_score,  0.90)

        # ── CLIP scene confidence gate — dampen weak/uncertain predictions ───
        # If the scene prediction confidence < 0.50, halve its contribution
        if 0 < scene_score < 0.50:
            scene_score *= 0.5

        weighted_sum = (
            obj_score       * w.get("object_detection",     0.75) +
            ctx_obj_score   * 0.35 +                                   # soft contextual hit
            nsfw_score      * w.get("nsfw_detection",       0.75) +
            scene_score     * w.get("scene_classification", 0.35) +
            motion_score    * w.get("motion",               0.20) +
            action_score    * w.get("action_recognition",   0.60) +
            audio_score     * w.get("audio_analysis",       0.80)
        )

        # ── Explicit Policy Breach Guarantees ───────────────────────────────
        # If an explicit adult content hit or a critical weapon is detected, 
        # guarantee it automatically crosses the 'HIGH RISK' or 'VIOLATION' boundary.
        if nsfw_score > 0.50:
            weighted_sum = max(weighted_sum, 0.76) # Force HIGH RISK
        elif obj_severity == "critical" and obj_score > 0.50:
            weighted_sum = max(weighted_sum, 0.76) # Force HIGH RISK
        elif audio_score > 0.50:
            weighted_sum = max(weighted_sum, 0.76) # Force HIGH RISK for Profanity

        # ── Multi-signal corroboration boost ────────────────────────────────
        # Independent strong detector signals (>0.15) corroborate each other
        signals_fired = sum([
            1 if obj_score    > 0.15 else 0,
            1 if nsfw_score   > 0.15 else 0,
            1 if scene_score  > 0.15 else 0,
            1 if motion_score > 0.15 else 0,
            1 if action_score > 0.15 else 0,
            1 if audio_score  > 0.15 else 0,
        ])

        if signals_fired >= 2:
            # Proportional boost — each extra signal adds but with diminishing returns
            boost = self.multi_boost * (signals_fired - 1)
            boost = min(boost, 0.25)   # hard cap so 5 detectors don't explode the score
            weighted_sum += boost

        final_score = round(min(1.0, weighted_sum), 4)

        # ── Risk level ──────────────────────────────────────────────────────
        if final_score < 0.30:
            risk_level = "SAFE"
        elif final_score < 0.45:
            risk_level = "BORDERLINE"
        elif final_score < 0.75:
            risk_level = "VIOLATION"
        else:
            risk_level = "HIGH RISK"

        # ── Human-readable violation reasons ────────────────────────────────
        reasons = []

        if object_result.get("violation_detected"):
            items = list({d["class"] for d in object_result.get("detections", [])})
            reasons.append(f"Banned objects detected: {', '.join(items)} (conf {obj_score:.0%})")

        if object_result.get("contextual_hits"):
            ctx_items = list({d["class"] for d in object_result.get("contextual_hits", [])})
            reasons.append(f"Contextual objects of concern: {', '.join(ctx_items)}")

        if nsfw_result.get("violation_detected"):
            cats = nsfw_result.get("categories", [])
            reasons.append(f"Explicit NSFW content: {', '.join(cats)} (conf {nsfw_score:.0%})")

        if scene_result.get("is_flagged"):
            reasons.append(scene_result.get("reason", "Risky scene detected"))

        if motion_result and motion_result.get("is_high_motion"):
            mag = motion_result.get("mean_magnitude", 0.0)
            reasons.append(f"Violent/chaotic motion spike (magnitude {mag:.1f})")

        if action_result and action_result.get("violation_detected"):
            reasons.append(f"Aggressive action detected: {action_result.get('action')} (conf {action_score:.0%})")

        if audio_result and audio_result.get("violation_detected"):
            words = ", ".join(audio_result.get("matched_words", []))
            reasons.append(f"Profanity/Hate speech detected: '{words}' (conf {audio_score:.0%})")

        if signals_fired >= 2:
            reasons.append(f"⚡ {signals_fired} independent detectors corroborated — confidence boosted")

        return {
            "final_score":       final_score,
            "risk_level":        risk_level,
            "violation_reasons": reasons,
            "signals_fired":     signals_fired,
            "component_scores": {
                "object_detection":    round(obj_score,     4),
                "contextual_objects":  round(ctx_obj_score, 4),
                "nsfw_detection":      round(nsfw_score,    4),
                "scene_classification":round(scene_score,   4),
                "motion":              round(motion_score,  4),
                "action":              round(action_score,  4),
                "audio":               round(audio_score,   4),
            },
        }

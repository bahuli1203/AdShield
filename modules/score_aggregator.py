import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config


class ScoreAggregator:
    def __init__(self):
        self.weights     = config.SCORE_WEIGHTS
        self.multi_boost = config.MULTI_SIGNAL_BOOST  # bonus when 2+ detectors fire

    def aggregate(self, object_result, nsfw_result, scene_result,
                  audio_result=None, motion_result=None, action_result=None) -> dict:
        """
        Combines all model results into a single weighted violation score.
        Includes a multi-signal boost when ≥2 independent detectors fire.

        Returns:
        {
            "final_score": float,           # 0.0–1.0
            "risk_level": str,
            "violation_reasons": [str],
            "component_scores": { ... },
            "signals_fired": int            # how many detectors triggered
        }
        """
        w = self.weights

        obj_score    = object_result.get("confidence",  0.0) if object_result.get("violation_detected") else 0.0
        nsfw_score   = nsfw_result.get("confidence",    0.0) if nsfw_result.get("violation_detected")   else 0.0
        scene_score  = scene_result.get("confidence",   0.0) if scene_result.get("is_flagged")          else 0.0
        audio_score  = audio_result.get("confidence",   0.0) if (audio_result and audio_result.get("violation_detected"))  else 0.0
        motion_score = motion_result.get("motion_score",0.0) if (motion_result and motion_result.get("is_high_motion"))    else 0.0
        action_score = action_result.get("confidence",  0.0) if (action_result and action_result.get("violation_detected")) else 0.0

        weighted_sum = (
            obj_score    * w.get("object_detection",     0.75) +
            nsfw_score   * w.get("nsfw_detection",       0.75) +
            scene_score  * w.get("scene_classification", 0.35) +
            audio_score  * w.get("audio",                0.55) +
            motion_score * w.get("motion",               0.20) +
            action_score * w.get("action_recognition",   0.60)
        )

        # Count how many independent detectors fired
        signals_fired = sum([
            1 if obj_score   > 0 else 0,
            1 if nsfw_score  > 0 else 0,
            1 if scene_score > 0 else 0,
            1 if audio_score > 0 else 0,
            1 if motion_score> 0 else 0,
            1 if action_score> 0 else 0,
        ])

        # Multi-signal corroboration boost — if 2+ detectors agree, add confidence
        if signals_fired >= 2:
            weighted_sum += self.multi_boost * (signals_fired - 1)

        final_score = round(min(1.0, weighted_sum), 4)

        # Risk level
        if final_score < 0.30:
            risk_level = "SAFE"
        elif final_score < 0.45:
            risk_level = "BORDERLINE"
        elif final_score < 0.75:
            risk_level = "VIOLATION"
        else:
            risk_level = "HIGH RISK"

        # Human-readable reasons
        reasons = []
        if object_result.get("violation_detected"):
            items = list({d["class"] for d in object_result.get("detections", [])})
            reasons.append(f"Banned objects: {', '.join(items)} (conf {obj_score:.0%})")

        if nsfw_result.get("violation_detected"):
            cats = nsfw_result.get("categories", [])
            reasons.append(f"NSFW content: {', '.join(cats)} (conf {nsfw_score:.0%})")

        if scene_result.get("is_flagged"):
            reasons.append(scene_result.get("reason", "Risky scene"))

        if audio_result and audio_result.get("violation_detected"):
            cats  = audio_result.get("categories", [])
            words = audio_result.get("flagged_words", [])
            reasons.append(f"Audio: {', '.join(cats)} — '{', '.join(words[:4])}'")

        if motion_result and motion_result.get("is_high_motion"):
            mag = motion_result.get("mean_magnitude", 0.0)
            reasons.append(f"High-motion anomaly (magnitude {mag:.1f})")

        if action_result and action_result.get("violation_detected"):
            reasons.append(f"Action: {action_result.get('action')} (conf {action_score:.0%})")

        if signals_fired >= 2:
            reasons.append(f"⚡ {signals_fired} detectors corroborated — confidence boosted")

        return {
            "final_score":       final_score,
            "risk_level":        risk_level,
            "violation_reasons": reasons,
            "signals_fired":     signals_fired,
            "component_scores": {
                "object_detection":    round(obj_score,    4),
                "nsfw_detection":      round(nsfw_score,   4),
                "scene_classification":round(scene_score,  4),
                "audio":               round(audio_score,  4),
                "motion":              round(motion_score, 4),
                "action":              round(action_score, 4),
            },
        }

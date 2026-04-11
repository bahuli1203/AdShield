"""
Optical Flow Motion Analyzer
Uses OpenCV Farneback dense optical flow to detect rapid/violent motion between frames.
High motion magnitude indicates potentially aggressive or policy-violating content.
"""
import cv2
import numpy as np
import os


class OpticalFlowAnalyzer:
    def __init__(self, motion_threshold: float = 8.0):
        """
        Args:
            motion_threshold: Mean magnitude above this is considered high-motion.
                              Typical values: calm scene ~1-3, action/sports ~5-10,
                              violent/chaotic ~12+
        """
        self.motion_threshold = motion_threshold
        self.prev_gray = None  # previous frame in grayscale

    def reset(self):
        """Call before starting a new video."""
        self.prev_gray = None

    def analyze(self, frame_path: str) -> dict:
        """
        Computes optical flow between the previous frame and the current frame.

        Returns:
            {
                "motion_score": float,     # 0.0 to 1.0 normalised
                "mean_magnitude": float,   # raw flow magnitude
                "is_high_motion": bool,
                "flow_frame_path": str     # path to visualised flow image (or original)
            }
        """
        result = {
            "motion_score": 0.0,
            "mean_magnitude": 0.0,
            "is_high_motion": False,
            "flow_frame_path": frame_path,
        }

        try:
            frame = cv2.imread(frame_path)
            if frame is None:
                return result

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            if self.prev_gray is None:
                # No previous frame yet — store and return zero motion
                self.prev_gray = gray
                return result

            # Farneback dense optical flow
            flow = cv2.calcOpticalFlowFarneback(
                self.prev_gray, gray,
                None,
                pyr_scale=0.5, levels=3, winsize=15,
                iterations=3, poly_n=5, poly_sigma=1.2,
                flags=0
            )

            # Compute magnitude of flow vectors
            mag, ang = cv2.cartToPolar(flow[..., 0], flow[..., 1])
            mean_mag = float(np.mean(mag))

            # Normalise: cap at 30.0 (very fast motion = 1.0)
            motion_score = min(mean_mag / 30.0, 1.0)
            is_high_motion = mean_mag >= self.motion_threshold

            # Save flow visualisation (HSV colour wheel)
            hsv = np.zeros_like(frame)
            hsv[..., 1] = 255
            hsv[..., 0] = ang * 180 / np.pi / 2
            hsv[..., 2] = cv2.normalize(mag, None, 0, 255, cv2.NORM_MINMAX)
            flow_vis = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)

            flow_dir = os.path.join(os.path.dirname(frame_path), "flow")
            os.makedirs(flow_dir, exist_ok=True)
            flow_path = os.path.join(flow_dir, "flow_" + os.path.basename(frame_path))
            cv2.imwrite(flow_path, flow_vis)

            self.prev_gray = gray

            result.update({
                "motion_score": round(motion_score, 4),
                "mean_magnitude": round(mean_mag, 4),
                "is_high_motion": is_high_motion,
                "flow_frame_path": flow_path,
            })

        except Exception as e:
            print(f"OpticalFlowAnalyzer error: {e}")

        return result

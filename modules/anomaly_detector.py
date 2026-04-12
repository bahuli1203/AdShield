import numpy as np

class AnomalyDetector:
    def __init__(self, z_score_threshold=2.0):
        """
        Statistical Anomaly Detection.
        Analyzes the full timeline of scores and identifies statistical outliers
        (frames that deviate significantly from this specific video's norm).
        """
        self.z_threshold = z_score_threshold
        
    def analyze_timeline(self, frames_data: list) -> dict:
        """
        Input: list of frame dicts containing their aggregated final_score.
        Returns: Dict containing anomaly flags added to frames, and global stats.
        """
        if not frames_data or len(frames_data) < 3:
            return {"anomalies_detected": 0, "global_mean": 0.0, "global_std": 0.0}
            
        scores = [f["aggregated"]["final_score"] for f in frames_data]
        
        mean_score = np.mean(scores)
        std_score = np.std(scores)
        
        # Prevent mathematical explosion (Z-score infinity) on completely flat/calm videos.
        # We enforce a baseline noise expectation of 0.08 variance.
        if std_score < 0.08:
            std_score = 0.08
            
        anomalies_count = 0
        
        for i, f in enumerate(frames_data):
            score = scores[i]
            # Z-score: how many standard deviations away from the mean
            z_score = (score - mean_score) / std_score
            
            is_anomaly = float(z_score) >= self.z_threshold
            
            # Anomaly is only registered if the score itself is somewhat noticeable (>0.2)
            # otherwise a video of pure 0s with one 0.05 will trigger a massive Z-score false positive
            if is_anomaly and score > 0.20:
                f["aggregated"]["is_anomaly"] = True
                f["aggregated"]["z_score"] = round(float(z_score), 2)
                if "Statistical Anomaly (Spike)" not in f["aggregated"]["violation_reasons"]:
                    f["aggregated"]["violation_reasons"].append(f"Statistical Anomaly: Z-Score +{z_score:.1f}σ")
                anomalies_count += 1
            else:
                f["aggregated"]["is_anomaly"] = False
                f["aggregated"]["z_score"] = round(float(z_score), 2)

        return {
            "anomalies_detected": anomalies_count,
            "global_mean": round(float(mean_score), 4),
            "global_std": round(float(std_score), 4)
        }

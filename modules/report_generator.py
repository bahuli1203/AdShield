import matplotlib.pyplot as plt
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

class ReportGenerator:
    def __init__(self, results_dir="results"):
        self.results_dir = results_dir
        if not os.path.exists(self.results_dir):
            os.makedirs(self.results_dir)

    def generate(self, analysis_results: list[dict], video_path: str) -> dict:
        """
        Generates timeline charts and logical summaries.
        """
        total_frames = len(analysis_results)
        flagged_frames = 0
        overall_max_score = 0.0
        
        timestamps = []
        scores = []
        
        for res in analysis_results:
            score = res.get("aggregated", {}).get("final_score", 0.0)
            if score >= config.VIOLATION_THRESHOLD:
                flagged_frames += 1
            if score > overall_max_score:
                overall_max_score = score
                
            timestamps.append(res.get("timestamp", 0.0))
            scores.append(score)

        violation_rate = (flagged_frames / total_frames * 100) if total_frames > 0 else 0.0

        if overall_max_score < 0.3:
            overall_risk = "SAFE"
        elif overall_max_score < config.VIOLATION_THRESHOLD:
            overall_risk = "BORDERLINE"
        elif overall_max_score < config.HIGH_RISK_THRESHOLD:
            overall_risk = "VIOLATION"
        else:
            overall_risk = "HIGH RISK"

        # Detect contiguous violation segments
        flagged_segments = []
        current_segment = None
        
        for i, res in enumerate(analysis_results):
            score = res.get("aggregated", {}).get("final_score", 0.0)
            timestamp = res.get("timestamp", 0.0)
            
            if score >= config.VIOLATION_THRESHOLD:
                if current_segment is None:
                    current_segment = {
                        "start": timestamp,
                        "end": timestamp,
                        "peak_score": score,
                        "start_idx": i,
                        "end_idx": i
                    }
                else:
                    current_segment["end"] = timestamp
                    current_segment["end_idx"] = i
                    current_segment["peak_score"] = max(current_segment["peak_score"], score)
            else:
                if current_segment is not None:
                    flagged_segments.append(current_segment)
                    current_segment = None
                    
        if current_segment is not None:
            flagged_segments.append(current_segment)

        # Generate timeline chart
        timeline_chart_path = os.path.join(self.results_dir, "timeline_chart.png")
        
        plt.figure(figsize=(12, 4))
        plt.plot(timestamps, scores, color='blue', linewidth=2)
        plt.fill_between(timestamps, scores, color='blue', alpha=0.1)
        
        # Color bands
        plt.axhline(y=0.3, color='y', linestyle='--', label='Borderline (0.3)')
        plt.axhline(y=config.VIOLATION_THRESHOLD, color='r', linestyle='--', label=f'Violation ({config.VIOLATION_THRESHOLD})')
        plt.axhline(y=config.HIGH_RISK_THRESHOLD, color='darkred', linestyle='--', label=f'High Risk ({config.HIGH_RISK_THRESHOLD})')
        
        plt.ylim(0, 1.0)
        plt.xlabel('Time (seconds)')
        plt.ylabel('Violation Score')
        plt.title('Policy Violation Score Timeline')
        plt.legend(loc='upper right')
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig(timeline_chart_path, dpi=150)
        plt.close()

        summary_text = (
            f"Analyzed {total_frames} frames. "
            f"Flagged {flagged_frames} frames (Violation rate: {violation_rate:.1f}%). "
            f"Overall video risk level is {overall_risk}. "
            f"Found {len(flagged_segments)} distinct violation segments."
        )

        return {
            "total_frames": total_frames,
            "flagged_frames": flagged_frames,
            "violation_rate": violation_rate,
            "overall_risk": overall_risk,
            "flagged_segments": flagged_segments,
            "timeline_chart_path": timeline_chart_path,
            "summary_text": summary_text
        }

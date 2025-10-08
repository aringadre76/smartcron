import joblib
import numpy as np
import os
from typing import Dict, Optional, Tuple
from pathlib import Path


class AIPredictor:
    
    def __init__(self, model_path: str = "models/model.pkl"):
        self.model_path = model_path
        self.model = None
        self.feature_columns = [
            'avg_cpu_load_5m',
            'cpu_percent',
            'ram_percent_used',
            'battery_level',
            'is_charging',
            'idle_time_sec',
            'last_job_success',
            'time_of_day'
        ]
        
        self._load_model()
    
    def _load_model(self):
        if os.path.exists(self.model_path):
            try:
                self.model = joblib.load(self.model_path)
                print(f"AI model loaded from {self.model_path}")
            except Exception as e:
                print(f"Error loading model: {e}")
                self.model = None
        else:
            print(f"Model not found at {self.model_path}. AI predictions will use fallback logic.")
            self.model = None
    
    def prepare_features(self, system_metrics: Dict, job_info: Dict) -> np.ndarray:
        from datetime import datetime
        
        features = {
            'avg_cpu_load_5m': system_metrics.get('cpu', {}).get('load_5m', 0),
            'cpu_percent': system_metrics.get('cpu', {}).get('cpu_percent', 0),
            'ram_percent_used': system_metrics.get('memory', {}).get('percent', 0),
            'battery_level': system_metrics.get('battery', {}).get('percent', 100) if system_metrics.get('battery') else 100,
            'is_charging': int(system_metrics.get('battery', {}).get('is_charging', True)) if system_metrics.get('battery') else 1,
            'idle_time_sec': system_metrics.get('idle_time_sec', 0) or 0,
            'last_job_success': int(job_info.get('last_job_success', 1)),
            'time_of_day': datetime.now().hour
        }
        
        feature_array = np.array([[features[col] for col in self.feature_columns]])
        return feature_array
    
    def predict(self, system_metrics: Dict, job_info: Dict) -> Tuple[float, str]:
        features = self.prepare_features(system_metrics, job_info)
        
        if self.model is not None:
            try:
                probability = self.model.predict_proba(features)[0][1]
                
                decision_reason = f"AI model predicts {probability:.2%} success probability"
                
                return probability, decision_reason
            except Exception as e:
                print(f"Error during prediction: {e}")
                return self._fallback_prediction(system_metrics, job_info)
        else:
            return self._fallback_prediction(system_metrics, job_info)
    
    def _fallback_prediction(self, system_metrics: Dict, job_info: Dict) -> Tuple[float, str]:
        score = 1.0
        reasons = []
        
        cpu_percent = system_metrics.get('cpu', {}).get('cpu_percent', 0)
        if cpu_percent > 80:
            score -= 0.3
            reasons.append("high CPU load")
        elif cpu_percent > 60:
            score -= 0.1
            reasons.append("moderate CPU load")
        
        ram_percent = system_metrics.get('memory', {}).get('percent', 0)
        if ram_percent > 90:
            score -= 0.2
            reasons.append("high RAM usage")
        elif ram_percent > 80:
            score -= 0.1
            reasons.append("moderate RAM usage")
        
        battery = system_metrics.get('battery')
        if battery:
            if not battery.get('is_charging') and battery.get('percent', 100) < 30:
                score -= 0.4
                reasons.append("low battery")
            elif not battery.get('is_charging') and battery.get('percent', 100) < 50:
                score -= 0.1
                reasons.append("moderate battery")
        
        idle_time = system_metrics.get('idle_time_sec', 0) or 0
        if idle_time > 300:
            score += 0.1
            reasons.append("user idle")
        
        if not job_info.get('last_job_success', True):
            score -= 0.2
            reasons.append("previous job failed")
        
        score = max(0.0, min(1.0, score))
        
        decision_reason = "Fallback heuristic: " + ", ".join(reasons) if reasons else "Fallback heuristic: conditions are good"
        
        return score, decision_reason
    
    def get_decision_score(self, system_metrics: Dict, job_info: Dict) -> Dict[str, any]:
        probability, reason = self.predict(system_metrics, job_info)
        
        if probability >= 0.8:
            decision = "run_now"
        elif probability >= 0.5:
            decision = "defer"
        else:
            decision = "skip"
        
        return {
            "probability_of_success": probability,
            "decision": decision,
            "reason": reason,
            "expected_runtime": job_info.get('avg_execution_time', 60)
        }


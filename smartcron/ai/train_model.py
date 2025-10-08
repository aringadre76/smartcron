import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score
import joblib
import sqlite3
import os
from typing import Optional


class ModelTrainer:
    
    def __init__(self, db_path: str = "/var/lib/smartcron/logs.db"):
        self.db_path = db_path
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
    
    def load_training_data(self) -> pd.DataFrame:
        conn = sqlite3.connect(self.db_path)
        
        query = """
            SELECT 
                je.job_name,
                je.start_time,
                je.success,
                je.system_state,
                je.execution_time_sec
            FROM job_executions je
            WHERE je.system_state IS NOT NULL
        """
        
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        return df
    
    def prepare_features(self, df: pd.DataFrame) -> pd.DataFrame:
        import json
        
        features = []
        
        for idx, row in df.iterrows():
            try:
                system_state = json.loads(row['system_state'])
                
                feature_dict = {
                    'avg_cpu_load_5m': system_state.get('cpu', {}).get('load_5m', 0),
                    'cpu_percent': system_state.get('cpu', {}).get('cpu_percent', 0),
                    'ram_percent_used': system_state.get('memory', {}).get('percent', 0),
                    'battery_level': system_state.get('battery', {}).get('percent', 100) if system_state.get('battery') else 100,
                    'is_charging': int(system_state.get('battery', {}).get('is_charging', True)) if system_state.get('battery') else 1,
                    'idle_time_sec': system_state.get('idle_time_sec', 0) or 0,
                    'last_job_success': 1,
                    'time_of_day': pd.to_datetime(row['start_time'], unit='s').hour,
                    'success': int(row['success'])
                }
                
                features.append(feature_dict)
            except (json.JSONDecodeError, KeyError) as e:
                continue
        
        return pd.DataFrame(features)
    
    def train(self, test_size: float = 0.2, random_state: int = 42):
        df = self.load_training_data()
        
        if len(df) < 10:
            print(f"Not enough training data: {len(df)} records. Need at least 10.")
            return None
        
        features_df = self.prepare_features(df)
        
        if len(features_df) == 0:
            print("No valid features could be extracted from training data.")
            return None
        
        X = features_df[self.feature_columns]
        y = features_df['success']
        
        print(f"Training with {len(X)} samples")
        print(f"Success rate: {y.mean():.2%}")
        
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=random_state
        )
        
        self.model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            random_state=random_state,
            class_weight='balanced'
        )
        
        self.model.fit(X_train, y_train)
        
        y_pred = self.model.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        
        print(f"\nModel Accuracy: {accuracy:.2%}")
        print("\nClassification Report:")
        print(classification_report(y_test, y_pred))
        
        feature_importance = pd.DataFrame({
            'feature': self.feature_columns,
            'importance': self.model.feature_importances_
        }).sort_values('importance', ascending=False)
        
        print("\nFeature Importance:")
        print(feature_importance)
        
        return self.model
    
    def save_model(self, model_path: str = "models/model.pkl"):
        if self.model is None:
            raise ValueError("No model to save. Train a model first.")
        
        os.makedirs(os.path.dirname(model_path), exist_ok=True)
        joblib.dump(self.model, model_path)
        print(f"Model saved to {model_path}")
    
    def generate_synthetic_data(self, n_samples: int = 1000, output_db: Optional[str] = None):
        if output_db is None:
            output_db = self.db_path
        
        conn = sqlite3.connect(output_db)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS job_executions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_name TEXT NOT NULL,
                start_time REAL NOT NULL,
                end_time REAL,
                exit_code INTEGER,
                stdout TEXT,
                stderr TEXT,
                execution_time_sec REAL,
                system_state TEXT,
                ai_decision_reason TEXT,
                success BOOLEAN,
                timestamp TEXT
            )
        ''')
        
        import json
        import time
        from datetime import datetime, timedelta
        
        base_time = time.time() - (n_samples * 3600)
        
        for i in range(n_samples):
            cpu_load = np.random.uniform(0, 100)
            ram_percent = np.random.uniform(20, 95)
            battery = np.random.uniform(20, 100)
            is_charging = np.random.choice([0, 1], p=[0.3, 0.7])
            idle_time = np.random.exponential(300)
            
            success_prob = 0.9
            if cpu_load > 80:
                success_prob -= 0.3
            if ram_percent > 90:
                success_prob -= 0.2
            if battery < 30 and not is_charging:
                success_prob -= 0.4
            
            success_prob = max(0.1, min(0.99, success_prob))
            success = np.random.choice([0, 1], p=[1-success_prob, success_prob])
            
            system_state = {
                "timestamp": base_time + i * 3600,
                "cpu": {
                    "load_5m": cpu_load / 20,
                    "cpu_percent": cpu_load
                },
                "memory": {
                    "percent": ram_percent
                },
                "battery": {
                    "percent": battery,
                    "is_charging": bool(is_charging)
                },
                "idle_time_sec": int(idle_time)
            }
            
            cursor.execute('''
                INSERT INTO job_executions 
                (job_name, start_time, end_time, exit_code, execution_time_sec, 
                 system_state, success, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                "synthetic_job",
                base_time + i * 3600,
                base_time + i * 3600 + 30,
                0 if success else 1,
                30.0,
                json.dumps(system_state),
                success,
                datetime.fromtimestamp(base_time + i * 3600).isoformat()
            ))
        
        conn.commit()
        conn.close()
        print(f"Generated {n_samples} synthetic training samples in {output_db}")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Train SmartCron AI model")
    parser.add_argument("--db", default="/var/lib/smartcron/logs.db", help="Path to logs database")
    parser.add_argument("--output", default="models/model.pkl", help="Path to save trained model")
    parser.add_argument("--generate", type=int, help="Generate N synthetic training samples")
    
    args = parser.parse_args()
    
    trainer = ModelTrainer(db_path=args.db)
    
    if args.generate:
        trainer.generate_synthetic_data(n_samples=args.generate)
    
    model = trainer.train()
    
    if model is not None:
        trainer.save_model(args.output)
    else:
        print("Training failed. Check if there is enough data in the database.")


if __name__ == "__main__":
    main()


"""
Simple ML model for fraud detection.
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score
import joblib
import os

class FraudDetector:
    """Fraud detection model with training and inference."""
    
    def __init__(self, model_path: str = "data/fraud_model.pkl"):
        self.model_path = model_path
        self.model = None
        
        if os.path.exists(model_path):
            self.model = joblib.load(model_path)
    
    def generate_synthetic_data(self, n_samples: int = 10000) -> pd.DataFrame:
        """Generate synthetic transaction data for training."""
        np.random.seed(42)
        
        data = {
            'amount': np.random.uniform(10, 50000, n_samples),
            'hour': np.random.randint(0, 24, n_samples),
            'day_of_week': np.random.randint(0, 7, n_samples),
            'user_avg_amount': np.random.uniform(50, 2000, n_samples),
            'user_tx_count': np.random.randint(1, 100, n_samples),
            'device_fingerprint_match': np.random.choice([0, 1], n_samples, p=[0.1, 0.9]),
            'location_distance_km': np.random.exponential(10, n_samples),
            'is_fraud': np.zeros(n_samples)
        }
        
        df = pd.DataFrame(data)
        
        # Inject fraud patterns
        fraud_mask = (
            (df['amount'] > 10000) |
            (df['hour'].between(1, 4)) |
            (df['device_fingerprint_match'] == 0)
        )
        
        # 30% of flagged transactions are fraud
        fraud_indices = np.where(fraud_mask)[0]
        fraud_count = int(len(fraud_indices) * 0.3)
        df.loc[fraud_indices[:fraud_count], 'is_fraud'] = 1
        
        # Additional random fraud (2%)
        random_fraud = np.random.choice(df.index, size=int(n_samples * 0.02), replace=False)
        df.loc[random_fraud, 'is_fraud'] = 1
        
        return df
    
    def train(self):
        """Train the fraud detection model."""
        print("Generating synthetic training data...")
        df = self.generate_synthetic_data(50000)
        
        feature_cols = ['amount', 'hour', 'day_of_week', 'user_avg_amount', 
                       'user_tx_count', 'device_fingerprint_match', 'location_distance_km']
        
        X = df[feature_cols]
        y = df['is_fraud']
        
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        print(f"Training on {len(X_train)} samples...")
        self.model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            random_state=42,
            class_weight='balanced'
        )
        self.model.fit(X_train, y_train)
        
        # Evaluate
        y_pred = self.model.predict(X_test)
        
        print(f"Accuracy: {accuracy_score(y_test, y_pred):.4f}")
        print(f"Precision: {precision_score(y_test, y_pred):.4f}")
        print(f"Recall: {recall_score(y_test, y_pred):.4f}")
        
        # Save model
        os.makedirs('data', exist_ok=True)
        joblib.dump(self.model, self.model_path)
        print(f"Model saved to {self.model_path}")
        
        return self.model
    
    def predict(self, features: dict) -> dict:
        """Predict fraud probability for a single transaction."""
        if self.model is None:
            raise ValueError("Model not trained. Call train() first.")
        
        # Convert features to DataFrame
        df = pd.DataFrame([features])
        
        # Get prediction
        probability = float(self.model.predict_proba(df)[0, 1])
        prediction = int(probability >= 0.5)
        
        return {
            "fraud_probability": round(probability, 4),
            "is_fraud": bool(prediction),
            "confidence": round(probability if prediction else 1 - probability, 4)
        }

# Singleton instance
fraud_detector = FraudDetector()

"""
Prediction endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
import logging

from app.services.auth_service import get_current_user, rate_limiter
from app.models.ml_model import fraud_detector

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/predict", tags=["Prediction"])

class TransactionRequest(BaseModel):
    """Transaction data for fraud prediction."""
    transaction_id: str
    amount: float = Field(..., gt=0, le=100000)
    hour: int = Field(..., ge=0, le=23)
    day_of_week: int = Field(..., ge=0, le=6)
    user_avg_amount: float = Field(..., gt=0)
    user_tx_count: int = Field(..., ge=1)
    device_fingerprint_match: int = Field(..., ge=0, le=1)
    location_distance_km: float = Field(..., ge=0)
    
    class Config:
        json_schema_extra = {
            "example": {
                "transaction_id": "TXN_123456",
                "amount": 15000.00,
                "hour": 14,
                "day_of_week": 2,
                "user_avg_amount": 500.00,
                "user_tx_count": 45,
                "device_fingerprint_match": 1,
                "location_distance_km": 2.5
            }
        }

class PredictionResponse(BaseModel):
    """Prediction response."""
    transaction_id: str
    fraud_probability: float
    is_fraud: bool
    confidence: float
    timestamp: str
    recommendation: str

@router.post("/", response_model=PredictionResponse)
async def predict_fraud(
    request: Request,
    transaction: TransactionRequest,
    current_user = Depends(get_current_user)
):
    """
    Predict fraud probability for a transaction.
    
    Requires authentication via JWT token.
    Rate limited based on user's API key.
    """
    
    # Check rate limit
    api_key = request.headers.get("X-API-Key", "")
    if not rate_limiter.check_rate_limit(api_key):
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded. 100 requests per day maximum."
        )
    
    # Log request
    logger.info(f"Prediction request from user {current_user['user_id']} for transaction {transaction.transaction_id}")
    
    # Make prediction
    features = transaction.dict(exclude={'transaction_id'})
    result = fraud_detector.predict(features)
    
    # Determine recommendation
    if result['fraud_probability'] < 0.3:
        recommendation = "APPROVE"
    elif result['fraud_probability'] < 0.7:
        recommendation = "MANUAL_REVIEW"
    else:
        recommendation = "BLOCK"
    
    return PredictionResponse(
        transaction_id=transaction.transaction_id,
        fraud_probability=result['fraud_probability'],
        is_fraud=result['is_fraud'],
        confidence=result['confidence'],
        timestamp=datetime.utcnow().isoformat(),
        recommendation=recommendation
    )

@router.post("/batch")
async def batch_predict(
    transactions: List[TransactionRequest],
    current_user = Depends(get_current_user)
):
    """Batch prediction for multiple transactions."""
    
    results = []
    for tx in transactions:
        features = tx.dict(exclude={'transaction_id'})
        result = fraud_detector.predict(features)
        results.append({
            "transaction_id": tx.transaction_id,
            **result
        })
    
    return {
        "total": len(results),
        "results": results,
        "summary": {
            "fraud_count": sum(1 for r in results if r['is_fraud']),
            "avg_probability": sum(r['fraud_probability'] for r in results) / len(results)
        }
    }

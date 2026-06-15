"""
Authentication endpoints.
"""

from fastapi import APIRouter, HTTPException, status, Depends
from datetime import datetime, timedelta
import secrets

from app.models.user import UserCreate, UserLogin, TokenResponse, hash_password, verify_password, generate_api_key
from app.services.auth_service import create_access_token, get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])

# In-memory user store (use database in production)
users_db = {}

@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register_user(user_data: UserCreate):
    """Register a new user."""
    
    if user_data.email in users_db:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    user_id = f"user_{secrets.token_hex(8)}"
    api_key = generate_api_key()
    
    user = {
        "user_id": user_id,
        "email": user_data.email,
        "name": user_data.name,
        "role": user_data.role,
        "api_key": api_key,
        "api_key_created_at": datetime.utcnow(),
        "hashed_password": hash_password(user_data.password),
        "created_at": datetime.utcnow(),
        "is_active": True,
        "rate_limit_per_day": 100 if user_data.role == "readonly" else 1000 if user_data.role == "analyst" else 10000
    }
    
    users_db[user_data.email] = user
    
    return {
        "message": "User registered successfully",
        "user_id": user_id,
        "api_key": api_key,
        "role": user_data.role
    }

@router.post("/login", response_model=TokenResponse)
async def login(login_data: UserLogin):
    """Login and receive JWT token."""
    
    user = users_db.get(login_data.email)
    if not user or not verify_password(login_data.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    if not user["is_active"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account disabled"
        )
    
    # Create JWT token
    access_token = create_access_token(
        data={"sub": user["user_id"], "role": user["role"], "email": user["email"]}
    )
    
    return TokenResponse(
        access_token=access_token,
        api_key=user["api_key"],
        expires_in=60 * 60 * 24
    )

@router.get("/me")
async def get_current_user_info(current_user = Depends(get_current_user)):
    """Get current user information."""
    return current_user

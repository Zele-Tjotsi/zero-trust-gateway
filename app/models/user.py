"""
User models for authentication and authorization.
"""

from pydantic import BaseModel, EmailStr
from typing import Optional, Literal
from datetime import datetime
import hashlib
import secrets

def hash_password(password: str) -> str:
    """Simple password hashing using SHA-256."""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return hash_password(plain_password) == hashed_password

def generate_api_key() -> str:
    """Generate a unique API key."""
    return f"zk_{secrets.token_urlsafe(32)}"

class UserRole:
    ADMIN = "admin"
    ANALYST = "analyst"
    READONLY = "readonly"

class User(BaseModel):
    user_id: str
    email: EmailStr
    name: str
    role: Literal["admin", "analyst", "readonly"]
    api_key: str
    api_key_created_at: datetime
    api_key_last_used: Optional[datetime] = None
    rate_limit_per_day: int = 100
    created_at: datetime
    is_active: bool = True

class UserCreate(BaseModel):
    email: EmailStr
    name: str
    password: str
    role: Literal["admin", "analyst", "readonly"] = "readonly"

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    api_key: str
    expires_in: int

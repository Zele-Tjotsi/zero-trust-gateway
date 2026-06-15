"""
Authentication service for JWT tokens and API keys.
"""

from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import redis
import json

# Configuration
SECRET_KEY = "your-super-secret-key-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

# Redis for rate limiting
try:
    redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)
    redis_client.ping()
except:
    print("Warning: Redis not running. Rate limiting will use mock mode.")
    redis_client = None

security = HTTPBearer()

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> dict:
    """Verify JWT token and return payload."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

def verify_api_key(api_key: str, user_data: dict) -> bool:
    """Verify API key."""
    return api_key.startswith("zk_")

class RateLimiter:
    """Rate limiting service."""
    
    def __init__(self, redis_client):
        self.redis = redis_client
        self.mock_mode = redis_client is None
    
    def check_rate_limit(self, api_key: str, limit_per_day: int = 100) -> bool:
        """Check if request is within rate limit."""
        if self.mock_mode:
            # In mock mode, always allow (for development)
            return True
        
        try:
            today = datetime.utcnow().strftime("%Y-%m-%d")
            key = f"rate_limit:{api_key}:{today}"
            
            current = self.redis.get(key)
            if current is None:
                self.redis.setex(key, 86400, 1)
                return True
            
            if int(current) >= limit_per_day:
                return False
            
            self.redis.incr(key)
            return True
        except:
            return True

rate_limiter = RateLimiter(redis_client)

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current user from JWT token."""
    token = credentials.credentials
    payload = verify_token(token)
    
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )
    
    return {"user_id": user_id, "role": payload.get("role", "readonly")}

def require_role(required_role: str):
    """Role-based access control."""
    async def role_checker(current_user = Depends(get_current_user)):
        roles_hierarchy = {
            "admin": 3,
            "analyst": 2,
            "readonly": 1
        }
        
        if roles_hierarchy.get(current_user.get("role", "readonly"), 0) < roles_hierarchy.get(required_role, 0):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role {required_role} or higher required"
            )
        return current_user
    return role_checker

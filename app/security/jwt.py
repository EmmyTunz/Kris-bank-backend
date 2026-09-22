from datetime import datetime, timedelta, timezone

import jwt
import hashlib

from app.core.config import JWT_SECRET_KEY, JWT_ALGORITHM

def create_access_token(user_id: int) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=30)

    payload = {
        "sub": str(user_id),
        "type": "access",
        "exp": expire
    }

    return jwt.encode(
        payload,
        JWT_SECRET_KEY,
        algorithm=JWT_ALGORITHM
    )

def create_refresh_token(user_id: int) -> str:
    expire = datetime.now(timezone.utc) + timedelta(days=1)
    payload = {
        "sub": str(user_id),
        "type": "refresh",
        "exp": expire
    }

    return jwt.encode(
        payload,
        JWT_SECRET_KEY,
        algorithm=JWT_ALGORITHM
    )

def hash_refresh_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()
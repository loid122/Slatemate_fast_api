# app/core/security.py
from datetime import datetime, timedelta
import jwt  # PyJWT
from app.db.config import settings


def create_access_token(data: dict, expires_delta: int = None):
    """
    Generate a JWT access token using PyJWT
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(
        minutes=expires_delta or settings.jwt_expire_minutes
    )
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode,
        settings.jwt_secret,
        algorithm=settings.jwt_algorithm
    )
    return encoded_jwt


def decode_access_token(token: str):
    """
    Decode a JWT access token and return payload if valid
    """
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm]
        )
        return payload
    except jwt.ExpiredSignatureError:
        # Token has expired
        return None
    except jwt.InvalidTokenError:
        # Any other error (bad signature, malformed, etc.)
        return None

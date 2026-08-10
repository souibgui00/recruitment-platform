import os
import secrets
from datetime import datetime, timedelta
from jose import jwt
from passlib.context import CryptContext

# CryptContext for password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT configuration - support both JWT_SECRET_KEY and SECRET_KEY for compatibility
SECRET_KEY = os.environ.get("JWT_SECRET_KEY") or os.environ.get("SECRET_KEY")
if not SECRET_KEY:
    import warnings
    SECRET_KEY = secrets.token_urlsafe(32)
    warnings.warn(
        "No JWT_SECRET_KEY or SECRET_KEY environment variable set. "
        f"Using ephemeral key: {SECRET_KEY[:8]}... "
        "Set a persistent key in production!"
    )
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 1 day expiration for development convenience

def hash_password(password: str) -> str:
    """Hash password using bcrypt."""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify standard plain text password against bcrypt hash."""
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: timedelta = None) -> str:
    """Generate JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

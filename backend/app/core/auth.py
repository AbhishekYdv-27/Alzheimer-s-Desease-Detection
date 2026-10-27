from datetime import datetime, timedelta, timezone
from typing import Optional
import hashlib
import hmac
import base64
import secrets
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from backend.app.core.config import settings

# Keep a stable development key unless a real secret is configured. Using a
# randomly generated value every process start invalidates JWTs after restarts.
DEFAULT_SECRET_KEY = "dev-secret-key-change-me-in-production"
APP_ENV = settings.app_env.strip().lower()
IS_PRODUCTION = APP_ENV in {"production", "prod"}
configured_secret = settings.secret_key.strip() if settings.secret_key else None

if IS_PRODUCTION and (
    not configured_secret
    or configured_secret == DEFAULT_SECRET_KEY
    or configured_secret.lower() in {"replace-with-a-long-random-secret", "change-me"}
    or len(configured_secret) < 32
):
    raise RuntimeError("Production requires a SECRET_KEY of at least 32 characters")

SECRET_KEY = configured_secret or DEFAULT_SECRET_KEY
ALGORITHM = settings.jwt_algorithm
ACCESS_TOKEN_EXPIRE_MINUTES = settings.access_token_expire_minutes

security = HTTPBearer()


def create_password_hash(password: str) -> str:
    salt = secrets.token_hex(16)
    hash_obj = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
    return f"{salt}${base64.b64encode(hash_obj).decode()}"


def verify_password(plain_password: str, stored_hash: str) -> bool:
    try:
        salt, stored_b64 = stored_hash.split('$')
        stored_bytes = base64.b64decode(stored_b64)
        hash_obj = hashlib.pbkdf2_hmac('sha256', plain_password.encode(), salt.encode(), 100000)
        return hmac.compare_digest(hash_obj, stored_bytes)
    except Exception:
        return False


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    from jose import jwt

    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> Optional[dict]:
    from jose import JWTError, jwt

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> str:
    token = credentials.credentials
    payload = decode_token(token)

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id: str = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user_id


async def get_current_user(user_id: str = Depends(get_current_user_id)) -> dict:
    from backend.app.core.database import get_user_by_id

    user = get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


def require_role(role: str):
    async def role_dependency(user: dict = Depends(get_current_user)) -> dict:
        if user.get("role", "patient") != role:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="This portal is restricted to the required role")
        return user
    return role_dependency

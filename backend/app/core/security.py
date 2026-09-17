import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from app.core.config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES

MIN_PASSWORD_LENGTH = 6


def _legacy_hash(password: str) -> str:
    salt = "smartrail_ktz_salt"
    return hashlib.sha256((password + salt).encode("utf-8")).hexdigest()


def hash_password(password: str) -> str:
    """PBKDF2-HMAC-SHA256 with per-user salt. Format: pbkdf2$<salt_hex>$<hash_hex>."""
    salt = secrets.token_hex(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), bytes.fromhex(salt), 200_000)
    return f"pbkdf2${salt}${dk.hex()}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    # Backward compatibility with demo accounts created by the old scheme
    if hashed_password and not hashed_password.startswith("pbkdf2$"):
        return _legacy_hash(plain_password) == hashed_password
    try:
        _, salt, expected = hashed_password.split("$")
        dk = hashlib.pbkdf2_hmac("sha256", plain_password.encode("utf-8"), bytes.fromhex(salt), 200_000)
        return secrets.compare_digest(dk.hex(), expected)
    except Exception:
        return False


def needs_rehash(hashed_password: str) -> bool:
    return not (hashed_password or "").startswith("pbkdf2$")

def create_access_token(data: dict, expires_delta: timedelta = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


_bearer_optional = HTTPBearer(auto_error=False)


def _decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Сессия истекла, войдите заново")
    except jwt.PyJWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Недействительный токен")


def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer_optional),
):
    """Returns the logged-in User or None (for public/terminal endpoints)."""
    if credentials is None:
        return None
    # Local imports to avoid circulars at module load time
    from app.core.database import SessionLocal
    from app.models.models import User

    payload = _decode_token(credentials.credentials)
    user_id = payload.get("id")
    if not user_id:
        return None
    session = SessionLocal()
    try:
        user = session.query(User).filter(User.id == user_id).first()
        if user is not None:
            session.expunge(user)  # detach safely: guards only read loaded columns
        return user
    finally:
        session.close()


def require_login(user=Depends(get_current_user_optional)):
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Требуется вход в систему")
    return user


def require_roles(*roles: str):
    def checker(user=Depends(get_current_user_optional)):
        if user is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Требуется вход в систему")
        if user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Недостаточно прав: действие доступно другой роли",
            )
        return user

    return checker

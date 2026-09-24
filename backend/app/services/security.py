import uuid
from datetime import datetime, timedelta
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.models.user import User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
bearer_scheme = HTTPBearer()


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(subject: str) -> str:
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": subject, "exp": expire}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")


def get_current_user(
    creds: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Decodes the bearer token and loads the corresponding user. Raises
    401 on any failure — expired, malformed, or referencing a deleted
    user — rather than letting a bad token silently pass through."""
    try:
        payload = jwt.decode(creds.credentials, settings.SECRET_KEY, algorithms=["HS256"])
        raw_id = payload.get("sub")
        if not raw_id:
            raise JWTError("Missing subject claim")
        user_id = uuid.UUID(raw_id)
    except (JWTError, ValueError):
        raise HTTPException(401, "Invalid or expired token")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(401, "User no longer exists")
    return user


def require_staff(user: User = Depends(get_current_user)) -> User:
    """Gate for CHW/clinician/admin-only routes, like the escalation
    dashboard — a mother's own login should never see this data."""
    if user.role not in ("chw", "clinician", "admin"):
        raise HTTPException(403, "Staff access only")
    return user

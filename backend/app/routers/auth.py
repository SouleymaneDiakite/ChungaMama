from datetime import datetime, timedelta
import secrets

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import (
    UserCreate, UserOut, Token, ForgotPasswordRequest, ResetPasswordRequest,
)
from app.services.security import hash_password, verify_password, create_access_token, get_current_user

router = APIRouter()


def _find_user_by_identifier(db: Session, email: str | None, phone: str | None) -> User | None:
    """Looks up a user by email or phone, without ever comparing a column
    to Python None — Column == None compiles to IS NULL in SQL, which
    would otherwise match any other row where that column happens to be
    null (e.g. any other phone-only account when email is None here)."""
    filters = []
    if email:
        filters.append(User.email == email)
    if phone:
        filters.append(User.phone == phone)
    if not filters:
        return None
    return db.query(User).filter(or_(*filters)).first()


@router.post("/register", response_model=UserOut)
def register(payload: UserCreate, db: Session = Depends(get_db)):
    if not payload.email and not payload.phone:
        raise HTTPException(400, "Provide an email or phone number")

    existing = _find_user_by_identifier(db, payload.email, payload.phone)
    if existing:
        raise HTTPException(409, "An account with this email or phone already exists")

    user = User(
        full_name=payload.full_name,
        email=payload.email,
        phone=payload.phone,
        hashed_password=hash_password(payload.password),
        role=payload.role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=Token)
def login(payload: UserCreate, db: Session = Depends(get_db)):
    user = _find_user_by_identifier(db, payload.email, payload.phone)
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(401, "Incorrect credentials")

    token = create_access_token(subject=str(user.id))
    return Token(access_token=token)


@router.get("/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)):
    return current_user


@router.post("/forgot-password")
def forgot_password(payload: ForgotPasswordRequest, db: Session = Depends(get_db)):
    user = _find_user_by_identifier(db, payload.email, payload.phone)

    # Always return the same generic response whether or not the account
    # exists — this prevents the endpoint being used to check which
    # emails/phone numbers are registered.
    generic_response = {"message": "If that account exists, a reset link has been sent."}

    if not user:
        return generic_response

    token = secrets.token_urlsafe(32)
    user.reset_token = token
    user.reset_token_expires = datetime.utcnow() + timedelta(minutes=30)
    db.commit()

    # DEV-ONLY: there's no email/SMS provider wired up yet, so the reset
    # link is just logged here instead of actually being sent. Before any
    # real deployment, this needs to go out via email (e.g. SendGrid) or
    # SMS (Africa's Talking, already the planned vendor for the rest of
    # the app) — never returned in the API response itself, and never
    # left only in server logs where anyone with log access can use it.
    reset_link = f"http://localhost:3000/reset-password?token={token}"
    print(f"[DEV] Password reset requested for {payload.email or payload.phone}")
    print(f"[DEV] Reset link (send this via email/SMS in production): {reset_link}")

    return generic_response


@router.post("/reset-password")
def reset_password(payload: ResetPasswordRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.reset_token == payload.token).first()

    if not user or not user.reset_token_expires or user.reset_token_expires < datetime.utcnow():
        raise HTTPException(400, "This reset link is invalid or has expired")

    user.hashed_password = hash_password(payload.new_password)
    user.reset_token = None
    user.reset_token_expires = None
    db.commit()

    return {"message": "Password updated successfully"}

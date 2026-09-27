import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database import get_db
from app import models, schemas
from app.auth.security import (
    hash_password, verify_password, create_access_token, generate_refresh_token,
)
from app.auth.dependencies import get_current_user
from app.logger import logger
from app.rate_limit import rate_limit

router = APIRouter(prefix="/auth", tags=["auth"])


# ---------- Request models ----------
class ForgotPasswordRequest(BaseModel):
    email: str

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str

class ProfileUpdateRequest(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None

class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str

class RefreshRequest(BaseModel):
    refresh_token: str


# ---------- Register ----------
@router.post("/register", response_model=schemas.UserResponse, status_code=201)
def register(payload: schemas.UserCreate, db: Session = Depends(get_db)):
    existing = db.query(models.User).filter(models.User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    user = models.User(
        name=payload.name,
        email=payload.email,
        password_hash=hash_password(payload.password),
        role=payload.role or "student",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


# ---------- Login ----------
@router.post("/login", response_model=schemas.TokenResponse)
def login(
    form: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
    _rl=Depends(rate_limit(max_requests=5, window_seconds=60)),
):
    user = db.query(models.User).filter(models.User.email == form.username).first()
    if not user or not verify_password(form.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access = create_access_token({"sub": user.email, "role": user.role})
    refresh = generate_refresh_token()
    db.add(models.RefreshToken(
        user_id=user.id,
        token=refresh,
        expires_at=datetime.now(timezone.utc) + timedelta(days=30),
    ))
    db.commit()
    return {
        "access_token": access,
        "refresh_token": refresh,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role": user.role,
        },
    }


# ---------- Refresh ----------
@router.post("/refresh")
def refresh_access_token(payload: RefreshRequest, db: Session = Depends(get_db)):
    row = db.query(models.RefreshToken).filter(
        models.RefreshToken.token == payload.refresh_token,
        models.RefreshToken.revoked == False,
    ).first()
    if not row:
        raise HTTPException(401, "Invalid refresh token")
    exp = row.expires_at
    if exp.tzinfo is None:
        exp = exp.replace(tzinfo=timezone.utc)
    if exp < datetime.now(timezone.utc):
        raise HTTPException(401, "Refresh token expired")
    user = db.query(models.User).filter(models.User.id == row.user_id).first()
    if not user:
        raise HTTPException(404, "User not found")
    new_access = create_access_token({"sub": user.email, "role": user.role})
    return {"access_token": new_access, "token_type": "bearer"}


# ---------- Logout ----------
@router.post("/logout")
def logout(payload: RefreshRequest, db: Session = Depends(get_db)):
    row = db.query(models.RefreshToken).filter(
        models.RefreshToken.token == payload.refresh_token
    ).first()
    if row:
        row.revoked = True
        db.commit()
    return {"message": "Logged out"}


# ---------- Revoke all sessions ----------
@router.post("/revoke-all")
def revoke_all(
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    db.query(models.RefreshToken).filter(
        models.RefreshToken.user_id == user.id,
        models.RefreshToken.revoked == False,
    ).update({"revoked": True})
    db.commit()
    return {"message": "All sessions revoked"}


# ---------- Current user ----------
@router.get("/me", response_model=schemas.UserResponse)
def me(user: models.User = Depends(get_current_user)):
    return user


# ---------- Update profile ----------
@router.patch("/me")
def update_profile(
    payload: ProfileUpdateRequest,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    if payload.name:
        user.name = payload.name
    if payload.email and payload.email != user.email:
        existing = db.query(models.User).filter(models.User.email == payload.email).first()
        if existing:
            raise HTTPException(400, "Email already in use")
        user.email = payload.email
    db.commit()
    db.refresh(user)
    return {"id": user.id, "name": user.name, "email": user.email, "role": user.role}


# ---------- Change password ----------
@router.post("/change-password")
def change_password(
    payload: ChangePasswordRequest,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    if not verify_password(payload.old_password, user.password_hash):
        raise HTTPException(400, "Incorrect current password")
    if len(payload.new_password) < 6:
        raise HTTPException(400, "New password must be at least 6 characters")
    user.password_hash = hash_password(payload.new_password)
    # Revoke all existing sessions
    db.query(models.RefreshToken).filter(
        models.RefreshToken.user_id == user.id,
        models.RefreshToken.revoked == False,
    ).update({"revoked": True})
    db.commit()
    return {"message": "Password changed. All other sessions revoked."}


# ---------- Forgot password ----------
@router.post("/forgot-password")
def forgot_password(
    payload: ForgotPasswordRequest,
    db: Session = Depends(get_db),
    _rl=Depends(rate_limit(max_requests=3, window_seconds=300)),
):
    user = db.query(models.User).filter(models.User.email == payload.email).first()
    if not user:
        return {"message": "If the email is registered, a reset link has been sent."}
    token = secrets.token_urlsafe(32)
    expires = datetime.now(timezone.utc) + timedelta(hours=1)
    db.add(models.PasswordResetToken(user_id=user.id, token=token, expires_at=expires))
    db.commit()
    logger.info(f"[Password Reset] user={user.email} token={token}")
    print(f"\n=== PASSWORD RESET LINK ===\nhttp://localhost:5173/reset-password?token={token}\n")
    return {
        "message": "Reset link generated.",
        "token": token,
        "reset_url": f"http://localhost:5173/reset-password?token={token}",
    }


# ---------- Reset password ----------
@router.post("/reset-password")
def reset_password(payload: ResetPasswordRequest, db: Session = Depends(get_db)):
    row = db.query(models.PasswordResetToken).filter(
        models.PasswordResetToken.token == payload.token,
        models.PasswordResetToken.used == False,
    ).first()
    if not row:
        raise HTTPException(400, "Invalid or used token")
    exp = row.expires_at
    if exp.tzinfo is None:
        exp = exp.replace(tzinfo=timezone.utc)
    if exp < datetime.now(timezone.utc):
        raise HTTPException(400, "Token expired")
    user = db.query(models.User).filter(models.User.id == row.user_id).first()
    if not user:
        raise HTTPException(404, "User not found")
    user.password_hash = hash_password(payload.new_password)
    row.used = True
    db.commit()
    return {"message": "Password reset successful. You can now log in."}

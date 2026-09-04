import os

from fastapi.responses import RedirectResponse
from fastapi import Request
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.services.google_oauth import oauth

from app.database.database import get_db
from app.dependencies.auth import get_current_user
from app.models.password_reset import PasswordResetToken
from app.models.user import User
from app.schemas.auth import (
    AuthResponse,
    ForgotPasswordRequest,
    LoginRequest,
    MeResponse,
    RegisterRequest,
    ResetPasswordRequest,
)
from app.services.auth import (
    create_access_token,
    create_password_reset_token,
    hash_password,
    hash_reset_token,
    verify_password,
)


router = APIRouter(
    prefix="/api/auth",
    tags=["Authentication"],
)


# ============================================================
# REGISTER
# ============================================================

@router.post(
    "/register",
    response_model=AuthResponse,
)
def register(
    data: RegisterRequest,
    db: Session = Depends(get_db),
):
    email = data.email.strip().lower()

    existing_user = (
        db.query(User)
        .filter(User.email == email)
        .first()
    )

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        )

    user = User(
        name=data.name.strip(),
        email=email,
        password_hash=hash_password(data.password),
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token(
        user_id=user.id,
        email=user.email,
    )

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
        },
    }


# ============================================================
# LOGIN
# ============================================================

@router.post(
    "/login",
    response_model=AuthResponse,
)
def login(
    data: LoginRequest,
    db: Session = Depends(get_db),
):
    email = data.email.strip().lower()

    user = (
        db.query(User)
        .filter(User.email == email)
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    if not verify_password(
        data.password,
        user.password_hash,
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This account is inactive.",
        )

    token = create_access_token(
        user_id=user.id,
        email=user.email,
    )

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
        },
    }


# ============================================================
# CURRENT USER
# ============================================================

@router.get(
    "/me",
    response_model=MeResponse,
)
def get_me(
    current_user: User = Depends(get_current_user),
):
    return {
        "user": {
            "id": current_user.id,
            "name": current_user.name,
            "email": current_user.email,
        },
    }
@router.get("/google/login")
async def google_login(request: Request):
    redirect_uri = os.getenv(
        "GOOGLE_REDIRECT_URI",
        "http://localhost:8000/api/auth/google/callback",
    )

    return await oauth.google.authorize_redirect(
        request,
        redirect_uri,
    )


# ============================================================
# FORGOT PASSWORD
# ============================================================

@router.post(
    "/forgot-password",
)
def forgot_password(
    data: ForgotPasswordRequest,
    db: Session = Depends(get_db),
):
    email = data.email.strip().lower()

    user = (
        db.query(User)
        .filter(User.email == email)
        .first()
    )

    # Generic response prevents account enumeration.
    if not user:
        return {
            "message": (
                "If an account exists with this email, "
                "a password reset link has been generated."
            )
        }

    # Invalidate previous unused tokens.
    db.query(PasswordResetToken).filter(
        PasswordResetToken.user_id == user.id,
        PasswordResetToken.used == False,
    ).update(
        {
            PasswordResetToken.used: True
        },
        synchronize_session=False,
    )

    raw_token, token_hash, expires_at = (
        create_password_reset_token()
    )

    reset_token = PasswordResetToken(
        user_id=user.id,
        token_hash=token_hash,
        expires_at=expires_at,
        used=False,
    )

    db.add(reset_token)
    db.commit()

    # --------------------------------------------------------
    # DEVELOPMENT MODE
    # --------------------------------------------------------
    # Email delivery will be connected later.
    # This allows us to test the complete flow locally.
    reset_link = (
        f"http://localhost:5173/reset-password"
        f"?token={raw_token}"
    )

    return {
        "message": (
            "If an account exists with this email, "
            "a password reset link has been generated."
        ),
        "reset_link": reset_link,
        "expires_in_minutes": 15,
    }


# ============================================================
# RESET PASSWORD
# ============================================================

@router.post(
    "/reset-password",
)
def reset_password(
    data: ResetPasswordRequest,
    db: Session = Depends(get_db),
):
    token_hash = hash_reset_token(
        data.token
    )

    reset_token = (
        db.query(PasswordResetToken)
        .filter(
            PasswordResetToken.token_hash
            == token_hash
        )
        .first()
    )

    if not reset_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token.",
        )

    if reset_token.used:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This reset link has already been used.",
        )

    if reset_token.expires_at < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This reset link has expired.",
        )

    user = (
        db.query(User)
        .filter(
            User.id == reset_token.user_id
        )
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unable to reset this account.",
        )

    user.password_hash = hash_password(
        data.new_password
    )

    reset_token.used = True

    db.commit()

    return {
        "message": (
            "Password reset successfully. "
            "You can now sign in with your new password."
        )
    }
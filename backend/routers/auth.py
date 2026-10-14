from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from models import User
from schemas import LoginRequest, TokenResponse
from auth_utils import verify_password, create_access_token, get_current_user

router = APIRouter(tags=["Authentication"])


@router.post("/login", response_model=TokenResponse)
def login(user_credentials: LoginRequest, db: Session = Depends(get_db)):
    """Authenticate a user and return a signed JWT access token."""
    user = (
        db.query(User)
        .filter(User.username == user_credentials.username.strip())
        .first()
    )

    if not user or not verify_password(user_credentials.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_access_token(data={"sub": user.username})

    return {
        "access_token": token,
        "token_type": "bearer",
        "username": user.username,
    }


@router.get("/auth/me")
def get_me(current_user: User = Depends(get_current_user)):
    """Return the profile of the currently authenticated user."""
    return {
        "id": current_user.id,
        "username": current_user.username
    }
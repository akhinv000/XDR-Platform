from fastapi import APIRouter, HTTPException
from sqlalchemy import text

from database import SessionLocal
from schemas import LoginRequest

router = APIRouter(tags=["Authentication"])


@router.post("/login")
def login(user: LoginRequest):

    db = SessionLocal()

    result = db.execute(
        text("""
            SELECT username, password
            FROM users
            WHERE username = :username
        """),
        {"username": user.username}
    ).fetchone()

    db.close()

    if result is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid username"
        )

    if result.password != user.password:
        raise HTTPException(
            status_code=401,
            detail="Invalid password"
        )

    return {
        "message": "Login Successful",
        "username": result.username
    }
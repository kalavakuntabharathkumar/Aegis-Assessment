import aiosqlite
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr

from database.db import get_db
from auth.jwt_auth import (
    Token,
    TokenData,
    hash_password,
    verify_password,
    create_access_token,
    get_current_user,
    ACCESS_TOKEN_EXPIRE_MINUTES,
)

router = APIRouter(prefix="/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    email: str
    password: str
    full_name: str = ""


class UserResponse(BaseModel):
    user_id: str
    email: str
    full_name: str
    created_at: str


@router.post("/register", response_model=UserResponse, status_code=201)
async def register(body: RegisterRequest, db: aiosqlite.Connection = Depends(get_db)):
    async with db.execute("SELECT id FROM users WHERE email = ?", (body.email,)) as cur:
        if await cur.fetchone():
            raise HTTPException(status_code=400, detail="Email already registered")

    if len(body.password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")

    hashed = hash_password(body.password)
    await db.execute(
        "INSERT INTO users (email, hashed_password, full_name) VALUES (?, ?, ?)",
        (body.email, hashed, body.full_name),
    )
    await db.commit()

    async with db.execute(
        "SELECT id, email, full_name, created_at FROM users WHERE email = ?", (body.email,)
    ) as cur:
        row = await cur.fetchone()

    return UserResponse(
        user_id=str(row["id"]),
        email=row["email"],
        full_name=row["full_name"] or "",
        created_at=str(row["created_at"]),
    )


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: aiosqlite.Connection = Depends(get_db),
):
    async with db.execute(
        "SELECT id, hashed_password FROM users WHERE email = ?", (form_data.username,)
    ) as cur:
        row = await cur.fetchone()

    if not row or not verify_password(form_data.password, row["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_access_token(
        {"sub": str(row["id"]), "email": form_data.username},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    return Token(
        access_token=token,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: TokenData = Depends(get_current_user),
    db: aiosqlite.Connection = Depends(get_db),
):
    async with db.execute(
        "SELECT id, email, full_name, created_at FROM users WHERE id = ?", (current_user.user_id,)
    ) as cur:
        row = await cur.fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="User not found")

    return UserResponse(
        user_id=str(row["id"]),
        email=row["email"],
        full_name=row["full_name"] or "",
        created_at=str(row["created_at"]),
    )


@router.get("/sessions")
async def get_my_sessions(
    current_user: TokenData = Depends(get_current_user),
    db: aiosqlite.Connection = Depends(get_db),
):
    async with db.execute(
        """SELECT id, candidate_name, role, status, experience_level, created_at
           FROM sessions WHERE user_id = ? ORDER BY created_at DESC LIMIT 20""",
        (current_user.user_id,),
    ) as cur:
        rows = await cur.fetchall()

    return {
        "sessions": [
            {
                "session_id": row["id"],
                "candidate_name": row["candidate_name"],
                "role": row["role"],
                "status": row["status"],
                "experience_level": row["experience_level"],
                "created_at": str(row["created_at"]),
            }
            for row in rows
        ]
    }

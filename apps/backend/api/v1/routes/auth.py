from uuid import UUID

from core.auth import (
    CREDENTIALS_EXCEPTION,
    create_access_token,
    create_refresh_token,
    decode_token,
    get_current_user,
)
from core.database import get_db
from core.exceptions import ConflictError, UnauthorizedError
from core.security import hash_password, verify_password
from fastapi import APIRouter, Depends
from models.user import User
from schemas.auth import RefreshRequest, TokenResponse, UserLogin, UserRegister, UserResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=201)
async def register(payload: UserRegister, db: AsyncSession = Depends(get_db)) -> User:
    existing_user = await db.scalar(select(User).where(User.email == payload.email))
    if existing_user is not None:
        raise ConflictError("Email already registered.")

    user = User(
        email=payload.email,
        hashed_password=hash_password(payload.password),
        full_name=payload.full_name,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@router.post("/login", response_model=TokenResponse)
async def login(payload: UserLogin, db: AsyncSession = Depends(get_db)) -> TokenResponse:
    user = await db.scalar(select(User).where(User.email == payload.email))
    if user is None or not verify_password(payload.password, user.hashed_password):
        raise UnauthorizedError("Incorrect email or password.")

    token_data = {"sub": str(user.id)}
    return TokenResponse(
        access_token=create_access_token(token_data),
        refresh_token=create_refresh_token(token_data),
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh(payload: RefreshRequest, db: AsyncSession = Depends(get_db)) -> TokenResponse:
    decoded = decode_token(payload.refresh_token)
    user_id = decoded.get("sub")
    if user_id is None:
        raise CREDENTIALS_EXCEPTION

    try:
        user_uuid = UUID(user_id)
    except ValueError as exc:
        raise CREDENTIALS_EXCEPTION from exc

    user = await db.scalar(select(User).where(User.id == user_uuid))
    if user is None:
        raise CREDENTIALS_EXCEPTION

    token_data = {"sub": str(user.id)}
    return TokenResponse(
        access_token=create_access_token(token_data),
        refresh_token=create_refresh_token(token_data),
    )


@router.get("/me", response_model=UserResponse)
async def me(current_user: User = Depends(get_current_user)) -> User:
    return current_user

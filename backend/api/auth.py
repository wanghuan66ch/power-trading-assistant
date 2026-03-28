"""
认证 API
"""
import uuid
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr

from core.database import AsyncSessionLocal, get_db
from core.security import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user_id,
    ACCESS_TOKEN_EXPIRE_MINUTES,
)
from models.user import User

router = APIRouter(prefix="/api/v1/auth", tags=["认证"])


# ---- Schema ----

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    username: str


class UserOut(BaseModel):
    id: str
    email: str
    username: str
    is_active: bool

    class Config:
        from_attributes = True


# ---- 内部工具 ----

async def get_user_by_email(db: AsyncSessionLocal, email: str) -> User | None:
    from sqlalchemy import select
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def authenticate_user(db: AsyncSessionLocal, email: str, password: str) -> User | None:
    user = await get_user_by_email(db, email)
    if not user or not verify_password(password, user.hashed_password):
        return None
    return user


# ---- 接口 ----

@router.post("/register", response_model=UserOut)
async def register(body: UserCreate, db: AsyncSessionLocal = Depends(get_db)):
    """注册新用户"""
    existing = await get_user_by_email(db, body.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该邮箱已被注册",
        )
    user = User(
        id=str(uuid.uuid4()),
        email=body.email,
        hashed_password=hash_password(body.password),
        username=body.username,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSessionLocal = Depends(get_db),
):
    """用户名/邮箱登录，返回 JWT token"""
    user = await authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="邮箱或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="账号已被禁用",
        )
    access_token = create_access_token(
        data={"sub": user.id},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    return Token(access_token=access_token)


@router.get("/me", response_model=UserOut)
async def get_me(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSessionLocal = Depends(get_db),
):
    """获取当前登录用户信息"""
    from sqlalchemy import select
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    return user

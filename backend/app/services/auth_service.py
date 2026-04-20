from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.user import User
from app.schemas.auth import (
    RegisterRequest,
    LoginRequest,
    UpdateProfileRequest,
    ChangePasswordRequest,
)
from app.utils.password import hash_password, verify_password
from app.utils.jwt import create_token, decode_token


class AuthService:

    async def register(self, db: AsyncSession, data: RegisterRequest) -> tuple[User, dict]:
        # 1. 이메일 중복 확인
        result = await db.execute(select(User).where(User.email == data.email))
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="이미 사용 중인 이메일입니다.",
            )
        # 2. 유저 생성
        user = User(
            email=data.email,
            name=data.name,
            hashed_password=hash_password(data.password),
            is_active=True,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)

        # 3. 토큰 발급
        tokens = self._issue_tokens(str(user.id))
        return user, tokens

    async def login(self, db: AsyncSession, data: LoginRequest) -> tuple[User, dict]:
        # 1. 유저 조회
        result = await db.execute(select(User).where(User.email == data.email))
        user = result.scalar_one_or_none()

        # 2. 검증
        if not user or not verify_password(data.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="이메일 또는 비밀번호가 올바르지 않습니다.",
            )
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="비활성화된 계정입니다.",
            )

        # 3. 토큰 발급
        tokens = self._issue_tokens(str(user.id))
        return user, tokens

    async def refresh_access_token(self, db: AsyncSession, refresh_token: str) -> str:
        payload = decode_token(refresh_token, "refresh")
        user_id = payload.get("sub")

        result = await db.execute(select(User).where(User.id == int(user_id)))
        user = result.scalar_one_or_none()
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="유효하지 않은 토큰입니다.",
            )
        return create_token(str(user.id), "access")

    async def update_profile(self, db: AsyncSession, user: User, data: UpdateProfileRequest) -> User:
        if data.name is not None:
            user.name = data.name
        await db.commit()
        await db.refresh(user)
        return user

    async def change_password(self, db: AsyncSession, user: User, data: ChangePasswordRequest) -> None:
        if not verify_password(data.current_password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="현재 비밀번호가 올바르지 않습니다.",
            )
        user.hashed_password = hash_password(data.new_password)
        await db.commit()

    async def deactivate_account(self, db: AsyncSession, user: User) -> None:
        user.is_active = False
        await db.commit()

    def _issue_tokens(self, user_id: str) -> dict:
        return {
            "access_token": create_token(user_id, "access"),
            "refresh_token": create_token(user_id, "refresh"),
        }


auth_service = AuthService()

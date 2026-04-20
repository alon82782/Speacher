from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import (
    RegisterRequest, RegisterResponse,
    LoginRequest, LoginResponse,
    RefreshRequest, RefreshResponse,
    UpdateProfileRequest, ChangePasswordRequest,
    UserProfile, TokenPair, MessageResponse,
)
from app.services.auth_service import auth_service
from app.utils.dependencies import get_current_user
from app.middleware.rate_limit import (
    login_rate_limit,
    register_rate_limit,
    refresh_rate_limit,
)

router = APIRouter(tags=["인증"])


@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED, summary="회원가입", dependencies=[Depends(register_rate_limit)])
async def register(data: RegisterRequest, db: AsyncSession = Depends(get_db)):
    user, tokens = await auth_service.register(db, data)
    return RegisterResponse(
        message="회원가입이 완료되었습니다.",
        user_id=user.id,
        tokens=TokenPair(**tokens),
    )


@router.post("/login", response_model=LoginResponse, summary="로그인", dependencies=[Depends(login_rate_limit)])
async def login(data: LoginRequest, db: AsyncSession = Depends(get_db)):
    user, tokens = await auth_service.login(db, data)
    return LoginResponse(
        message="로그인 성공",
        tokens=TokenPair(**tokens),
        user=UserProfile.model_validate(user),
    )


@router.post("/logout", response_model=MessageResponse, summary="로그아웃")
async def logout(_: User = Depends(get_current_user)):
    return MessageResponse(message="로그아웃 되었습니다.")


@router.post("/refresh", response_model=RefreshResponse, summary="Access Token 갱신", dependencies=[Depends(refresh_rate_limit)])
async def refresh(data: RefreshRequest, db: AsyncSession = Depends(get_db)):
    new_access_token = await auth_service.refresh_access_token(db, data.refresh_token)
    return RefreshResponse(access_token=new_access_token)


@router.get("/verify", response_model=MessageResponse, summary="토큰 유효성 확인")
async def verify_token(_: User = Depends(get_current_user)):
    return MessageResponse(message="유효한 토큰입니다.")


@router.get("/me", response_model=UserProfile, summary="내 프로필 조회")
async def get_me(current_user: User = Depends(get_current_user)):
    return UserProfile.model_validate(current_user)


@router.put("/me", response_model=UserProfile, summary="프로필 수정")
async def update_me(data: UpdateProfileRequest, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    updated = await auth_service.update_profile(db, current_user, data)
    return UserProfile.model_validate(updated)


@router.put("/me/password", response_model=MessageResponse, summary="비밀번호 변경")
async def change_password(data: ChangePasswordRequest, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    await auth_service.change_password(db, current_user, data)
    return MessageResponse(message="비밀번호가 변경되었습니다.")


@router.delete("/me", response_model=MessageResponse, status_code=status.HTTP_200_OK, summary="회원 탈퇴")
async def delete_me(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    await auth_service.deactivate_account(db, current_user)
    return MessageResponse(message="회원 탈퇴가 완료되었습니다.")

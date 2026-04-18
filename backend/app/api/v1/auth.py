"""
routers/auth.py
---------------
인증 관련 API 엔드포인트 9개

POST   /api/v1/auth/register        회원가입
POST   /api/v1/auth/login           로그인
POST   /api/v1/auth/logout          로그아웃
POST   /api/v1/auth/refresh         토큰 갱신
GET    /api/v1/auth/verify          토큰 유효성 확인
GET    /api/v1/auth/me              내 정보 조회
PUT    /api/v1/auth/me              내 정보 수정
PUT    /api/v1/auth/me/password     비밀번호 변경
DELETE /api/v1/auth/me              회원 탈퇴
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

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

router = APIRouter(prefix="/auth", tags=["인증"])


# ─────────────────────────────────────────────────────────
# 1. 회원가입
# ─────────────────────────────────────────────────────────
@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
    summary="회원가입",
    dependencies=[Depends(register_rate_limit)],  # 5분에 3회 제한
)
def register(
    data: RegisterRequest,
    db: Session = Depends(get_db),
):
    """
    이메일·비밀번호로 회원가입.
    성공 시 Access Token + Refresh Token 즉시 발급 (가입 후 바로 로그인 상태).
    """
    user, tokens = auth_service.register(db, data)
    return RegisterResponse(
        message="회원가입이 완료되었습니다.",
        user_id=user.id,
        tokens=TokenPair(**tokens),
    )


# ─────────────────────────────────────────────────────────
# 2. 로그인
# ─────────────────────────────────────────────────────────
@router.post(
    "/login",
    response_model=LoginResponse,
    summary="로그인",
    dependencies=[Depends(login_rate_limit)],  # 1분에 5회 제한
)
def login(
    data: LoginRequest,
    db: Session = Depends(get_db),
):
    user, tokens = auth_service.login(db, data)
    return LoginResponse(
        message="로그인 성공",
        tokens=TokenPair(**tokens),
        user=UserProfile.model_validate(user),
    )


# ─────────────────────────────────────────────────────────
# 3. 로그아웃
# ─────────────────────────────────────────────────────────
@router.post(
    "/logout",
    response_model=MessageResponse,
    summary="로그아웃",
)
def logout(
    _: User = Depends(get_current_user),  # 토큰 유효성만 검증
):
    """
    JWT는 서버에 저장되지 않으므로 서버 측 처리 없음.
    클라이언트가 로컬 스토리지의 토큰을 삭제하면 로그아웃 완료.
    (Refresh Token 블랙리스트는 Redis 연동 Phase에서 추가 예정)
    """
    return MessageResponse(message="로그아웃 되었습니다.")


# ─────────────────────────────────────────────────────────
# 4. 토큰 갱신
# ─────────────────────────────────────────────────────────
@router.post(
    "/refresh",
    response_model=RefreshResponse,
    summary="Access Token 갱신",
    dependencies=[Depends(refresh_rate_limit)],
)
def refresh(
    data: RefreshRequest,
    db: Session = Depends(get_db),
):
    """
    Refresh Token으로 새 Access Token 발급.
    Access Token이 만료(401)됐을 때 프론트엔드 axios interceptor가 자동 호출.
    """
    new_access_token = auth_service.refresh_access_token(db, data.refresh_token)
    return RefreshResponse(access_token=new_access_token)


# ─────────────────────────────────────────────────────────
# 5. 토큰 유효성 확인
# ─────────────────────────────────────────────────────────
@router.get(
    "/verify",
    response_model=MessageResponse,
    summary="토큰 유효성 확인",
)
def verify_token(
    _: User = Depends(get_current_user),
):
    """
    토큰이 유효하면 200, 만료/위변조면 401 자동 반환.
    프론트엔드 앱 시작 시 로그인 상태 확인에 사용.
    """
    return MessageResponse(message="유효한 토큰입니다.")


# ─────────────────────────────────────────────────────────
# 6. 내 정보 조회
# ─────────────────────────────────────────────────────────
@router.get(
    "/me",
    response_model=UserProfile,
    summary="내 프로필 조회",
)
def get_me(
    current_user: User = Depends(get_current_user),
):
    return UserProfile.model_validate(current_user)


# ─────────────────────────────────────────────────────────
# 7. 내 정보 수정
# ─────────────────────────────────────────────────────────
@router.put(
    "/me",
    response_model=UserProfile,
    summary="프로필 수정",
)
def update_me(
    data: UpdateProfileRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    updated = auth_service.update_profile(db, current_user, data)
    return UserProfile.model_validate(updated)


# ─────────────────────────────────────────────────────────
# 8. 비밀번호 변경
# ─────────────────────────────────────────────────────────
@router.put(
    "/me/password",
    response_model=MessageResponse,
    summary="비밀번호 변경",
)
def change_password(
    data: ChangePasswordRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    auth_service.change_password(db, current_user, data)
    return MessageResponse(message="비밀번호가 변경되었습니다.")


# ─────────────────────────────────────────────────────────
# 9. 회원 탈퇴
# ─────────────────────────────────────────────────────────
@router.delete(
    "/me",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="회원 탈퇴",
)
def delete_me(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    auth_service.deactivate_account(db, current_user)
    return MessageResponse(message="회원 탈퇴가 완료되었습니다.")

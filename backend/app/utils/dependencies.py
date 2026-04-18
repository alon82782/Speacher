"""
utils/dependencies.py
---------------------
FastAPI 의존성 주입(Dependency Injection) 모음

[의존성 주입이란?]
  API 함수가 실행되기 전에 "미리 처리해야 할 것들"을 자동으로 실행해주는 패턴.
  예: 토큰 검증 → 유저 조회를 매 API마다 반복 작성하지 않고
      Depends(get_current_user) 한 줄로 해결.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.utils.jwt import get_user_id_from_token
from app.models.user import User

# Authorization: Bearer <token> 헤더를 자동으로 파싱해주는 FastAPI 내장 클래스
bearer_scheme = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    """
    요청 헤더의 Bearer 토큰을 검증하고 현재 로그인 유저를 반환.

    사용 예:
        @router.get("/me")
        def get_me(current_user: User = Depends(get_current_user)):
            return current_user

    동작 흐름:
        1. Authorization: Bearer <token> 헤더 파싱
        2. JWT 서명 검증 + 만료 확인
        3. payload에서 user_id 추출
        4. DB에서 유저 조회
        5. 비활성 계정 차단
        6. User 객체 반환
    """
    # 1~3: 토큰 검증 + user_id 추출
    user_id = get_user_id_from_token(credentials.credentials)

    # 4: DB에서 유저 조회
    user = db.query(User).filter(User.id == user_id).first()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="존재하지 않는 사용자입니다.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 5: 탈퇴/비활성 계정 차단
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="비활성화된 계정입니다.",
        )

    return user


# 선택적 인증: 토큰이 없어도 에러 안 냄 (공개 + 로그인 혼합 페이지용)
def get_optional_user(
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials | None = Depends(
        HTTPBearer(auto_error=False)
    ),
) -> User | None:
    if credentials is None:
        return None
    try:
        user_id = get_user_id_from_token(credentials.credentials)
        return db.query(User).filter(User.id == user_id).first()
    except Exception:
        return None

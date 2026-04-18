"""
utils/jwt.py
------------
JWT(Access Token / Refresh Token) 생성·검증 유틸리티

[JWT란?]
  Header.Payload.Signature 형태의 암호화된 문자열.
  로그인 성공 시 서버가 발급 → 클라이언트가 저장 → 이후 요청마다 헤더에 첨부

[두 가지 토큰 전략]
  - Access Token  : 유효기간 짧음(60분). API 호출에 사용
  - Refresh Token : 유효기간 김(7일). Access Token 만료 시 재발급에만 사용
"""

from datetime import datetime, timedelta, timezone
from typing import Literal
import jwt
from fastapi import HTTPException, status
from app.config import settings


# ─────────────────────────────────────────────
# 토큰 타입
# ─────────────────────────────────────────────
TokenType = Literal["access", "refresh"]


def create_token(user_id: str, token_type: TokenType) -> str:
    """
    JWT 토큰 생성

    Args:
        user_id   : users.id (UUID 문자열)
        token_type: "access" | "refresh"

    Returns:
        서명된 JWT 문자열
    """
    now = datetime.now(timezone.utc)

    # 유효기간 설정
    if token_type == "access":
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    else:
        expire = now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    # Payload (토큰 안에 담길 정보)
    payload = {
        "sub": user_id,         # subject: 누구의 토큰인지
        "type": token_type,     # 토큰 종류 구분
        "iat": now,             # issued at: 발급 시각
        "exp": expire,          # expiration: 만료 시각
    }

    return jwt.encode(
        payload,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )


def decode_token(token: str, expected_type: TokenType) -> dict:
    """
    JWT 토큰 검증 및 디코딩

    Args:
        token        : 클라이언트가 보낸 JWT 문자열
        expected_type: 기대하는 토큰 타입 ("access" | "refresh")

    Returns:
        payload dict (sub, type, iat, exp)

    Raises:
        HTTPException 401: 만료됐거나 유효하지 않은 토큰
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="유효하지 않은 토큰입니다.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="토큰이 만료되었습니다.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError:
        raise credentials_exception

    # 토큰 타입 검증 (access 토큰으로 refresh 엔드포인트 접근 차단)
    if payload.get("type") != expected_type:
        raise credentials_exception

    return payload


def get_user_id_from_token(token: str) -> str:
    """Access Token에서 user_id(UUID) 추출"""
    payload = decode_token(token, "access")
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="토큰에서 사용자 정보를 찾을 수 없습니다.",
        )
    return user_id

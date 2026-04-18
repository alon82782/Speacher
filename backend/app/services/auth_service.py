"""
services/auth_service.py
------------------------
인증 관련 비즈니스 로직 모음

[서비스 레이어란?]
  라우터(API 엔드포인트)와 DB 사이에서 실제 비즈니스 로직을 처리하는 계층.
  라우터는 "요청 받기 + 응답 반환"만,
  서비스는 "실제 처리"를 담당 → 코드 재사용·테스트 용이
"""

import uuid
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

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

    # ─────────────────────────────────────────────────────
    # 회원가입
    # ─────────────────────────────────────────────────────
    def register(self, db: Session, data: RegisterRequest) -> tuple[User, dict]:
        """
        새 유저 생성 + 토큰 발급

        Returns:
            (User 객체, {"access_token": ..., "refresh_token": ...})
        """
        # 1. 이메일 중복 확인
        if db.query(User).filter(User.email == data.email).first():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="이미 사용 중인 이메일입니다.",
            )

        # 2. 유저 생성
        user = User(
            email=data.email,
            uname=data.name,
            hashed_password=hash_password(data.password),
            is_active=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)                    # DB에서 최신 상태로 갱신 (created_at 등)

        # 3. 토큰 발급
        tokens = self._issue_tokens(user.id)
        return user, tokens

    # ─────────────────────────────────────────────────────
    # 로그인
    # ─────────────────────────────────────────────────────
    def login(self, db: Session, data: LoginRequest) -> tuple[User, dict]:
        """
        이메일/비밀번호 검증 + 토큰 발급

        Returns:
            (User 객체, {"access_token": ..., "refresh_token": ...})
        """
        # 1. 유저 조회
        user = db.query(User).filter(User.email == data.email).first()

        # 2. 존재 여부 + 비밀번호 검증
        #    ⚠️ "이메일 없음"과 "비밀번호 틀림"을 같은 메시지로 응답
        #       (어느 쪽이 틀렸는지 공격자에게 힌트를 주지 않기 위해)
        if not user or not verify_password(data.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="이메일 또는 비밀번호가 올바르지 않습니다.",
            )

        # 3. 비활성 계정 차단
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="비활성화된 계정입니다.",
            )

        # 4. 토큰 발급
        tokens = self._issue_tokens(user.id)
        return user, tokens

    # ─────────────────────────────────────────────────────
    # 토큰 갱신
    # ─────────────────────────────────────────────────────
    def refresh_access_token(self, db: Session, refresh_token: str) -> str:
        """
        Refresh Token 검증 후 새 Access Token 발급

        Returns:
            새 access_token 문자열
        """
        # 1. Refresh Token 검증 (만료·위변조 확인)
        payload = decode_token(refresh_token, "refresh")
        user_id = payload.get("sub")

        # 2. 유저 존재·활성 여부 확인
        user = db.query(User).filter(User.id == user_id).first()
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="유효하지 않은 토큰입니다.",
            )

        # 3. 새 Access Token 발급 (Refresh Token은 그대로 유지)
        return create_token(user_id, "access")

    # ─────────────────────────────────────────────────────
    # 프로필 수정
    # ─────────────────────────────────────────────────────
    def update_profile(
        self, db: Session, user: User, data: UpdateProfileRequest
    ) -> User:
        if data.name is not None:
            user.name = data.name
        db.commit()
        db.refresh(user)
        return user

    # ─────────────────────────────────────────────────────
    # 비밀번호 변경
    # ─────────────────────────────────────────────────────
    def change_password(
        self, db: Session, user: User, data: ChangePasswordRequest
    ) -> None:
        # 현재 비밀번호 검증
        if not verify_password(data.current_password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="현재 비밀번호가 올바르지 않습니다.",
            )
        # 새 비밀번호로 교체
        user.hashed_password = hash_password(data.new_password)
        db.commit()

    # ─────────────────────────────────────────────────────
    # 회원 탈퇴 (소프트 삭제)
    # ─────────────────────────────────────────────────────
    def deactivate_account(self, db: Session, user: User) -> None:
        """
        실제 DB 삭제 대신 is_active=False로 비활성화.
        (분석 이력 보존 + 실수로 삭제 방지)
        """
        user.is_active = False
        db.commit()

    # ─────────────────────────────────────────────────────
    # 내부 헬퍼
    # ─────────────────────────────────────────────────────
    def _issue_tokens(self, user_id: str) -> dict:
        return {
            "access_token": create_token(user_id, "access"),
            "refresh_token": create_token(user_id, "refresh"),
        }


# 싱글톤 인스턴스 (모듈 임포트 시 한 번만 생성)
auth_service = AuthService()

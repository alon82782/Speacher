"""
utils/password.py
-----------------
bcrypt를 사용한 비밀번호 해싱·검증

[bcrypt란?]
  비밀번호를 DB에 그대로 저장하면 해킹 시 모두 노출됨.
  bcrypt는 비밀번호를 "복호화 불가능한 해시값"으로 변환해 저장.
  검증 시엔 입력값을 같은 방식으로 해싱해서 해시끼리 비교.

[work_factor(rounds)]
  12 = 해싱 시 2^12(4096)번 반복 → 무차별 대입 공격 속도 늦춤
  숫자가 클수록 안전하지만 느림. 12가 현재(2025) 일반적 권장값.
"""

import bcrypt


def hash_password(plain_password: str) -> str:
    """
    평문 비밀번호 → bcrypt 해시 문자열

    Args:
        plain_password: 사용자가 입력한 평문 비밀번호

    Returns:
        "$2b$12$..." 형태의 해시 문자열 (DB에 이 값을 저장)
    """
    password_bytes = plain_password.encode("utf-8")
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    평문 비밀번호와 해시값 비교

    Args:
        plain_password  : 로그인 시 사용자가 입력한 비밀번호
        hashed_password : DB에 저장된 해시값

    Returns:
        True  = 일치 (로그인 허용)
        False = 불일치 (로그인 거부)
    """
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8"),
    )

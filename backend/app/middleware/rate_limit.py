"""
middleware/rate_limit.py
------------------------
Rate Limiting: 짧은 시간 안에 너무 많은 요청을 차단

[왜 필요한가?]
  로그인 API에 비밀번호를 초당 수천 번 시도하는 공격(Brute Force Attack)을 방지.
  Redis 없이 메모리(dict)로 구현 → 서버 재시작 시 초기화됨 (캡스톤용으로 충분)
  운영 환경에선 Redis 기반 slowapi 사용 권장.

[동작 방식]
  IP + 경로별로 요청 횟수와 첫 요청 시각을 기록.
  window_seconds 안에 max_requests를 초과하면 429 Too Many Requests 응답.
"""

import time
from collections import defaultdict
from fastapi import Request, HTTPException, status


# IP별 요청 기록: { "ip:path": [타임스탬프1, 타임스탬프2, ...] }
_request_log: dict[str, list[float]] = defaultdict(list)


def rate_limit(max_requests: int = 5, window_seconds: int = 60):
    """
    Rate Limit 의존성 팩토리

    Args:
        max_requests   : 윈도우 내 최대 허용 요청 수 (기본 5회)
        window_seconds : 시간 윈도우 (기본 60초)

    사용 예:
        @router.post("/login", dependencies=[Depends(rate_limit(5, 60))])
        def login(...):
            ...
    """
    async def _check(request: Request):
        # 클라이언트 IP 추출 (Nginx 프록시 뒤에 있을 경우 X-Forwarded-For 사용)
        forwarded_for = request.headers.get("X-Forwarded-For")
        ip = forwarded_for.split(",")[0].strip() if forwarded_for else request.client.host

        key = f"{ip}:{request.url.path}"
        now = time.time()
        window_start = now - window_seconds

        # 오래된 기록 제거 (윈도우 밖의 타임스탬프)
        _request_log[key] = [t for t in _request_log[key] if t > window_start]

        # 현재 요청 횟수 확인
        if len(_request_log[key]) >= max_requests:
            retry_after = int(window_seconds - (now - _request_log[key][0]))
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"요청이 너무 많습니다. {retry_after}초 후 다시 시도하세요.",
                headers={"Retry-After": str(retry_after)},
            )

        # 현재 요청 기록
        _request_log[key].append(now)

    return _check


# ─────────────────────────────────────────────────────────
# 사전 정의된 리밋 (각 API에서 바로 사용)
# ─────────────────────────────────────────────────────────
login_rate_limit    = rate_limit(max_requests=5,  window_seconds=60)   # 1분에 5회
register_rate_limit = rate_limit(max_requests=3,  window_seconds=300)  # 5분에 3회
refresh_rate_limit  = rate_limit(max_requests=10, window_seconds=60)   # 1분에 10회

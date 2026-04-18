"""
middleware/error_handler.py
---------------------------
전역 에러를 일관된 JSON 형식으로 반환하는 핸들러

[왜 필요한가?]
  FastAPI 기본 에러 형식:  {"detail": "..."}
  Pydantic 검증 에러 형식: {"detail": [{"loc": [...], "msg": "..."}]}
  
  프론트엔드가 에러를 일관되게 처리할 수 있도록
  모든 에러를 동일한 형식으로 통일합니다:
  {
    "success": false,
    "error": {
      "code": "VALIDATION_ERROR",
      "message": "...",
      "details": [...]
    }
  }
"""

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException


def register_error_handlers(app: FastAPI) -> None:
    """main.py의 app에 에러 핸들러 등록"""

    # ── HTTP 에러 (404, 401, 403, 409 등) ────────────────────────
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "error": {
                    "code": _status_to_code(exc.status_code),
                    "message": exc.detail,
                },
            },
        )

    # ── Pydantic 검증 에러 (422: 요청 바디 형식 오류) ─────────────
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        # 여러 필드 에러를 하나의 메시지로 합치기
        messages = []
        for error in exc.errors():
            field = " → ".join(str(loc) for loc in error["loc"] if loc != "body")
            messages.append(f"{field}: {error['msg']}" if field else error["msg"])

        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "success": False,
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": messages[0] if len(messages) == 1 else "입력값을 확인해주세요.",
                    "details": messages,
                },
            },
        )

    # ── 예상치 못한 서버 에러 (500) ───────────────────────────────
    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        # 운영환경에서는 로깅 시스템(Sentry 등)으로 전송
        import traceback
        traceback.print_exc()  # 개발 중엔 콘솔 출력

        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "error": {
                    "code": "INTERNAL_SERVER_ERROR",
                    "message": "서버 내부 오류가 발생했습니다.",
                },
            },
        )


def _status_to_code(status_code: int) -> str:
    """HTTP 상태코드 → 에러 코드 문자열 변환"""
    mapping = {
        400: "BAD_REQUEST",
        401: "UNAUTHORIZED",
        403: "FORBIDDEN",
        404: "NOT_FOUND",
        409: "CONFLICT",
        422: "VALIDATION_ERROR",
        429: "TOO_MANY_REQUESTS",
        500: "INTERNAL_SERVER_ERROR",
    }
    return mapping.get(status_code, f"HTTP_{status_code}")

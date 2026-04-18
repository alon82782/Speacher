from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from app.utils.logger import logger


class SpeacherException(Exception):
    def __init__(self, message: str, status_code: int = 500, error_code: str = "INTERNAL_ERROR"):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        super().__init__(message)

class AuthException(SpeacherException):
    def __init__(self, message: str = "인증에 실패했습니다.", error_code: str = "AUTH_ERROR"):
        super().__init__(message, status.HTTP_401_UNAUTHORIZED, error_code)

class ForbiddenException(SpeacherException):
    def __init__(self, message: str = "접근 권한이 없습니다."):
        super().__init__(message, status.HTTP_403_FORBIDDEN, "FORBIDDEN")

class NotFoundException(SpeacherException):
    def __init__(self, resource: str = "리소스"):
        super().__init__(f"{resource}을(를) 찾을 수 없습니다.", status.HTTP_404_NOT_FOUND, "NOT_FOUND")

class ConflictException(SpeacherException):
    def __init__(self, message: str = "이미 존재하는 리소스입니다."):
        super().__init__(message, status.HTTP_409_CONFLICT, "CONFLICT")

class ValidationException(SpeacherException):
    def __init__(self, message: str):
        super().__init__(message, status.HTTP_422_UNPROCESSABLE_ENTITY, "VALIDATION_ERROR")

class FileException(SpeacherException):
    def __init__(self, message: str, error_code: str = "FILE_ERROR"):
        super().__init__(message, status.HTTP_400_BAD_REQUEST, error_code)


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(SpeacherException)
    async def speacher_handler(request: Request, exc: SpeacherException):
        logger.warning(f"[{exc.error_code}] {exc.message}")
        return JSONResponse(
            status_code=exc.status_code,
            content={"success": False, "error": {"code": exc.error_code, "message": exc.message}}
        )

    @app.exception_handler(Exception)
    async def unhandled_handler(request: Request, exc: Exception):
        logger.error(f"[UNHANDLED] {type(exc).__name__}: {exc}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": {"code": "INTERNAL_ERROR", "message": "서버 내부 오류가 발생했습니다."}}
        )

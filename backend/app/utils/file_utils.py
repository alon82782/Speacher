"""
app/utils/file_utils.py
파일 업로드 유효성 검사 및 저장 유틸리티
"""
import os
import uuid
import aiofiles
from fastapi import UploadFile
from app.config import settings
from app.core.exceptions import FileException


ALLOWED_EXTENSIONS = {"mp4", "mov", "avi", "webm"}
ALLOWED_MIME_TYPES = {
    "video/mp4", "video/quicktime",
    "video/x-msvideo", "video/webm"
}


def get_extension(filename: str) -> str:
    return filename.rsplit(".", 1)[-1].lower() if "." in filename else ""


def validate_video_file(file: UploadFile) -> None:
    """파일 확장자 + MIME 타입 + 크기 검사"""
    ext = get_extension(file.filename or "")
    if ext not in ALLOWED_EXTENSIONS:
        raise FileException(
            f"지원하지 않는 파일 형식입니다. (허용: {', '.join(ALLOWED_EXTENSIONS)})",
            error_code="INVALID_FILE_TYPE"
        )
    if file.content_type and file.content_type not in ALLOWED_MIME_TYPES:
        raise FileException(
            "올바른 동영상 파일이 아닙니다.",
            error_code="INVALID_MIME_TYPE"
        )


async def save_upload_file(file: UploadFile, job_id: str) -> tuple[str, int]:
    """
    업로드 파일을 임시 디렉토리에 저장

    Returns:
        (저장된 파일 경로, 파일 크기 bytes)
    """
    ext = get_extension(file.filename or "mp4")
    dir_path = os.path.join(settings.TEMP_UPLOAD_DIR, job_id)
    os.makedirs(dir_path, exist_ok=True)
    file_path = os.path.join(dir_path, f"video.{ext}")

    total_size = 0
    async with aiofiles.open(file_path, "wb") as out_file:
        while chunk := await file.read(1024 * 1024):  # 1MB씩 읽기
            total_size += len(chunk)
            if total_size > settings.max_file_size_bytes:
                await out_file.close()
                os.remove(file_path)
                raise FileException(
                    f"파일 크기가 {settings.MAX_FILE_SIZE_MB}MB를 초과합니다.",
                    error_code="FILE_TOO_LARGE"
                )
            await out_file.write(chunk)

    return file_path, total_size


def cleanup_job_files(job_id: str) -> None:
    """Job 관련 임시 파일 삭제"""
    import shutil
    dir_path = os.path.join(settings.TEMP_UPLOAD_DIR, job_id)
    if os.path.exists(dir_path):
        shutil.rmtree(dir_path, ignore_errors=True)

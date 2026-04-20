"""
app/services/analysis_service.py
분석 비즈니스 로직
"""
import uuid
from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

import app.crud.analysis as crud
from app.models.analysis_job import AnalysisJob, JobStatus
from app.models.user import User
from app.utils.file_utils import validate_video_file, save_upload_file, cleanup_job_files
from app.core.exceptions import NotFoundException, ForbiddenException, ValidationException
from app.utils.logger import logger


class AnalysisService:

    # ── 파일 사전 검증 ────────────────────────────────────────────────────────
    async def validate_file(self, file: UploadFile) -> dict:
        """업로드 전 파일 유효성 검사만 수행 (저장 없음)"""
        validate_video_file(file)
        return {"valid": True, "filename": file.filename, "content_type": file.content_type}

    # ── 분석 시작 ─────────────────────────────────────────────────────────────
    async def start_analysis(
        self,
        db: AsyncSession,
        user: User,
        file: UploadFile,
        title: str = "",
        target_duration_sec: float | None = None,
    ) -> AnalysisJob:
        """
        1. 파일 유효성 검사
        2. 임시 저장
        3. Job 생성
        4. Celery 태스크 발송 (Phase 5에서 연결)
        """
        # 1. 유효성 검사
        validate_video_file(file)

        # 2. Job UUID 생성 + 파일 저장
        job_uuid = str(uuid.uuid4())
        file_title = title.strip() or file.filename or "발표 영상"

        try:
            file_path, file_size = await save_upload_file(file, job_uuid)
        except Exception as e:
            logger.error(f"파일 저장 실패: {e}")
            raise

        # 3. DB에 Job 생성
        job = await crud.create_job(
            db=db,
            user_id=user.id,
            job_uuid=job_uuid,
            title=file_title,
            original_filename=file.filename or "video",
            file_path=file_path,
            file_size_bytes=file_size,
            target_duration_sec=target_duration_sec,
        )

        logger.info(f"[Job 생성] job_uuid={job_uuid} user_id={user.id}")

        # 4. Celery 태스크 발송 (Phase 5에서 활성화)
        # from app.tasks.analysis_task import run_analysis
        # task = run_analysis.delay(
        #     job_id=job_uuid,
        #     file_path=file_path,
        #     user_id=user.id,
        #     meta={"title": file_title, "target_duration_sec": target_duration_sec},
        # )
        # await crud.update_job_status(db, job, JobStatus.PROCESSING, celery_task_id=task.id)

        return job

    # ── Job 조회 (권한 검증 포함) ──────────────────────────────────────────────
    async def get_job(self, db: AsyncSession, job_uuid: str, user_id: int) -> AnalysisJob:
        job = await crud.get_job_by_uuid_and_user(db, job_uuid, user_id)
        if not job:
            raise NotFoundException("분석 Job")
        return job

    # ── 분석 재시도 ───────────────────────────────────────────────────────────
    async def retry_analysis(self, db: AsyncSession, job_uuid: str, user: User) -> AnalysisJob:
        job = await self.get_job(db, job_uuid, user.id)
        if job.status != JobStatus.FAILED:
            raise ValidationException("실패한 분석만 재시도할 수 있습니다.")
        job = await crud.update_job_status(db, job, JobStatus.PENDING, current_step=0, step_progress=0, error_message=None)
        logger.info(f"[Job 재시도] job_uuid={job_uuid}")
        return job

    # ── 분석 삭제 ─────────────────────────────────────────────────────────────
    async def delete_analysis(self, db: AsyncSession, job_uuid: str, user: User) -> None:
        job = await self.get_job(db, job_uuid, user.id)
        cleanup_job_files(job_uuid)
        await crud.delete_job(db, job)
        logger.info(f"[Job 삭제] job_uuid={job_uuid}")

    # ── 이력 목록 ─────────────────────────────────────────────────────────────
    async def get_history(
        self, db: AsyncSession, user_id: int, page: int = 1, size: int = 10
    ) -> dict:
        jobs, total = await crud.get_job_history(db, user_id, page, size)
        return {
            "items": jobs,
            "total": total,
            "page": page,
            "size": size,
            "has_next": (page * size) < total,
        }

    # ── 대시보드 통계 ─────────────────────────────────────────────────────────
    async def get_stats(self, db: AsyncSession, user_id: int) -> dict:
        return await crud.get_user_stats(db, user_id)


analysis_service = AnalysisService()

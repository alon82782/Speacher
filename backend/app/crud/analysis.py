"""
app/crud/analysis.py
분석 Job DB CRUD 함수
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from sqlalchemy.orm import selectinload

from app.models.analysis_job import AnalysisJob, JobStatus
from app.models.analysis_result import AnalysisResult
from app.models.timeline_event import TimelineEvent


# ── Job 생성 ──────────────────────────────────────────────────────────────────
async def create_job(
    db: AsyncSession,
    user_id: int,
    job_uuid: str,
    title: str,
    original_filename: str,
    file_path: str,
    file_size_bytes: int,
    target_duration_sec: float | None = None,
) -> AnalysisJob:
    job = AnalysisJob(
        job_uuid=job_uuid,
        user_id=user_id,
        title=title,
        original_filename=original_filename,
        file_path=file_path,
        file_size_bytes=file_size_bytes,
        target_duration_sec=target_duration_sec,
        status=JobStatus.PENDING,
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)
    return job


# ── Job 조회 (UUID로) ──────────────────────────────────────────────────────────
async def get_job_by_uuid(db: AsyncSession, job_uuid: str) -> AnalysisJob | None:
    result = await db.execute(
        select(AnalysisJob).where(AnalysisJob.job_uuid == job_uuid)
    )
    return result.scalar_one_or_none()


# ── Job 조회 (UUID + 유저 검증) ────────────────────────────────────────────────
async def get_job_by_uuid_and_user(
    db: AsyncSession, job_uuid: str, user_id: int
) -> AnalysisJob | None:
    result = await db.execute(
        select(AnalysisJob).where(
            AnalysisJob.job_uuid == job_uuid,
            AnalysisJob.user_id == user_id,
        )
    )
    return result.scalar_one_or_none()


# ── Job 상태 업데이트 ──────────────────────────────────────────────────────────
async def update_job_status(
    db: AsyncSession,
    job: AnalysisJob,
    status: JobStatus,
    current_step: int = None,
    step_progress: int = None,
    error_message: str = None,
    celery_task_id: str = None,
) -> AnalysisJob:
    job.status = status
    if current_step is not None:
        job.current_step = current_step
    if step_progress is not None:
        job.step_progress = step_progress
    if error_message is not None:
        job.error_message = error_message
    if celery_task_id is not None:
        job.celery_task_id = celery_task_id
    await db.commit()
    await db.refresh(job)
    return job


# ── Job 삭제 ──────────────────────────────────────────────────────────────────
async def delete_job(db: AsyncSession, job: AnalysisJob) -> None:
    await db.delete(job)
    await db.commit()


# ── 이력 목록 조회 (페이지네이션) ─────────────────────────────────────────────
async def get_job_history(
    db: AsyncSession,
    user_id: int,
    page: int = 1,
    size: int = 10,
) -> tuple[list[AnalysisJob], int]:
    offset = (page - 1) * size

    # 전체 개수
    count_result = await db.execute(
        select(func.count()).where(AnalysisJob.user_id == user_id)
    )
    total = count_result.scalar_one()

    # 목록
    result = await db.execute(
        select(AnalysisJob)
        .where(AnalysisJob.user_id == user_id)
        .order_by(desc(AnalysisJob.created_at))
        .offset(offset)
        .limit(size)
        .options(selectinload(AnalysisJob.result))
    )
    jobs = result.scalars().all()
    return list(jobs), total


# ── 대시보드 통계 조회 ─────────────────────────────────────────────────────────
async def get_user_stats(db: AsyncSession, user_id: int) -> dict:
    # 총 분석 횟수
    count_result = await db.execute(
        select(func.count()).select_from(AnalysisJob).where(
            AnalysisJob.user_id == user_id,
            AnalysisJob.status == JobStatus.COMPLETED,
        )
    )
    total = count_result.scalar_one()

    if total == 0:
        return {
            "total_analyses": 0,
            "average_score": None,
            "best_score": None,
            "recent_scores": [],
            "score_by_metric": {},
        }

    # 평균/최고 점수
    score_result = await db.execute(
        select(
            func.avg(AnalysisResult.total_score),
            func.max(AnalysisResult.total_score),
        )
        .join(AnalysisJob, AnalysisJob.id == AnalysisResult.job_id)
        .where(AnalysisJob.user_id == user_id)
    )
    avg_score, best_score = score_result.one()

    # 최근 10개 점수 추이
    recent_result = await db.execute(
        select(AnalysisJob.created_at, AnalysisResult.total_score)
        .join(AnalysisResult, AnalysisResult.job_id == AnalysisJob.id)
        .where(AnalysisJob.user_id == user_id)
        .order_by(desc(AnalysisJob.created_at))
        .limit(10)
    )
    recent_rows = recent_result.all()
    recent_scores = [
        {"date": str(row.created_at.date()), "score": round(row.total_score, 1)}
        for row in reversed(recent_rows)
    ]

    # 지표별 평균 점수
    metric_result = await db.execute(
        select(
            func.avg(AnalysisResult.gaze_score),
            func.avg(AnalysisResult.posture_score),
            func.avg(AnalysisResult.speech_rate_score),
            func.avg(AnalysisResult.volume_pitch_score),
            func.avg(AnalysisResult.filler_word_score),
            func.avg(AnalysisResult.pronunciation_score),
            func.avg(AnalysisResult.time_score),
        )
        .join(AnalysisJob, AnalysisJob.id == AnalysisResult.job_id)
        .where(AnalysisJob.user_id == user_id)
    )
    m = metric_result.one()
    score_by_metric = {
        "gaze": round(m[0] or 0, 1),
        "posture": round(m[1] or 0, 1),
        "speech_rate": round(m[2] or 0, 1),
        "volume_pitch": round(m[3] or 0, 1),
        "filler_word": round(m[4] or 0, 1),
        "pronunciation": round(m[5] or 0, 1),
        "time_compliance": round(m[6] or 0, 1),
    }

    return {
        "total_analyses": total,
        "average_score": round(avg_score or 0, 1),
        "best_score": round(best_score or 0, 1),
        "recent_scores": recent_scores,
        "score_by_metric": score_by_metric,
    }

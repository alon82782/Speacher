"""분석 파이프라인 Celery 태스크.

흐름: PENDING → PROCESSING (단계별 진행률 갱신) → COMPLETED / FAILED
동기 Celery worker 안에서 async DB 호출은 asyncio.run으로 감싸 처리.
"""
import asyncio
from pathlib import Path

from celery import shared_task

import app.crud.analysis as crud
from app.db.session import AsyncSessionLocal
from app.models.analysis_job import JobStatus
from app.models.analysis_result import AnalysisResult
from app.models.timeline_event import EventType, TimelineEvent
from app.services.analysis.context import PipelineContext
from app.services.analysis.pipeline import PipelineError, run_pipeline
from app.services.analysis.scoring import ScoringOutput
from app.utils.logger import logger


@shared_task(
    bind=True,
    name="app.tasks.analysis_task.run_analysis",
    max_retries=2,
    default_retry_delay=30,
)
def run_analysis(self, job_uuid: str, file_path: str, user_id: int, meta: dict):
    """분석 파이프라인 진입점."""
    logger.info(f"[Analysis Start] job_uuid={job_uuid}")

    def _on_progress(step: int, percent: int) -> None:
        # 단계 진행률 콜백 — pipeline orchestrator가 단계 시작/끝마다 호출
        try:
            asyncio.run(_persist_progress(job_uuid, step, percent))
        except Exception as e:
            logger.warning(f"[Analysis Progress] DB 갱신 실패 (무시): {e}")

    ctx = PipelineContext(
        job_uuid=job_uuid,
        file_path=Path(file_path),
        user_id=user_id,
        target_duration_sec=meta.get("target_duration_sec"),
        update_progress=_on_progress,
    )

    try:
        scoring = run_pipeline(ctx)
    except PipelineError as exc:
        logger.error(f"[Analysis Failed] job_uuid={job_uuid}: {exc}")
        asyncio.run(_persist_failure(job_uuid, str(exc)))
        try:
            raise self.retry(exc=exc)
        except self.MaxRetriesExceededError:
            return
    except NotImplementedError as exc:
        # 단계·환산 미구현 — 재시도해도 동일하므로 즉시 FAILED 처리
        logger.error(f"[Analysis NotImplemented] job_uuid={job_uuid}: {exc}")
        asyncio.run(_persist_failure(job_uuid, f"미구현: {exc}"))
        return
    except Exception as exc:
        logger.exception(f"[Analysis Crashed] job_uuid={job_uuid}")
        asyncio.run(_persist_failure(job_uuid, f"예상치 못한 오류: {exc}"))
        return

    asyncio.run(_persist_result(job_uuid, scoring))
    logger.info(f"[Analysis Complete] job_uuid={job_uuid}")


# ── DB 영속화 헬퍼 (async) ────────────────────────────────────────────────────

async def _persist_progress(job_uuid: str, step: int, percent: int) -> None:
    async with AsyncSessionLocal() as db:
        job = await crud.get_job_by_uuid(db, job_uuid)
        if job is None:
            return
        await crud.update_job_status(
            db, job, JobStatus.PROCESSING,
            current_step=step, step_progress=percent,
        )


async def _persist_failure(job_uuid: str, error_message: str) -> None:
    async with AsyncSessionLocal() as db:
        job = await crud.get_job_by_uuid(db, job_uuid)
        if job is None:
            return
        await crud.update_job_status(
            db, job, JobStatus.FAILED,
            error_message=error_message,
        )


async def _persist_result(job_uuid: str, scoring: ScoringOutput) -> None:
    async with AsyncSessionLocal() as db:
        job = await crud.get_job_by_uuid(db, job_uuid)
        if job is None:
            logger.warning(f"[Analysis Result] job_uuid={job_uuid} 찾을 수 없음")
            return

        db.add(AnalysisResult(
            job_id=job.id,
            total_score=scoring.total_score,
            gaze_score=scoring.gaze_score,
            posture_score=scoring.posture_score,
            speech_rate_score=scoring.speech_rate_score,
            volume_pitch_score=scoring.volume_pitch_score,
            filler_word_score=scoring.filler_word_score,
            pronunciation_score=scoring.pronunciation_score,
            time_score=scoring.time_score,
            visual_score=scoring.visual_score,
            audio_score=scoring.audio_score,
            vocab_score=scoring.vocab_score,
            delivery_score=scoring.delivery_score,
            raw_metrics=scoring.raw_metrics,
            feedback_summary=scoring.feedback_summary,
            feedback_strengths=scoring.feedback_strengths,
            feedback_improvements=scoring.feedback_improvements,
            feedback_details=scoring.feedback_details,
            calibration_data=scoring.calibration_data,
        ))

        for entry in scoring.timeline:
            db.add(TimelineEvent(
                job_id=job.id,
                event_type=EventType(entry.event_type),
                timestamp_sec=entry.timestamp_sec,
                end_timestamp_sec=entry.end_timestamp_sec,
                severity=entry.severity,
                description=entry.description,
                extra_data=entry.extra_data,
            ))

        # update_job_status가 commit하면서 위 add들도 함께 영속화
        await crud.update_job_status(
            db, job, JobStatus.COMPLETED,
            current_step=7, step_progress=100,
        )

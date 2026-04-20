"""
app/api/v1/analysis.py
분석 API 라우터 (Phase 4 구현)
"""
from fastapi import APIRouter, Depends, UploadFile, File, Form, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.user import User
from app.models.analysis_job import JobStatus
from app.schemas.analysis import (
    JobCreatedResponse,
    JobStatusResponse,
    HistoryResponse,
    HistoryItem,
    StatsResponse,
)
from app.schemas.common import SuccessResponse
from app.services.analysis_service import analysis_service
from app.utils.dependencies import get_current_user
from app.core.exceptions import NotFoundException

router = APIRouter(tags=["Analysis"])


# ── 파일 사전 검증 ────────────────────────────────────────────────────────────
@router.post("/validate", summary="파일 사전 검증")
async def validate_file(
    file: UploadFile = File(...),
    _: User = Depends(get_current_user),
):
    result = await analysis_service.validate_file(file)
    return SuccessResponse(data=result, message="유효한 파일입니다.")


# ── 분석 시작 (파일 업로드) ───────────────────────────────────────────────────
@router.post("", summary="영상 업로드 및 분석 시작")
async def start_analysis(
    file: UploadFile = File(...),
    title: str = Form(default=""),
    target_duration_sec: float | None = Form(default=None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    job = await analysis_service.start_analysis(
        db=db,
        user=current_user,
        file=file,
        title=title,
        target_duration_sec=target_duration_sec,
    )
    return SuccessResponse(
        data=JobCreatedResponse(job_id=job.job_uuid, status=job.status),
        message="분석이 시작되었습니다.",
    )


# ── 분석 상태 조회 ────────────────────────────────────────────────────────────
@router.get("/{job_id}/status", summary="분석 진행 상태 조회")
async def get_analysis_status(
    job_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    job = await analysis_service.get_job(db, job_id, current_user.id)
    return SuccessResponse(
        data=JobStatusResponse(
            job_id=job.job_uuid,
            status=job.status,
            current_step=job.current_step,
            step_progress=job.step_progress,
            error_message=job.error_message,
        )
    )


# ── 분석 결과 조회 ────────────────────────────────────────────────────────────
@router.get("/{job_id}/result", summary="분석 결과 조회")
async def get_analysis_result(
    job_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    job = await analysis_service.get_job(db, job_id, current_user.id)
    if job.status != JobStatus.COMPLETED or not job.result:
        raise NotFoundException("분석 결과")
    r = job.result
    return SuccessResponse(data={
        "job_id": job.job_uuid,
        "title": job.title,
        "total_score": r.total_score,
        "scores": {
            "gaze": r.gaze_score,
            "posture": r.posture_score,
            "speech_rate": r.speech_rate_score,
            "volume_pitch": r.volume_pitch_score,
            "filler_word": r.filler_word_score,
            "pronunciation": r.pronunciation_score,
            "time_compliance": r.time_score,
        },
        "channel_scores": {
            "visual": r.visual_score,
            "audio": r.audio_score,
            "vocab": r.vocab_score,
            "delivery": r.delivery_score,
        },
        "raw_metrics": r.raw_metrics,
        "video_duration_sec": job.video_duration_sec,
        "created_at": job.created_at,
    })


# ── 타임라인 조회 ─────────────────────────────────────────────────────────────
@router.get("/{job_id}/timeline", summary="타임라인 이벤트 조회")
async def get_analysis_timeline(
    job_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    job = await analysis_service.get_job(db, job_id, current_user.id)
    events = job.timeline_events or []
    return SuccessResponse(data={
        "job_id": job.job_uuid,
        "events": [
            {
                "id": e.id,
                "event_type": e.event_type,
                "timestamp_sec": e.timestamp_sec,
                "end_timestamp_sec": e.end_timestamp_sec,
                "severity": e.severity,
                "description": e.description,
                "extra_data": e.extra_data,
            }
            for e in events
        ],
        "total": len(events),
    })


# ── GPT 피드백 조회 ───────────────────────────────────────────────────────────
@router.get("/{job_id}/feedback", summary="GPT 피드백 조회")
async def get_analysis_feedback(
    job_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    job = await analysis_service.get_job(db, job_id, current_user.id)
    if not job.result:
        raise NotFoundException("피드백")
    r = job.result
    return SuccessResponse(data={
        "job_id": job.job_uuid,
        "summary": r.feedback_summary,
        "strengths": r.feedback_strengths,
        "improvements": r.feedback_improvements,
        "details": r.feedback_details,
    })


# ── 분석 재시도 ───────────────────────────────────────────────────────────────
@router.post("/{job_id}/retry", summary="분석 재시도")
async def retry_analysis(
    job_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    job = await analysis_service.retry_analysis(db, job_id, current_user)
    return SuccessResponse(
        data=JobCreatedResponse(job_id=job.job_uuid, status=job.status),
        message="분석 재시도가 시작되었습니다.",
    )


# ── 분석 이력 목록 ────────────────────────────────────────────────────────────
@router.get("/history", summary="분석 이력 목록")
async def get_history(
    page: int = Query(default=1, ge=1),
    size: int = Query(default=10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await analysis_service.get_history(db, current_user.id, page, size)
    items = [
        {
            "job_id": job.job_uuid,
            "title": job.title,
            "status": job.status,
            "total_score": job.result.total_score if job.result else None,
            "video_duration_sec": job.video_duration_sec,
            "created_at": job.created_at,
        }
        for job in result["items"]
    ]
    return SuccessResponse(data={
        "items": items,
        "total": result["total"],
        "page": result["page"],
        "size": result["size"],
        "has_next": result["has_next"],
    })


# ── 대시보드 통계 ─────────────────────────────────────────────────────────────
@router.get("/stats", summary="대시보드 통계")
async def get_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stats = await analysis_service.get_stats(db, current_user.id)
    return SuccessResponse(data=stats)


# ── 분석 삭제 ─────────────────────────────────────────────────────────────────
@router.delete("/{job_id}", summary="분석 기록 삭제")
async def delete_analysis(
    job_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await analysis_service.delete_analysis(db, job_id, current_user)
    return SuccessResponse(message="삭제되었습니다.")

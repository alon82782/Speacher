from datetime import datetime
from typing import Any
from pydantic import BaseModel, Field
from app.models.analysis_job import JobStatus
from app.models.timeline_event import EventType


class JobCreatedResponse(BaseModel):
    job_id: str
    status: JobStatus


class JobStatusResponse(BaseModel):
    job_id: str
    status: JobStatus
    current_step: int
    step_progress: int
    error_message: str | None = None


class ScoreBreakdown(BaseModel):
    gaze: float
    posture: float
    speech_rate: float
    volume_pitch: float
    filler_word: float
    pronunciation: float
    time_compliance: float


class ChannelScores(BaseModel):
    visual: float
    audio: float
    vocab: float
    delivery: float


class AnalysisResultResponse(BaseModel):
    job_id: str
    title: str
    total_score: float
    scores: ScoreBreakdown
    channel_scores: ChannelScores
    raw_metrics: dict[str, Any] | None = None
    video_duration_sec: float | None = None
    created_at: datetime
    model_config = {"from_attributes": True}


class FeedbackResponse(BaseModel):
    job_id: str
    summary: str | None = None
    strengths: str | None = None
    improvements: str | None = None
    details: dict[str, str] | None = None


class TimelineEventResponse(BaseModel):
    id: int
    event_type: EventType
    timestamp_sec: float
    end_timestamp_sec: float | None = None
    severity: int
    description: str | None = None
    extra_data: dict[str, Any] | None = None
    model_config = {"from_attributes": True}


class TimelineResponse(BaseModel):
    job_id: str
    events: list[TimelineEventResponse]
    total: int


class HistoryItem(BaseModel):
    job_id: str
    title: str
    status: JobStatus
    total_score: float | None = None
    video_duration_sec: float | None = None
    created_at: datetime
    model_config = {"from_attributes": True}


class HistoryResponse(BaseModel):
    items: list[HistoryItem]
    total: int
    page: int
    size: int
    has_next: bool


class StatsResponse(BaseModel):
    total_analyses: int
    average_score: float | None
    best_score: float | None
    recent_scores: list[dict]
    score_by_metric: dict[str, float]

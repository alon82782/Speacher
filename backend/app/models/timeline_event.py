import enum
from sqlalchemy import BigInteger, Enum, Float, ForeignKey, Index, Integer, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, TimestampMixin


class EventType(str, enum.Enum):
    FILLER_WORD   = "filler_word"
    GAZE_MISS     = "gaze_miss"
    LOW_VOLUME    = "low_volume"
    FAST_SPEECH   = "fast_speech"
    SLOW_SPEECH   = "slow_speech"
    POSTURE_SWAY  = "posture_sway"
    PRONUNCIATION = "pronunciation"


class TimelineEvent(Base, TimestampMixin):
    __tablename__ = "timeline_events"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("analysis_jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    timestamp_sec: Mapped[float] = mapped_column(Float, nullable=False)
    end_timestamp_sec: Mapped[float | None] = mapped_column(Float, nullable=True)
    event_type: Mapped[EventType] = mapped_column(Enum(EventType), nullable=False, index=True)
    severity: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    extra_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    job: Mapped["AnalysisJob"] = relationship("AnalysisJob", back_populates="timeline_events")

    __table_args__ = (
        Index("ix_timeline_job_ts", "job_id", "timestamp_sec"),
        Index("ix_timeline_job_type", "job_id", "event_type"),
    )

    def __repr__(self) -> str:
        return f"<TimelineEvent job_id={self.job_id} type={self.event_type}>"

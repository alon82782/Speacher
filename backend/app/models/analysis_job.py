import enum
from sqlalchemy import BigInteger, Enum, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, TimestampMixin


class JobStatus(str, enum.Enum):
    PENDING    = "pending"
    PROCESSING = "processing"
    COMPLETED  = "completed"
    FAILED     = "failed"


class AnalysisJob(Base, TimestampMixin):
    __tablename__ = "analysis_jobs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    job_uuid: Mapped[str] = mapped_column(String(36), unique=True, nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    file_size_bytes: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    video_duration_sec: Mapped[float | None] = mapped_column(Float, nullable=True)
    target_duration_sec: Mapped[float | None] = mapped_column(Float, nullable=True)
    status: Mapped[JobStatus] = mapped_column(Enum(JobStatus), default=JobStatus.PENDING, nullable=False, index=True)
    current_step: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    step_progress: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    celery_task_id: Mapped[str | None] = mapped_column(String(255), nullable=True)

    user: Mapped["User"] = relationship("User", back_populates="analysis_jobs")
    result: Mapped["AnalysisResult | None"] = relationship(
        "AnalysisResult", back_populates="job", cascade="all, delete-orphan", uselist=False
    )
    timeline_events: Mapped[list["TimelineEvent"]] = relationship(
        "TimelineEvent", back_populates="job", cascade="all, delete-orphan",
        order_by="TimelineEvent.timestamp_sec"
    )

    __table_args__ = (
        Index("ix_jobs_user_created", "user_id", "created_at"),
        Index("ix_jobs_user_status", "user_id", "status"),
    )

    def __repr__(self) -> str:
        return f"<AnalysisJob uuid={self.job_uuid} status={self.status}>"

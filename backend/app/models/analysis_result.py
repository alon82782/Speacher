from sqlalchemy import BigInteger, Float, ForeignKey, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, TimestampMixin


class AnalysisResult(Base, TimestampMixin):
    __tablename__ = "analysis_results"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("analysis_jobs.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)

    total_score: Mapped[float] = mapped_column(Float, nullable=False)
    gaze_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    posture_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    speech_rate_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    volume_pitch_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    filler_word_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    pronunciation_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    time_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    visual_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    audio_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    vocab_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    delivery_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    raw_metrics: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    feedback_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    feedback_strengths: Mapped[str | None] = mapped_column(Text, nullable=True)
    feedback_improvements: Mapped[str | None] = mapped_column(Text, nullable=True)
    feedback_details: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    calibration_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    job: Mapped["AnalysisJob"] = relationship("AnalysisJob", back_populates="result")

    def __repr__(self) -> str:
        return f"<AnalysisResult job_id={self.job_id} total={self.total_score}>"

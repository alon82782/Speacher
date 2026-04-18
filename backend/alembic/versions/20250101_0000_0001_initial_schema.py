"""initial schema

Revision ID: 0001
Revises: 
Create Date: 2025-01-01 00:00:00
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("name", sa.String(50), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="1"),
        sa.Column("refresh_token", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_index("ix_users_email_active", "users", ["email", "is_active"])

    op.create_table(
        "analysis_jobs",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("job_uuid", sa.String(36), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("original_filename", sa.String(255), nullable=False),
        sa.Column("file_path", sa.String(500), nullable=False),
        sa.Column("file_size_bytes", sa.BigInteger(), nullable=True),
        sa.Column("video_duration_sec", sa.Float(), nullable=True),
        sa.Column("target_duration_sec", sa.Float(), nullable=True),
        sa.Column("status", sa.Enum("pending","processing","completed","failed", name="jobstatus"), nullable=False, server_default="pending"),
        sa.Column("current_step", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("step_progress", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("celery_task_id", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("job_uuid"),
    )
    op.create_index("ix_jobs_uuid", "analysis_jobs", ["job_uuid"], unique=True)
    op.create_index("ix_jobs_user_id", "analysis_jobs", ["user_id"])
    op.create_index("ix_jobs_status", "analysis_jobs", ["status"])
    op.create_index("ix_jobs_user_created", "analysis_jobs", ["user_id", "created_at"])
    op.create_index("ix_jobs_user_status", "analysis_jobs", ["user_id", "status"])

    op.create_table(
        "analysis_results",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("job_id", sa.BigInteger(), nullable=False),
        sa.Column("total_score", sa.Float(), nullable=False),
        sa.Column("gaze_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("posture_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("speech_rate_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("volume_pitch_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("filler_word_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("pronunciation_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("time_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("visual_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("audio_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("vocab_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("delivery_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("raw_metrics", sa.JSON(), nullable=True),
        sa.Column("feedback_summary", sa.Text(), nullable=True),
        sa.Column("feedback_strengths", sa.Text(), nullable=True),
        sa.Column("feedback_improvements", sa.Text(), nullable=True),
        sa.Column("feedback_details", sa.JSON(), nullable=True),
        sa.Column("calibration_data", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["job_id"], ["analysis_jobs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("job_id"),
    )
    op.create_index("ix_results_job_id", "analysis_results", ["job_id"], unique=True)

    op.create_table(
        "timeline_events",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("job_id", sa.BigInteger(), nullable=False),
        sa.Column("timestamp_sec", sa.Float(), nullable=False),
        sa.Column("end_timestamp_sec", sa.Float(), nullable=True),
        sa.Column("event_type", sa.Enum("filler_word","gaze_miss","low_volume","fast_speech","slow_speech","posture_sway","pronunciation", name="eventtype"), nullable=False),
        sa.Column("severity", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("extra_data", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["job_id"], ["analysis_jobs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_timeline_job_id", "timeline_events", ["job_id"])
    op.create_index("ix_timeline_job_ts", "timeline_events", ["job_id", "timestamp_sec"])
    op.create_index("ix_timeline_job_type", "timeline_events", ["job_id", "event_type"])


def downgrade() -> None:
    op.drop_table("timeline_events")
    op.drop_table("analysis_results")
    op.drop_table("analysis_jobs")
    op.drop_table("users")

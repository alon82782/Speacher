from celery import Celery
from app.config import settings

celery_app = Celery(
    "speacher",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.tasks.analysis_task"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Seoul",
    enable_utc=True,
    result_expires=60 * 60 * 24 * 7,
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    task_soft_time_limit=settings.ANALYSIS_TIMEOUT_SECONDS,
    task_time_limit=settings.ANALYSIS_TIMEOUT_SECONDS + 60,
)

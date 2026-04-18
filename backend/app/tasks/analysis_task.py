from celery import shared_task
from app.utils.logger import logger


@shared_task(
    bind=True,
    name="app.tasks.analysis_task.run_analysis",
    max_retries=2,
    default_retry_delay=30,
)
def run_analysis(self, job_id: str, file_path: str, user_id: int, meta: dict):
    logger.info(f"[Analysis Start] job_id={job_id}")
    try:
        # Phase 5에서 파이프라인 구현 예정
        pass
    except Exception as exc:
        logger.error(f"[Analysis Failed] job_id={job_id}, error={exc}")
        raise self.retry(exc=exc)

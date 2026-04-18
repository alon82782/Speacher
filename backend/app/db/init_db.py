from app.db.session import engine
from app.utils.logger import logger


async def init_db() -> None:
    try:
        async with engine.connect() as conn:
            await conn.run_sync(lambda _: None)
        logger.info("DB 연결 확인")
    except Exception as e:
        logger.error(f"DB 연결 실패: {e}")
        raise

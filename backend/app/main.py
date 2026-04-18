import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.api.v1.router import api_router
from app.config import settings
from app.middleware.error_handler import register_error_handlers
from app.db.session import engine
from app.utils.logger import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Speacher API Start | ENV={settings.APP_ENV}")
    os.makedirs(settings.TEMP_UPLOAD_DIR, exist_ok=True)
    yield
    logger.info("Speacher API Stop")
    await engine.dispose()


limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title="Speacher API",
    description="AI Presentation Coaching System",
    version="1.0.0",
    docs_url="/docs" if settings.APP_DEBUG else None,
    redoc_url="/redoc" if settings.APP_DEBUG else None,
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

register_error_handlers(app)
app.include_router(api_router, prefix="/api/v1")


@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "healthy", "env": settings.APP_ENV, "version": "1.0.0"}

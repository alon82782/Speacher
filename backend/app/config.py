from functools import lru_cache
from typing import List
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    APP_ENV: str = "development"
    APP_DEBUG: bool = True
    APP_SECRET_KEY: str = "dev-secret-key"
    ALLOWED_ORIGINS: str = "http://localhost:5173,http://localhost:3000"

    @property
    def allowed_origins_list(self) -> List[str]:
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",")]

    DB_HOST: str = "localhost"
    DB_PORT: int = 3306
    DB_NAME: str = "speacher"
    DB_USER: str = "speacher_user"
    DB_PASSWORD: str = "speacher_password"
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20

    @property
    def database_url(self) -> str:
        return (
            f"mysql+aiomysql://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}?charset=utf8mb4"
        )

    JWT_SECRET_KEY: str = "jwt-dev-secret"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str = ""
    REDIS_DB: int = 0

    @property
    def redis_url(self) -> str:
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o"

    MAX_FILE_SIZE_MB: int = 500
    ALLOWED_VIDEO_EXTENSIONS: str = "mp4,mov,avi,webm"
    TEMP_UPLOAD_DIR: str = "/tmp/speacher_uploads"

    @property
    def allowed_extensions(self) -> List[str]:
        return [e.strip().lower() for e in self.ALLOWED_VIDEO_EXTENSIONS.split(",")]

    @property
    def max_file_size_bytes(self) -> int:
        return self.MAX_FILE_SIZE_MB * 1024 * 1024

    WHISPER_MODEL: str = "base"
    CALIBRATION_SECONDS: int = 3
    ANALYSIS_TIMEOUT_SECONDS: int = 600

    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_UPLOAD_PER_HOUR: int = 10

    SCORE_GAZE: int = 25
    SCORE_POSTURE: int = 10
    SCORE_SPEECH_RATE: int = 20
    SCORE_VOLUME_PITCH: int = 15
    SCORE_FILLER_WORD: int = 15
    SCORE_PRONUNCIATION: int = 10
    SCORE_TIME_COMPLIANCE: int = 5


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

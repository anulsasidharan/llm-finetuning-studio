from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    APP_NAME: str = "LLM Fine-Tuning Studio"
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "DEBUG"
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    POSTGRES_HOST: str = "postgres"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "fts_user"
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str = "fts_db"
    DATABASE_URL: str
    DATABASE_URL_SYNC: str

    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str
    REDIS_URL: str
    CELERY_BROKER_URL: str
    CELERY_RESULT_BACKEND: str

    MINIO_HOST: str = "minio"
    MINIO_PORT: int = 9000
    MINIO_ROOT_USER: str = "minioadmin"
    MINIO_ROOT_PASSWORD: str
    MINIO_ENDPOINT: str = "http://minio:9000"
    MINIO_USE_SSL: bool = False

    BUCKET_DATASETS: str = "fts-datasets"
    BUCKET_MODELS: str = "fts-models"
    BUCKET_CHECKPOINTS: str = "fts-checkpoints"
    BUCKET_EXPORTS: str = "fts-exports"

    HF_TOKEN: str = ""
    HF_WRITE_TOKEN: str = ""
    HF_CACHE_DIR: str = "/app/.cache/huggingface"

    MAX_UPLOAD_SIZE_MB: int = 500


settings = Settings()

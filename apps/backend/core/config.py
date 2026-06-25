from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

_CONFIG_PARENTS = Path(__file__).resolve().parents
REPO_ROOT_ENV_FILE = _CONFIG_PARENTS[3] / ".env" if len(_CONFIG_PARENTS) > 3 else None


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=REPO_ROOT_ENV_FILE,
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # ─── App ────────────────────────────────────────────────────────
    APP_NAME: str = "LLM Fine-Tuning Studio"
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "DEBUG"
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    # ─── PostgreSQL ─────────────────────────────────────────────────
    POSTGRES_HOST: str = "postgres"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "fts_user"
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str = "fts_db"
    DATABASE_URL: str
    DATABASE_URL_SYNC: str

    # ─── Redis ──────────────────────────────────────────────────────
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str
    REDIS_URL: str
    CELERY_BROKER_URL: str
    CELERY_RESULT_BACKEND: str
    TRAINING_PUBSUB_DB: str = ""

    # ─── MinIO ──────────────────────────────────────────────────────
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

    # ─── AWS S3 (production — replaces MinIO) ───────────────────────
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    AWS_DEFAULT_REGION: str = "us-east-1"
    S3_BUCKET_DATASETS: str = "fts-datasets-prod"
    S3_BUCKET_MODELS: str = "fts-models-prod"
    S3_BUCKET_CHECKPOINTS: str = "fts-checkpoints-prod"
    S3_BUCKET_EXPORTS: str = "fts-exports-prod"

    # ─── HuggingFace ────────────────────────────────────────────────
    HF_TOKEN: str = ""
    HF_WRITE_TOKEN: str = ""
    HF_CACHE_DIR: str = "/app/.cache/huggingface"

    # ─── Cloud GPU Vendors ──────────────────────────────────────────
    RUNPOD_API_KEY: str = ""
    LAMBDA_LABS_API_KEY: str = ""
    CLOUD_AWS_ACCESS_KEY_ID: str = ""
    CLOUD_AWS_SECRET_ACCESS_KEY: str = ""
    CLOUD_GCP_SERVICE_ACCOUNT_JSON: str = ""
    CLOUD_AZURE_SUBSCRIPTION_ID: str = ""
    CLOUD_AZURE_CLIENT_ID: str = ""
    CLOUD_AZURE_CLIENT_SECRET: str = ""
    CLOUD_AZURE_TENANT_ID: str = ""

    # ─── GPU Pricing ────────────────────────────────────────────────
    GPU_PRICING_CACHE_TTL_SECONDS: int = 3600

    # ─── Cloud Launcher ─────────────────────────────────────────────
    TRAINING_ENGINE_DOCKER_IMAGE: str = ""

    # ─── Notifications (optional) ───────────────────────────────────
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    NOTIFICATION_FROM_EMAIL: str = "noreply@orionvexa.ca"
    SLACK_WEBHOOK_URL: str = ""

    # ─── Training Engine ────────────────────────────────────────────
    MAX_UPLOAD_SIZE_MB: int = 500
    TRAINING_CHECKPOINT_INTERVAL_STEPS: int = 200
    TRAINING_METRICS_PUSH_INTERVAL_SECONDS: int = 5
    TRAINING_ENGINE_REDIS_URL: str = ""


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

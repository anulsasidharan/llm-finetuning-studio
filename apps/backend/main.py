import asyncio
from collections.abc import AsyncIterator, Callable, Coroutine
from contextlib import asynccontextmanager

import redis.asyncio as redis_asyncio
import structlog
from api.v1 import api_router
from core.config import settings
from core.database import AsyncSessionLocal
from core.storage import minio_client
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

log = structlog.get_logger()

HealthCheck = Callable[[], Coroutine[None, None, str]]
_HEALTH_CHECK_TIMEOUT_SECONDS: float = 5.0


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    log.info("fts.api.startup", version="1.0.0", environment=settings.ENVIRONMENT)
    yield


async def _check_database() -> str:
    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
        return "up"
    except Exception as exc:
        log.warning("fts.health.database_down", error=str(exc))
        return "down"


async def _check_redis() -> str:
    try:
        client = redis_asyncio.from_url(settings.REDIS_URL)
        try:
            await client.ping()
            return "up"
        finally:
            await client.aclose()
    except Exception as exc:
        log.warning("fts.health.redis_down", error=str(exc))
        return "down"


async def _check_storage() -> str:
    try:
        await asyncio.to_thread(minio_client.bucket_exists, settings.BUCKET_DATASETS)
        return "up"
    except Exception as exc:
        log.warning("fts.health.storage_down", error=str(exc))
        return "down"


async def _check_with_timeout(check: HealthCheck, name: str) -> str:
    try:
        return await asyncio.wait_for(check(), timeout=_HEALTH_CHECK_TIMEOUT_SECONDS)
    except TimeoutError:
        log.warning("fts.health.timeout", dependency=name)
        return "down"


def create_app() -> FastAPI:
    app = FastAPI(
        title="LLM Fine-Tuning Studio API",
        description="Backend API for LLM Fine-Tuning Studio",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_router, prefix="/api/v1")

    @app.get("/health", tags=["health"])
    async def health() -> dict[str, str]:
        database_status, redis_status, storage_status = await asyncio.gather(
            _check_with_timeout(_check_database, "database"),
            _check_with_timeout(_check_redis, "redis"),
            _check_with_timeout(_check_storage, "storage"),
        )
        overall_status = (
            "healthy"
            if all(s == "up" for s in (database_status, redis_status, storage_status))
            else "degraded"
        )
        return {
            "status": overall_status,
            "service": "LLM Fine-Tuning Studio API",
            "version": "1.0.0",
            "database": database_status,
            "redis": redis_status,
            "storage": storage_status,
        }

    return app


app = create_app()

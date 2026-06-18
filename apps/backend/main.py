from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import structlog
from api.v1 import api_router
from core.config import settings
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

log = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    log.info("fts.api.startup", version="1.0.0", environment=settings.ENVIRONMENT)
    yield


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
        return {
            "status": "healthy",
            "service": "LLM Fine-Tuning Studio API",
            "version": "1.0.0",
        }

    return app


app = create_app()

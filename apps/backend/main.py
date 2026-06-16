import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

log = structlog.get_logger()

app = FastAPI(
    title="LLM Fine-Tuning Studio API",
    description="Backend API for LLM Fine-Tuning Studio",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup():
    log.info("fts.api.startup", version="1.0.0", environment="development")


@app.get("/health", tags=["health"])
async def health():
    return {
        "status": "healthy",
        "service": "LLM Fine-Tuning Studio API",
        "version": "1.0.0",
    }

"""Exports the FastAPI app's OpenAPI schema for frontend type generation.
Run with: uv run python scripts/export_openapi.py
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import structlog
from main import app

log = structlog.get_logger()

OUTPUT_PATH = Path(__file__).resolve().parents[2] / "frontend" / "openapi" / "schema.json"


def export_openapi_schema() -> None:
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(app.openapi(), indent=2) + "\n", encoding="utf-8")
    log.info("fts.openapi.exported", path=str(OUTPUT_PATH))


if __name__ == "__main__":
    export_openapi_schema()

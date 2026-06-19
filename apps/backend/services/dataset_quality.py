"""Quality checks for normalized (ChatML) dataset rows.

Ported from `training_engine/datasets/quality_check.py` rather than
imported, since `apps/backend` and `training_engine` are separate
standalone processes/environments per CLAUDE.md's architecture decision.
Keep the two copies in sync if either evolves.

Operates on the canonical `{"messages": [...]}` rows produced by
`services.dataset_format.to_chatml` — exact-match deduplication,
word-count summary stats, and per-row language detection.
"""

import statistics
from collections import Counter

from langdetect import DetectorFactory, LangDetectException, detect

# Deterministic detection results across runs (langdetect's detector is
# seeded from a non-deterministic RNG by default).
DetectorFactory.seed = 0

_EMPTY_WORD_COUNT_STATS = {"min": 0, "max": 0, "mean": 0, "median": 0}


def _row_text(row: dict) -> str:
    messages = row.get("messages", [])
    return " ".join(message.get("content", "") for message in messages)


def _normalize_for_dedup(text: str) -> str:
    return " ".join(text.lower().split())


def _detect_language(text: str) -> str:
    try:
        return detect(text)
    except LangDetectException:
        return "unknown"


def run_quality_check(rows: list[dict]) -> dict:
    """Run dedup, word-count stats, and language detection over `rows`.

    `rows` must be in the canonical ChatML shape `{"messages": [...]}`.
    Returns a JSON-serializable quality report dict.
    """
    total_rows = len(rows)
    texts = [_row_text(row) for row in rows]

    seen: set[str] = set()
    duplicate_indices: list[int] = []
    for index, text in enumerate(texts):
        key = _normalize_for_dedup(text)
        if key in seen:
            duplicate_indices.append(index)
        else:
            seen.add(key)

    word_counts = [len(text.split()) for text in texts]
    word_count_stats = (
        {
            "min": min(word_counts),
            "max": max(word_counts),
            "mean": round(statistics.mean(word_counts), 2),
            "median": statistics.median(word_counts),
        }
        if word_counts
        else dict(_EMPTY_WORD_COUNT_STATS)
    )

    languages = Counter(_detect_language(text) for text in texts if text.strip())

    return {
        "total_rows": total_rows,
        "duplicate_rows": len(duplicate_indices),
        "unique_rows": total_rows - len(duplicate_indices),
        "duplicate_indices": duplicate_indices,
        "word_count": word_count_stats,
        "languages": dict(languages),
    }

"""Detect and normalize Alpaca / ShareGPT / ChatML dataset rows.

Canonical internal representation is ChatML-style ``{"messages": [...]}``,
since that's the shape ``trl.SFTTrainer``/``DPOTrainer`` expect.
"""

SUPPORTED_FORMATS = ("alpaca", "sharegpt", "chatml")

_SHAREGPT_ROLE_MAP = {
    "human": "user",
    "gpt": "assistant",
    "system": "system",
}


class DatasetFormatError(ValueError):
    """Raised when a dataset row doesn't match any supported format."""


def _is_alpaca(row: dict) -> bool:
    return all(key in row for key in ("instruction", "input", "output"))


def _is_sharegpt(row: dict) -> bool:
    conversations = row.get("conversations")
    return (
        isinstance(conversations, list)
        and len(conversations) > 0
        and all(
            isinstance(turn, dict) and "from" in turn and "value" in turn for turn in conversations
        )
    )


def _is_chatml(row: dict) -> bool:
    messages = row.get("messages")
    return (
        isinstance(messages, list)
        and len(messages) > 0
        and all(
            isinstance(message, dict) and "role" in message and "content" in message
            for message in messages
        )
    )


def detect_format(row: dict) -> str:
    """Return one of `SUPPORTED_FORMATS` for `row`, or raise `DatasetFormatError`."""
    if not isinstance(row, dict):
        raise DatasetFormatError(f"Dataset row must be a dict, got {type(row).__name__}")
    if _is_chatml(row):
        return "chatml"
    if _is_sharegpt(row):
        return "sharegpt"
    if _is_alpaca(row):
        return "alpaca"
    raise DatasetFormatError(f"Unrecognized dataset row shape: keys={sorted(row.keys())}")


def to_chatml(row: dict, format: str | None = None) -> dict:
    """Normalize `row` to canonical `{"messages": [{"role", "content"}, ...]}`.

    `format` is auto-detected via `detect_format` when not given.
    """
    fmt = format or detect_format(row)

    if fmt == "alpaca":
        if not _is_alpaca(row):
            raise DatasetFormatError(f"Row does not match alpaca shape: keys={sorted(row.keys())}")
        instruction = row["instruction"]
        input_text = row["input"]
        user_content = f"{instruction}\n\n{input_text}" if input_text else instruction
        return {
            "messages": [
                {"role": "user", "content": user_content},
                {"role": "assistant", "content": row["output"]},
            ]
        }

    if fmt == "sharegpt":
        if not _is_sharegpt(row):
            raise DatasetFormatError(
                f"Row does not match sharegpt shape: keys={sorted(row.keys())}"
            )
        return {
            "messages": [
                {
                    "role": _SHAREGPT_ROLE_MAP.get(turn["from"], turn["from"]),
                    "content": turn["value"],
                }
                for turn in row["conversations"]
            ]
        }

    if fmt == "chatml":
        if not _is_chatml(row):
            raise DatasetFormatError(f"Row does not match chatml shape: keys={sorted(row.keys())}")
        return {"messages": row["messages"]}

    raise DatasetFormatError(f"Unsupported format: {fmt!r} (expected one of {SUPPORTED_FORMATS})")

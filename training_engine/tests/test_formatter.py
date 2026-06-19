import pytest
from datasets.formatter import DatasetFormatError, detect_format, to_chatml

ALPACA_ROW = {"instruction": "Summarize this.", "input": "Some text.", "output": "A summary."}
ALPACA_ROW_NO_INPUT = {"instruction": "Say hi.", "input": "", "output": "Hi!"}
SHAREGPT_ROW = {
    "conversations": [
        {"from": "human", "value": "Hello"},
        {"from": "gpt", "value": "Hi there"},
    ]
}
CHATML_ROW = {
    "messages": [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi there"},
    ]
}


@pytest.mark.parametrize(
    ("row", "expected"),
    [(ALPACA_ROW, "alpaca"), (SHAREGPT_ROW, "sharegpt"), (CHATML_ROW, "chatml")],
)
def test_detect_format(row: dict, expected: str) -> None:
    assert detect_format(row) == expected


@pytest.mark.parametrize(
    "row",
    [
        {},
        {"foo": "bar"},
        {"conversations": "not-a-list"},
        {"conversations": [{"from": "human"}]},
        {"messages": [{"role": "user"}]},
        {"instruction": "x"},
    ],
)
def test_detect_format_raises_on_malformed_row(row: dict) -> None:
    with pytest.raises(DatasetFormatError):
        detect_format(row)


def test_detect_format_raises_on_non_dict() -> None:
    with pytest.raises(DatasetFormatError):
        detect_format(["not", "a", "dict"])  # type: ignore[arg-type]


def test_to_chatml_from_alpaca_combines_instruction_and_input() -> None:
    result = to_chatml(ALPACA_ROW)
    assert result == {
        "messages": [
            {"role": "user", "content": "Summarize this.\n\nSome text."},
            {"role": "assistant", "content": "A summary."},
        ]
    }


def test_to_chatml_from_alpaca_without_input_omits_blank_line() -> None:
    result = to_chatml(ALPACA_ROW_NO_INPUT)
    assert result["messages"][0]["content"] == "Say hi."


def test_to_chatml_from_sharegpt_maps_roles() -> None:
    result = to_chatml(SHAREGPT_ROW)
    assert result == {
        "messages": [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there"},
        ]
    }


def test_to_chatml_from_chatml_is_passthrough() -> None:
    assert to_chatml(CHATML_ROW) == CHATML_ROW


def test_to_chatml_auto_detects_format_when_not_given() -> None:
    assert to_chatml(SHAREGPT_ROW, format=None) == to_chatml(SHAREGPT_ROW, format="sharegpt")


def test_to_chatml_raises_when_explicit_format_does_not_match_row() -> None:
    with pytest.raises(DatasetFormatError):
        to_chatml(ALPACA_ROW, format="sharegpt")


def test_to_chatml_raises_on_unsupported_format() -> None:
    with pytest.raises(DatasetFormatError):
        to_chatml(CHATML_ROW, format="xml")

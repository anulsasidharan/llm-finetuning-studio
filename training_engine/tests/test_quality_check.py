from datasets.quality_check import run_quality_check

EN_SENTENCE = (
    "This is a sufficiently long English sentence written to make the "
    "language detector confident about its result."
)
FR_SENTENCE = (
    "Ceci est une phrase suffisamment longue en francais ecrite pour que "
    "le detecteur de langue soit confiant dans son resultat."
)


def _row(content: str) -> dict:
    return {"messages": [{"role": "user", "content": content}]}


def test_run_quality_check_counts_total_and_unique_rows_with_no_duplicates() -> None:
    rows = [_row(EN_SENTENCE), _row(FR_SENTENCE)]
    report = run_quality_check(rows)
    assert report["total_rows"] == 2
    assert report["unique_rows"] == 2
    assert report["duplicate_rows"] == 0
    assert report["duplicate_indices"] == []


def test_run_quality_check_detects_exact_duplicate_rows() -> None:
    rows = [_row(EN_SENTENCE), _row(EN_SENTENCE), _row(FR_SENTENCE)]
    report = run_quality_check(rows)
    assert report["total_rows"] == 3
    assert report["duplicate_rows"] == 1
    assert report["unique_rows"] == 2
    assert report["duplicate_indices"] == [1]


def test_run_quality_check_dedup_ignores_case_and_whitespace() -> None:
    rows = [_row("Hello   World"), _row("hello world")]
    report = run_quality_check(rows)
    assert report["duplicate_rows"] == 1
    assert report["duplicate_indices"] == [1]


def test_run_quality_check_word_count_stats_on_known_dataset() -> None:
    rows = [_row("one two"), _row("one two three four"), _row("one")]
    report = run_quality_check(rows)
    assert report["word_count"] == {"min": 1, "max": 4, "mean": 2.33, "median": 2}


def test_run_quality_check_detects_english_language() -> None:
    report = run_quality_check([_row(EN_SENTENCE)])
    assert report["languages"] == {"en": 1}


def test_run_quality_check_detects_french_language() -> None:
    report = run_quality_check([_row(FR_SENTENCE)])
    assert report["languages"] == {"fr": 1}


def test_run_quality_check_languages_distribution_counts_per_row() -> None:
    rows = [_row(EN_SENTENCE), _row(EN_SENTENCE), _row(FR_SENTENCE)]
    report = run_quality_check(rows)
    assert report["languages"] == {"en": 2, "fr": 1}


def test_run_quality_check_handles_empty_rows_list() -> None:
    report = run_quality_check([])
    assert report == {
        "total_rows": 0,
        "duplicate_rows": 0,
        "unique_rows": 0,
        "duplicate_indices": [],
        "word_count": {"min": 0, "max": 0, "mean": 0, "median": 0},
        "languages": {},
    }


def test_run_quality_check_skips_blank_rows_in_language_detection() -> None:
    report = run_quality_check([_row(""), _row(EN_SENTENCE)])
    assert report["total_rows"] == 2
    assert report["languages"] == {"en": 1}


def test_run_quality_check_handles_multi_turn_rows() -> None:
    row = {
        "messages": [
            {"role": "user", "content": "one two"},
            {"role": "assistant", "content": "three four five"},
        ]
    }
    report = run_quality_check([row])
    assert report["word_count"] == {"min": 5, "max": 5, "mean": 5, "median": 5}

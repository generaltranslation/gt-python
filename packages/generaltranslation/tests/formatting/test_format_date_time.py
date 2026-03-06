"""Tests for format_date_time."""

import json
from pathlib import Path

import pytest
from generaltranslation.formatting import format_date_time

FIXTURES = json.loads(
    (Path(__file__).parent / "fixtures" / "formatting_fixtures.json").read_text()
)


def _normalize_ws(s: str) -> str:
    """Normalize Unicode whitespace (NNBSP \\u202f → regular space).

    Babel and JS Intl may use different whitespace characters (e.g. before
    AM/PM), so we normalize for comparison.
    """
    return s.replace("\u202f", " ")


@pytest.mark.parametrize("case", FIXTURES["format_date_time"])
def test_format_date_time(case):
    result = format_date_time(
        case["value"],
        locales=case.get("locales"),
        options=case.get("options"),
    )
    expected = case["expected"]
    assert _normalize_ws(result) == _normalize_ws(expected), (
        f"format_date_time({case['value']!r}, {case.get('locales')!r}, "
        f"{case.get('options')!r}): {result!r} != {expected!r}"
    )

"""Tests for format_message."""

import json
from pathlib import Path

import pytest
from generaltranslation.formatting import format_message

FIXTURES = json.loads(
    (Path(__file__).parent / "fixtures" / "formatting_fixtures.json").read_text()
)


@pytest.mark.parametrize("case", FIXTURES["format_message"])
def test_format_message(case):
    result = format_message(
        case["message"],
        locales=case.get("locales"),
        variables=case.get("variables"),
    )
    assert result == case["expected"], (
        f"format_message({case['message']!r}, {case.get('locales')!r}, "
        f"{case.get('variables')!r}): {result!r} != {case['expected']!r}"
    )

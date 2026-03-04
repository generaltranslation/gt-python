"""Tests for format_relative_time."""

import json
from pathlib import Path

import pytest
from generaltranslation.formatting import format_relative_time

FIXTURES = json.loads(
    (Path(__file__).parent / "fixtures" / "formatting_fixtures.json").read_text()
)


@pytest.mark.parametrize("case", FIXTURES["format_relative_time"])
def test_format_relative_time(case):
    result = format_relative_time(
        case["value"],
        unit=case["unit"],
        locales=case.get("locales"),
        options=case.get("options"),
    )
    assert result == case["expected"], (
        f"format_relative_time({case['value']!r}, {case['unit']!r}, "
        f"{case.get('locales')!r}, {case.get('options')!r}): "
        f"{result!r} != {case['expected']!r}"
    )

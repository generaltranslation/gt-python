"""Tests for format_list."""

import json
from pathlib import Path
from typing import Any

import pytest
from generaltranslation.formatting import format_list

FIXTURES = json.loads((Path(__file__).parent / "fixtures" / "formatting_fixtures.json").read_text())


@pytest.mark.parametrize("case", FIXTURES["format_list"])
def test_format_list(case: dict[str, Any]) -> None:
    result = format_list(
        case["value"],
        locales=case.get("locales"),
        options=case.get("options"),
    )
    assert result == case["expected"], (
        f"format_list({case['value']!r}, {case.get('locales')!r}, "
        f"{case.get('options')!r}): {result!r} != {case['expected']!r}"
    )

"""Tests for format_list_to_parts."""

import json
from pathlib import Path
from typing import Any

import pytest
from generaltranslation.formatting import format_list_to_parts

FIXTURES = json.loads((Path(__file__).parent / "fixtures" / "formatting_fixtures.json").read_text())


@pytest.mark.parametrize("case", FIXTURES["format_list_to_parts"])
def test_format_list_to_parts(case: dict[str, Any]) -> None:
    result = format_list_to_parts(
        case["value"],
        locales=case.get("locales"),
        options=case.get("options"),
    )
    assert result == case["expected"], (
        f"format_list_to_parts({case['value']!r}, {case.get('locales')!r}, "
        f"{case.get('options')!r}): {result!r} != {case['expected']!r}"
    )

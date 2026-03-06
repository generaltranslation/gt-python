"""Tests for format_num."""

import json
from pathlib import Path
from typing import Any

import pytest
from generaltranslation.formatting import format_num

FIXTURES = json.loads((Path(__file__).parent / "fixtures" / "formatting_fixtures.json").read_text())


@pytest.mark.parametrize("case", FIXTURES["format_num"])
def test_format_num(case: dict[str, Any]) -> None:
    result = format_num(
        case["value"],
        locales=case.get("locales"),
        options=case.get("options"),
    )
    assert result == case["expected"], (
        f"format_num({case['value']!r}, {case.get('locales')!r}, {case.get('options')!r}): "
        f"{result!r} != {case['expected']!r}"
    )

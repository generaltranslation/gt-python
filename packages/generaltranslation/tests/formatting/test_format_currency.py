"""Tests for format_currency."""

import json
from pathlib import Path
from typing import Any

import pytest
from generaltranslation.formatting import format_currency

FIXTURES = json.loads((Path(__file__).parent / "fixtures" / "formatting_fixtures.json").read_text())


@pytest.mark.parametrize("case", FIXTURES["format_currency"])
def test_format_currency(case: dict[str, Any]) -> None:
    result = format_currency(
        case["value"],
        currency=case.get("currency", "USD"),
        locales=case.get("locales"),
        options=case.get("options"),
    )
    assert result == case["expected"], (
        f"format_currency({case['value']!r}, {case.get('currency')!r}, "
        f"{case.get('locales')!r}, {case.get('options')!r}): "
        f"{result!r} != {case['expected']!r}"
    )

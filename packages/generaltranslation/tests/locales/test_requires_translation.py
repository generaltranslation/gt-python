"""Tests for _requires_translation.py."""

import json
from pathlib import Path
from typing import Any

import pytest
from generaltranslation.locales import requires_translation

FIXTURES = json.loads((Path(__file__).parent / "fixtures" / "locale_fixtures.json").read_text())


@pytest.mark.parametrize("case", FIXTURES["requires_translation"])
def test_requires_translation(case: dict[str, Any]) -> None:
    result = requires_translation(
        case["source"],
        case["target"],
        approved_locales=case.get("approved"),
    )
    assert result == case["expected"]

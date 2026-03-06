"""Tests for _custom_locale_mapping.py."""

import json
from pathlib import Path
from typing import Any

import pytest
from generaltranslation.locales import get_custom_property, should_use_canonical_locale

FIXTURES = json.loads((Path(__file__).parent / "fixtures" / "locale_fixtures.json").read_text())
MAPPING = FIXTURES["custom_mapping"]["mapping"]


@pytest.mark.parametrize("case", FIXTURES["custom_mapping"]["get_custom_property"])
def test_get_custom_property(case: dict[str, Any]) -> None:
    result = get_custom_property(MAPPING, case["locale"], case["property"])
    assert result == case["expected"]


_CANONICAL_CASES = FIXTURES["custom_mapping"]["should_use_canonical_locale"]


@pytest.mark.parametrize("case", _CANONICAL_CASES)
def test_should_use_canonical_locale(case: dict[str, Any]) -> None:
    result = should_use_canonical_locale(case["locale"], MAPPING)
    assert result == case["expected"]

"""Tests for _get_region_properties.py."""

import json
from pathlib import Path
from typing import Any

import pytest
from generaltranslation.locales import get_region_properties

FIXTURES = json.loads((Path(__file__).parent / "fixtures" / "locale_fixtures.json").read_text())


@pytest.mark.parametrize("case", FIXTURES["get_region_properties"])
def test_get_region_properties(case: dict[str, Any]) -> None:
    result = get_region_properties(case["region"], default_locale=case["default_locale"])
    expected = case["expected"]
    assert result["code"] == expected["code"]
    assert result["name"] == expected["name"]
    assert result["emoji"] == expected["emoji"]

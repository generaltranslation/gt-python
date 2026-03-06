"""Tests for _get_locale_emoji.py."""

import json
from pathlib import Path
from typing import Any

import pytest
from generaltranslation.locales import get_locale_emoji

FIXTURES = json.loads((Path(__file__).parent / "fixtures" / "locale_fixtures.json").read_text())


@pytest.mark.parametrize("case", FIXTURES["get_locale_emoji"])
def test_get_locale_emoji(case: dict[str, Any]) -> None:
    result = get_locale_emoji(case["locale"])
    assert result == case["expected"]

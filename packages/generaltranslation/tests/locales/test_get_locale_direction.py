"""Tests for _get_locale_direction.py."""

import json
from pathlib import Path

import pytest
from generaltranslation.locales import get_locale_direction

FIXTURES = json.loads(
    (Path(__file__).parent / "fixtures" / "locale_fixtures.json").read_text()
)


@pytest.mark.parametrize("case", FIXTURES["get_locale_direction"])
def test_get_locale_direction(case):
    result = get_locale_direction(case["locale"])
    assert result == case["expected"]

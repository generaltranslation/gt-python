"""Tests for _get_locale_name.py."""
import json
from pathlib import Path

import pytest
from generaltranslation.locales import get_locale_name

FIXTURES = json.loads(
    (Path(__file__).parent / "fixtures" / "locale_fixtures.json").read_text()
)


@pytest.mark.parametrize("case", FIXTURES["get_locale_name"])
def test_get_locale_name(case):
    result = get_locale_name(case["locale"], default_locale=case["default_locale"])
    assert result == case["expected"]

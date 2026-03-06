"""Tests for _determine_locale.py."""

import json
from pathlib import Path

import pytest
from generaltranslation.locales import determine_locale

FIXTURES = json.loads(
    (Path(__file__).parent / "fixtures" / "locale_fixtures.json").read_text()
)


@pytest.mark.parametrize("case", FIXTURES["determine_locale"])
def test_determine_locale(case):
    result = determine_locale(case["locales"], case["approved"])
    assert result == case["expected"]

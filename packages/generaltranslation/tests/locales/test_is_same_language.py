"""Tests for _is_same_language.py."""
import json
from pathlib import Path

import pytest
from generaltranslation.locales import is_same_language

FIXTURES = json.loads(
    (Path(__file__).parent / "fixtures" / "locale_fixtures.json").read_text()
)


@pytest.mark.parametrize("case", FIXTURES["is_same_language"])
def test_is_same_language(case):
    result = is_same_language(*case["locales"])
    assert result == case["expected"]

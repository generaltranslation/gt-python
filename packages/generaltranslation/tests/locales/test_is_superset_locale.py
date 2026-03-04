"""Tests for _is_superset_locale.py."""
import json
from pathlib import Path

import pytest
from generaltranslation.locales import is_superset_locale

FIXTURES = json.loads(
    (Path(__file__).parent / "fixtures" / "locale_fixtures.json").read_text()
)


@pytest.mark.parametrize("case", FIXTURES["is_superset_locale"])
def test_is_superset_locale(case):
    result = is_superset_locale(case["super_locale"], case["sub_locale"])
    assert result == case["expected"]

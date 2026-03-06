"""Tests for _is_same_dialect.py."""

import json
from pathlib import Path
from typing import Any

import pytest
from generaltranslation.locales import is_same_dialect

FIXTURES = json.loads((Path(__file__).parent / "fixtures" / "locale_fixtures.json").read_text())


@pytest.mark.parametrize("case", FIXTURES["is_same_dialect"])
def test_is_same_dialect(case: dict[str, Any]) -> None:
    result = is_same_dialect(*case["locales"])
    assert result == case["expected"]

"""Tests for _get_plural_form.py."""

import json
from pathlib import Path
from typing import Any

import pytest
from generaltranslation.locales import get_plural_form

FIXTURES = json.loads((Path(__file__).parent / "fixtures" / "locale_fixtures.json").read_text())


@pytest.mark.parametrize("case", FIXTURES["get_plural_form"])
def test_get_plural_form(case: dict[str, Any]) -> None:
    result = get_plural_form(
        case["n"],
        forms=case["forms"],
        locales=case["locales"],
    )
    assert result == case["expected"]

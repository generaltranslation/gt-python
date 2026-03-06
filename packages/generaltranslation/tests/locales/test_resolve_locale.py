"""Tests for _resolve_locale.py."""

import json
from pathlib import Path

import pytest
from generaltranslation.locales import resolve_alias_locale, resolve_canonical_locale

FIXTURES = json.loads(
    (Path(__file__).parent / "fixtures" / "locale_fixtures.json").read_text()
)


@pytest.mark.parametrize("case", FIXTURES["resolve_canonical_locale"])
def test_resolve_canonical_locale(case):
    result = resolve_canonical_locale(case["locale"], case["mapping"])
    assert result == case["expected"]


@pytest.mark.parametrize("case", FIXTURES["resolve_alias_locale"])
def test_resolve_alias_locale(case):
    result = resolve_alias_locale(case["locale"], case["mapping"])
    assert result == case["expected"]

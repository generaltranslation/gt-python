"""Tests for _is_valid_locale.py."""

import json
from pathlib import Path

import pytest
from generaltranslation.locales import is_valid_locale, standardize_locale

FIXTURES = json.loads(
    (Path(__file__).parent / "fixtures" / "locale_fixtures.json").read_text()
)


@pytest.mark.parametrize("locale", FIXTURES["is_valid_locale"]["valid"])
def test_valid_locale(locale):
    assert is_valid_locale(locale) is True


@pytest.mark.parametrize("locale", FIXTURES["is_valid_locale"]["invalid"])
def test_invalid_locale(locale):
    assert is_valid_locale(locale) is False


@pytest.mark.parametrize("case", FIXTURES["is_valid_locale"]["custom_mapping_cases"])
def test_custom_mapping(case):
    result = is_valid_locale(case["locale"], case["mapping"])
    assert result == case["expected"]


@pytest.mark.parametrize("case", FIXTURES["standardize_locale"])
def test_standardize_locale(case):
    result = standardize_locale(case["input"])
    assert result == case["expected"]

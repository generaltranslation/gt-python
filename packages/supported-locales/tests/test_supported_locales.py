"""Tests for generaltranslation_supported_locales, parametrized from JS fixtures."""

import json
from pathlib import Path

import pytest

from generaltranslation_supported_locales import (
    get_supported_locale,
    list_supported_locales,
)
from generaltranslation_supported_locales._data import _SUPPORTED_LOCALES

FIXTURES = json.loads(
    (Path(__file__).parent / "fixtures" / "supported_locales_fixtures.json").read_text()
)


@pytest.mark.parametrize(
    "case",
    FIXTURES["get_supported_locale"],
    ids=[c["input"] or "<empty>" for c in FIXTURES["get_supported_locale"]],
)
def test_get_supported_locale(case):
    result = get_supported_locale(case["input"])
    assert result == case["expected"]


def test_list_supported_locales():
    result = list_supported_locales()
    assert result == FIXTURES["list_supported_locales"]["expected"]


def test_list_supported_locales_is_list():
    assert isinstance(list_supported_locales(), list)


def test_list_supported_locales_is_sorted():
    result = list_supported_locales()
    assert result == sorted(result)


def test_list_supported_locales_no_duplicates():
    result = list_supported_locales()
    assert len(result) == len(set(result))


def test_list_supported_locales_count_matches_data():
    expected_count = sum(len(v) for v in _SUPPORTED_LOCALES.values())
    assert len(list_supported_locales()) == expected_count

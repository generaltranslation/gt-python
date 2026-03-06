"""Tests for extract_variables ($-key filtering)."""

from gt_i18n.translation_functions._extract_variables import extract_variables


def test_filters_dollar_keys():
    opts = {"name": "Alice", "$context": "greeting", "$id": "hello"}
    result = extract_variables(opts)
    assert result == {"name": "Alice"}


def test_keeps_all_non_dollar():
    opts = {"name": "Alice", "count": 5, "item": "apples"}
    result = extract_variables(opts)
    assert result == opts


def test_empty_dict():
    assert extract_variables({}) == {}


def test_all_dollar_keys():
    opts = {"$context": "x", "$id": "y", "$max_chars": 10}
    assert extract_variables(opts) == {}

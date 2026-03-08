"""Tests for extract_variables (_-key filtering)."""

from gt_i18n.translation_functions._extract_variables import extract_variables


def test_filters_underscore_keys() -> None:
    opts: dict[str, object] = dict({"name": "Alice", "_context": "greeting", "_id": "hello"})
    result = extract_variables(opts)
    assert result == {"name": "Alice"}


def test_keeps_all_non_underscore() -> None:
    opts = {"name": "Alice", "count": 5, "item": "apples"}
    result = extract_variables(opts)
    assert result == opts


def test_empty_dict() -> None:
    assert extract_variables({}) == {}


def test_all_underscore_keys() -> None:
    opts = {"_context": "x", "_id": "y", "_max_chars": 10}
    assert extract_variables(opts) == {}

"""Tests for the derive() function."""

from __future__ import annotations

from generaltranslation import derive


class TestDerive:
    """Tests for derive() — the canonical marker for derivable content."""

    def test_returns_same_string(self) -> None:
        assert derive("hello") == "hello"

    def test_returns_same_int(self) -> None:
        assert derive(42) == 42

    def test_returns_same_float(self) -> None:
        assert derive(3.14) == 3.14

    def test_returns_same_list(self) -> None:
        value = [1, 2, 3]
        assert derive(value) is value

    def test_returns_same_dict(self) -> None:
        value = {"key": "value"}
        assert derive(value) is value

    def test_returns_none(self) -> None:
        assert derive(None) is None

    def test_returns_same_bool(self) -> None:
        assert derive(True) is True

    def test_identity_preserves_reference(self) -> None:
        """derive() should be a pure identity function — same object in, same object out."""
        obj = object()
        assert derive(obj) is obj

    def test_nested_structure(self) -> None:
        value = {"a": [1, {"b": 2}]}
        assert derive(value) is value

    def test_empty_string(self) -> None:
        assert derive("") == ""

    def test_multiline_string(self) -> None:
        text = "line one\nline two\nline three"
        assert derive(text) == text

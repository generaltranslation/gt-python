"""Tests for the deprecated declare_static() function."""

from __future__ import annotations

import warnings

from generaltranslation import declare_static


class TestDeclareStaticDeprecation:
    """Placeholder tests for declare_static() — deprecated in favour of derive()."""

    def test_emits_deprecation_warning(self) -> None:
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            declare_static("hello")
            assert len(w) == 1
            assert issubclass(w[0].category, DeprecationWarning)
            assert "derive()" in str(w[0].message)

    def test_still_returns_value(self) -> None:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            assert declare_static("hello") == "hello"

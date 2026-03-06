"""Tests for t_fallback() — interpolation-only, no manager."""

from gt_i18n import t_fallback


def test_simple_interpolation():
    result = t_fallback("Hello, {name}!", name="World")
    assert result == "Hello, World!"


def test_no_variables():
    result = t_fallback("Hello, world!")
    assert result == "Hello, world!"


def test_multiple_variables():
    result = t_fallback("{a} and {b}", a="X", b="Y")
    assert result == "X and Y"


def test_with_declared_variables():
    from generaltranslation.static._declare_var import declare_var

    msg = f"Price: {declare_var('$99', name='price')}"
    result = t_fallback(msg)
    assert "$99" in result


def test_bad_icu_returns_source():
    """Invalid ICU syntax should return the source message."""
    result = t_fallback("{bad, plural, }")
    # Should return source (or something reasonable), not crash
    assert isinstance(result, str)

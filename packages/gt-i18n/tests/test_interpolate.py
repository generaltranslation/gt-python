"""Tests for interpolate_message pipeline."""

from gt_i18n.translation_functions._interpolate import interpolate_message


def test_simple_variable():
    result = interpolate_message("Hello, {name}!", {"name": "Alice"})
    assert result == "Hello, Alice!"


def test_multiple_variables():
    result = interpolate_message(
        "{greeting}, {name}!", {"greeting": "Hi", "name": "Bob"}
    )
    assert result == "Hi, Bob!"


def test_no_variables():
    result = interpolate_message("Hello, world!", {})
    assert result == "Hello, world!"


def test_max_chars_cutoff():
    result = interpolate_message(
        "This is a very long message that should be cut off",
        {"$max_chars": 10},
    )
    assert len(result) <= 10


def test_fallback_on_error():
    """Invalid ICU should fall back to the fallback message."""
    result = interpolate_message(
        "{invalid, plural, }",
        {"$_fallback": "fallback message"},
    )
    assert result == "fallback message"


def test_with_declared_variables():
    """Test interpolation with _gt_ declared variables."""
    from generaltranslation.static._declare_var import declare_var

    msg = f"Hello, {declare_var('Alice', name='user')}!"
    result = interpolate_message(msg, {})
    assert "Alice" in result

"""Tests for interpolate_message pipeline.

Tests are derived from the JS interpolateMessage behavior in:
packages/i18n/src/translation-functions/utils/interpolateMessage.ts
and its test suite in:
packages/i18n/src/translation-functions/fallbacks/__tests__/gtFallback.test.ts
"""

from generaltranslation.static._declare_var import declare_var
from gt_i18n.translation_functions._interpolate import interpolate_message

# --- Basic interpolation ---


def test_simple_variable() -> None:
    result = interpolate_message("Hello, {name}!", {"name": "Alice"})
    assert result == "Hello, Alice!"


def test_multiple_variables() -> None:
    result = interpolate_message("{greeting}, {name}!", {"greeting": "Hi", "name": "Bob"})
    assert result == "Hi, Bob!"


def test_no_variables() -> None:
    result = interpolate_message("Hello, world!", {})
    assert result == "Hello, world!"


def test_max_chars_cutoff() -> None:
    result = interpolate_message(
        "This is a very long message that should be cut off",
        {"$max_chars": 10},
    )
    assert len(result) <= 10


# --- declare_var (source message, no translation) ---


def test_declare_var_source_only() -> None:
    """declare_var values should be interpolated in the source message."""
    msg = f"Hello, {declare_var('Alice', name='user')}!"
    result = interpolate_message(msg, {})
    assert result == "Hello, Alice!"


def test_multiple_declare_vars() -> None:
    """Multiple declare_var values should all be interpolated."""
    msg = (
        f"{declare_var('Bob', name='user')} bought "
        f"{declare_var('5', name='count')} of "
        f"{declare_var('apples', name='item')}"
    )
    result = interpolate_message(msg, {})
    assert result == "Bob bought 5 of apples"


def test_declare_var_with_user_variables() -> None:
    """declare_var + regular ICU variables should both work."""
    msg = f"Hello, {declare_var('Alice', name='user')}! You have {{count}} items."
    result = interpolate_message(msg, {"count": "3"})
    assert "Alice" in result
    assert "3" in result


def test_empty_declare_var() -> None:
    """Empty declare_var value should produce empty string."""
    msg = f"Hello, {declare_var('', name='user')}!"
    result = interpolate_message(msg, {})
    assert result == "Hello, !"


# --- declare_var (translated message with $_fallback) ---


def test_translated_with_declare_var() -> None:
    """Translated strings reference _gt_ vars by index.

    JS behavior: extractVars is called on source/$_fallback, not on
    the translated message. The translated message uses {_gt_1} etc.
    as simple variable references.
    """
    source = f"Welcome back, {declare_var('Alice', name='user_name')}!"
    translated = "Bienvenido de nuevo, {_gt_1}!"
    result = interpolate_message(translated, {"$_fallback": source})
    assert result == "Bienvenido de nuevo, Alice!"


def test_translated_multiple_declare_vars() -> None:
    """Multiple _gt_ vars extracted from source, used in translation."""
    source = (
        f"{declare_var('Bob', name='user')} bought "
        f"{declare_var('5', name='count')} of "
        f"{declare_var('oranges', name='item')}"
    )
    translated = "{_gt_1} compró {_gt_2} de {_gt_3}"
    result = interpolate_message(translated, {"$_fallback": source})
    assert result == "Bob compró 5 de oranges"


def test_translated_reordered_vars() -> None:
    """Translation can reorder _gt_ variables."""
    source = f"{declare_var('Alice', name='user')} bought {declare_var('apples', name='item')}"
    # Translation reorders: item before user
    translated = "{_gt_2} fueron comprados por {_gt_1}"
    result = interpolate_message(translated, {"$_fallback": source})
    assert result == "apples fueron comprados por Alice"


# --- Fallback behavior (JS parity) ---


def test_fallback_retry_on_format_error() -> None:
    """When formatting the translated string fails, retry with the source.

    JS behavior: catch block recursively calls interpolateMessage(source,
    {...options, $_fallback: undefined}) — i.e. it tries to format the
    fallback/source message instead of returning it raw.
    """
    bad_translation = "{broken, plural, }"
    source = "Hello, world!"
    result = interpolate_message(bad_translation, {"$_fallback": source})
    # Should successfully format the source, not return it raw
    assert result == "Hello, world!"


def test_fallback_retry_preserves_user_vars() -> None:
    """Fallback retry should preserve user variables.

    JS behavior: on retry, the same options (minus $_fallback) are passed,
    so user variables are still interpolated into the source.
    """
    bad_translation = "{broken, plural, }"
    source = "Hello, {name}!"
    result = interpolate_message(bad_translation, {"$_fallback": source, "name": "Alice"})
    assert result == "Hello, Alice!"


def test_fallback_retry_preserves_declare_vars() -> None:
    """Fallback retry should also handle declare_var in the source."""
    bad_translation = "{broken, plural, }"
    source = f"Hello, {declare_var('Alice', name='user')}!"
    result = interpolate_message(bad_translation, {"$_fallback": source})
    assert result == "Hello, Alice!"


def test_no_fallback_returns_raw_with_cutoff() -> None:
    """When there's no fallback and formatting fails, return raw message with cutoff.

    JS behavior: final catch returns formatCutoff(encodedMsg, {maxChars}).
    """
    bad_msg = "{broken, plural, }"
    result = interpolate_message(bad_msg, {"$max_chars": 5})
    assert len(result) <= 5


def test_no_fallback_returns_raw_message() -> None:
    """When there's no fallback and formatting fails, return raw message."""
    bad_msg = "{broken, plural, }"
    result = interpolate_message(bad_msg, {})
    assert result == bad_msg


# --- Cutoff behavior ---


def test_cutoff_applied_after_interpolation() -> None:
    """$max_chars truncates after interpolation."""
    result = interpolate_message("Hello, {name}!", {"name": "Alice", "$max_chars": 8})
    assert len(result) <= 8


def test_cutoff_on_fallback_retry() -> None:
    """$max_chars should still apply when falling back to source."""
    bad_translation = "{broken, plural, }"
    source = "This is a long fallback message"
    result = interpolate_message(bad_translation, {"$_fallback": source, "$max_chars": 10})
    assert len(result) <= 10

"""Golden-standard tests for the format-aware hash_message behavior.

gt PR #1207 changed the hash algorithm: ``indexVars()`` is now applied ONLY for
ICU format, not for STRING or I18NEXT formats. This is a subtle but critical
on-wire compatibility pin — if the Python hash diverges from the JS hash, a
translation fetched by a JS client and a translation fetched by a Python
client will miss each other's cache.

Before this PR, Python's ``hash_message`` indexed vars unconditionally (the
current behavior). After the port, the function must accept a ``format`` kwarg
and branch on it:

- ``format="ICU"`` — index vars, then hash (UNCHANGED for ICU sources).
- ``format="STRING"`` — hash the raw message (NO indexing).
- ``format="I18NEXT"`` — hash the raw message (NO indexing).

All tests should FAIL until PR #1207 is ported — the current ``hash_message``
does not accept a ``format`` kwarg.
"""

from __future__ import annotations

from generaltranslation._id._hash import hash_source
from generaltranslation.static._index_vars import index_vars
from gt_i18n.translation_functions._hash_message import hash_message

# ---------------------------------------------------------------------------
# test_icu_format_hashes_with_indexed_vars
#
# The pre-existing ICU behavior MUST NOT change — ICU messages have their vars
# normalized (e.g. ``{name}`` → ``{_gt_0}``) before hashing so that two templates
# differing only in variable names collide.
#
# Example:
#     hash_message("Hello, {name}!", format="ICU")
#     # == hash_source(index_vars("Hello, {name}!"), data_format="ICU")
# ---------------------------------------------------------------------------


def test_icu_format_hashes_with_indexed_vars() -> None:
    """For ICU format, the hash is computed over index_vars(message) — UNCHANGED."""
    message = "Hello, {name}!"
    expected = hash_source(index_vars(message), data_format="ICU")
    assert hash_message(message, format="ICU") == expected


# ---------------------------------------------------------------------------
# test_string_format_hashes_raw_message
#
# NEW in PR #1207: for STRING format, the message is hashed raw — no var
# indexing. The rationale is that STRING templates pass the user's literal
# template verbatim to the translation service.
#
# Example:
#     hash_message("Hello, {name}!", format="STRING")
#     # == hash_source("Hello, {name}!", data_format="STRING")   (raw, NOT indexed)
# ---------------------------------------------------------------------------


def test_string_format_hashes_raw_message() -> None:
    """For STRING format, the hash is computed over the RAW message — no index_vars."""
    message = "Hello, {name}!"
    expected = hash_source(message, data_format="STRING")
    assert hash_message(message, format="STRING") == expected


# ---------------------------------------------------------------------------
# test_i18next_format_hashes_raw_message
#
# NEW in PR #1207: same raw-hash treatment for I18NEXT format templates.
#
# Example:
#     hash_message("Hello, {{name}}", format="I18NEXT")
#     # == hash_source("Hello, {{name}}", data_format="I18NEXT")   (raw)
# ---------------------------------------------------------------------------


def test_i18next_format_hashes_raw_message() -> None:
    """For I18NEXT format, the hash is computed over the RAW message — no index_vars."""
    message = "Hello, {{name}}"
    expected = hash_source(message, data_format="I18NEXT")
    assert hash_message(message, format="I18NEXT") == expected


# ---------------------------------------------------------------------------
# test_icu_vs_string_produce_different_hashes_for_same_template
#
# Pin: a template that looks identical as a source string must hash
# differently depending on its format, because the translation service
# interprets it differently (ICU var is placeholder-indexed; STRING var is
# literal). Prevents cross-format cache collisions.
# ---------------------------------------------------------------------------


def test_icu_vs_string_produce_different_hashes_for_same_template() -> None:
    """The same template hashed as ICU vs STRING must produce different keys."""
    message = "Hello, {name}!"

    icu_hash = hash_message(message, format="ICU")
    string_hash = hash_message(message, format="STRING")

    assert icu_hash != string_hash, (
        "ICU and STRING formats must produce different hashes — they are different wire representations of the template"
    )


# ---------------------------------------------------------------------------
# test_format_default_stays_icu_for_backward_compat
#
# Current Python API: ``hash_message(msg)`` has no ``format`` kwarg and always
# ICU-indexes. The port adds a ``format`` kwarg but the default stays "ICU"
# so existing callers don't break.
#
# Example:
#     # old code still works:
#     hash_message("Hello, {name}!")   # == hash_message("Hello, {name}!", format="ICU")
# ---------------------------------------------------------------------------


def test_format_default_stays_icu_for_backward_compat() -> None:
    """Calling hash_message without ``format`` defaults to ICU (preserves existing callers)."""
    message = "Hello, {name}!"
    assert hash_message(message) == hash_message(message, format="ICU")

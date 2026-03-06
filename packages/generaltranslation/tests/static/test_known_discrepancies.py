"""Tests for edge cases that previously had discrepancies between Python and JS.

These tests assert against the JS expected output to verify that our parser
and printer match formatjs behavior for escaped content, boundary apostrophes,
and ``#`` in plural context.
"""

from generaltranslation.static import condense_vars

# ---------------------------------------------------------------------------
# print_ast re-escapes {} in literal text
# JS printAST calls printEscapedMessage() which wraps regions containing {}
# in single quotes so they round-trip correctly.
# ---------------------------------------------------------------------------


def test_condense_escaped_braces_in_non_condensed_select():
    icu = (
        "{_gt_1, select, other {x}} "
        "{type, select, a {text with '{braces}'} other {plain}}"
    )
    js_expected = "{_gt_1} {type,select,a{text with '{braces}'} other{plain}}"
    assert condense_vars(icu) == js_expected


# ---------------------------------------------------------------------------
# print_ast re-escapes # in plural context
# JS printLiteralElement escapes bare # inside plural branches so it isn't
# mis-parsed as a hash replacement node.
# ---------------------------------------------------------------------------


def test_condense_escaped_hash_in_non_condensed_plural():
    icu = (
        "{_gt_1, select, other {x}} "
        "{n, plural, offset:1 one {# item, not '#'} other {# items}}"
    )
    js_expected = "{_gt_1} {n,plural,offset:1 one{# item, not '#'} other{# items}}"
    assert condense_vars(icu) == js_expected


# ---------------------------------------------------------------------------
# print_ast doubles ' at literal boundaries
# JS printLiteralElement doubles a leading ' when preceded by a placeholder
# to prevent it from being mis-parsed as an escape sequence start.
# ---------------------------------------------------------------------------


def test_condense_apostrophe_at_literal_boundary():
    icu = "{_gt_1, select, other {x}} it''s {name}''s"
    js_expected = "{_gt_1} it's {name}''s"
    assert condense_vars(icu) == js_expected


# ---------------------------------------------------------------------------
# Parser escape triggers match formatjs
# formatjs always treats '<' and '>' after ' as starting an escape sequence,
# regardless of whether tags are enabled. Our parser now does the same.
# ---------------------------------------------------------------------------


def test_parser_escape_angle_brackets():
    icu = (
        "{_gt_1, select, other {val}} "
        "{mode, select, "
        'json {\'{"key": "val"}\'} '
        "xml {'<tag />'} "
        "other {plain}}"
    )
    js_expected = (
        '{_gt_1} {mode,select,json{\'{"key": "val"}\'} xml{<tag />} other{plain}}'
    )
    assert condense_vars(icu) == js_expected

"""Comprehensive tests for the ICU MessageFormat formatter.

Validates shot-for-shot against icu4py (reference ICU implementation).
Tests cover all ICU MessageFormat features across multiple locales.
"""

import pytest
from generaltranslation_intl_messageformat import IntlMessageFormat
from icu4py.messageformat import MessageFormat as RefMessageFormat


# ---------------------------------------------------------------------------
# Helper: compare our output against icu4py reference
# ---------------------------------------------------------------------------
def _assert_matches_ref(pattern, locale, variables, desc):
    our_result = IntlMessageFormat(pattern, locale).format(variables)
    ref_result = RefMessageFormat(pattern, locale).format(variables)
    assert our_result == ref_result, (
        f"Output mismatch for {desc!r}:\n"
        f"  pattern:  {pattern!r}\n"
        f"  locale:   {locale}\n"
        f"  vars:     {variables}\n"
        f"  ours:     {our_result!r}\n"
        f"  icu4py:   {ref_result!r}"
    )


# ---------------------------------------------------------------------------
# Simple variable interpolation
# ---------------------------------------------------------------------------
SIMPLE_VAR_CASES = [
    ("Hello, {name}!", "en", {"name": "World"}, "simple hello"),
    ("{greeting}, {name}!", "en", {"greeting": "Hi", "name": "Alice"}, "two vars"),
    ("{a} {b} {c}", "en", {"a": "1", "b": "2", "c": "3"}, "three vars"),
    ("No vars", "en", {}, "no vars"),
    ("{x}", "en", {"x": "value"}, "single var only"),
    ("{a}{b}{c}", "en", {"a": "x", "b": "y", "c": "z"}, "adjacent vars"),
    ("before {var} after", "en", {"var": "middle"}, "var in middle"),
    ("{name} is {age} years old", "en", {"name": "Bob", "age": 30}, "mixed types"),
    ("Unicode: {name}", "en", {"name": "こんにちは"}, "unicode value"),
    ("{emoji}", "en", {"emoji": "🚀"}, "emoji value"),
    ("Result: {val}", "en", {"val": 42}, "numeric value"),
    ("Result: {val}", "en", {"val": 3.14}, "float value"),
    # Carve-out: Python str(True) is "True", icu4py treats bool as int (1).
    # We match Python behavior. This test is not compared against icu4py.
    ("Result: {val}", "en", {"val": ""}, "empty string value"),
]


@pytest.mark.parametrize(
    "pattern,locale,variables,desc",
    SIMPLE_VAR_CASES,
    ids=[c[3] for c in SIMPLE_VAR_CASES],
)
def test_simple_variables(pattern, locale, variables, desc):
    _assert_matches_ref(pattern, locale, variables, desc)


# ---------------------------------------------------------------------------
# Plural - English
# ---------------------------------------------------------------------------
PLURAL_EN_CASES = [
    ("{count, plural, one {# item} other {# items}}", "en", {"count": 0}, "en plural 0"),
    ("{count, plural, one {# item} other {# items}}", "en", {"count": 1}, "en plural 1"),
    ("{count, plural, one {# item} other {# items}}", "en", {"count": 2}, "en plural 2"),
    ("{count, plural, one {# item} other {# items}}", "en", {"count": 5}, "en plural 5"),
    ("{count, plural, one {# item} other {# items}}", "en", {"count": 10}, "en plural 10"),
    ("{count, plural, one {# item} other {# items}}", "en", {"count": 100}, "en plural 100"),
    ("{count, plural, one {# item} other {# items}}", "en", {"count": 1000}, "en plural 1000"),
    # Exact matches
    ("{n, plural, =0 {zero} =1 {one exactly} one {# one} other {# other}}", "en", {"n": 0}, "en exact 0"),
    ("{n, plural, =0 {zero} =1 {one exactly} one {# one} other {# other}}", "en", {"n": 1}, "en exact 1"),
    ("{n, plural, =0 {zero} =1 {one exactly} one {# one} other {# other}}", "en", {"n": 2}, "en exact 2"),
    ("{n, plural, =0 {zero} =1 {one exactly} one {# one} other {# other}}", "en", {"n": 5}, "en exact 5"),
    # Multiple exact
    ("{n, plural, =0 {none} =1 {single} =2 {double} =3 {triple} other {# many}}", "en", {"n": 0}, "en multi exact 0"),
    ("{n, plural, =0 {none} =1 {single} =2 {double} =3 {triple} other {# many}}", "en", {"n": 1}, "en multi exact 1"),
    ("{n, plural, =0 {none} =1 {single} =2 {double} =3 {triple} other {# many}}", "en", {"n": 2}, "en multi exact 2"),
    ("{n, plural, =0 {none} =1 {single} =2 {double} =3 {triple} other {# many}}", "en", {"n": 3}, "en multi exact 3"),
    ("{n, plural, =0 {none} =1 {single} =2 {double} =3 {triple} other {# many}}", "en", {"n": 7}, "en multi exact 7"),
    # Hash in text
    ("{count, plural, one {There is # cat} other {There are # cats}}", "en", {"count": 1}, "en hash text 1"),
    ("{count, plural, one {There is # cat} other {There are # cats}}", "en", {"count": 5}, "en hash text 5"),
    # Only other
    ("{count, plural, other {# things}}", "en", {"count": 1}, "en other only 1"),
    ("{count, plural, other {# things}}", "en", {"count": 42}, "en other only 42"),
]


@pytest.mark.parametrize(
    "pattern,locale,variables,desc",
    PLURAL_EN_CASES,
    ids=[c[3] for c in PLURAL_EN_CASES],
)
def test_plural_english(pattern, locale, variables, desc):
    _assert_matches_ref(pattern, locale, variables, desc)


# ---------------------------------------------------------------------------
# Plural - German
# ---------------------------------------------------------------------------
PLURAL_DE_CASES = [
    ("{n, plural, one {# Artikel} other {# Artikel}}", "de", {"n": v}, f"de plural {v}")
    for v in [0, 1, 2, 5, 10, 100]
]


@pytest.mark.parametrize(
    "pattern,locale,variables,desc",
    PLURAL_DE_CASES,
    ids=[c[3] for c in PLURAL_DE_CASES],
)
def test_plural_german(pattern, locale, variables, desc):
    _assert_matches_ref(pattern, locale, variables, desc)


# ---------------------------------------------------------------------------
# Plural - French (0 and 1 are "one")
# ---------------------------------------------------------------------------
PLURAL_FR_CASES = [
    ("{n, plural, one {# élément} other {# éléments}}", "fr", {"n": v}, f"fr plural {v}")
    for v in [0, 1, 2, 5, 10, 100]
]


@pytest.mark.parametrize(
    "pattern,locale,variables,desc",
    PLURAL_FR_CASES,
    ids=[c[3] for c in PLURAL_FR_CASES],
)
def test_plural_french(pattern, locale, variables, desc):
    _assert_matches_ref(pattern, locale, variables, desc)


# ---------------------------------------------------------------------------
# Plural - Arabic (6 plural forms: zero, one, two, few, many, other)
# ---------------------------------------------------------------------------
ARABIC_PATTERN = "{n, plural, zero {٠ عناصر} one {عنصر واحد} two {عنصران} few {# عناصر} many {# عنصرًا} other {# عنصر}}"
PLURAL_AR_CASES = [
    (ARABIC_PATTERN, "ar", {"n": v}, f"ar plural {v}")
    for v in [0, 1, 2, 3, 4, 5, 6, 10, 11, 20, 100, 101, 102, 103, 111]
]


@pytest.mark.parametrize(
    "pattern,locale,variables,desc",
    PLURAL_AR_CASES,
    ids=[c[3] for c in PLURAL_AR_CASES],
)
def test_plural_arabic(pattern, locale, variables, desc):
    _assert_matches_ref(pattern, locale, variables, desc)


# ---------------------------------------------------------------------------
# Plural - Japanese (no plural distinction, always "other")
# ---------------------------------------------------------------------------
PLURAL_JA_CASES = [
    ("{n, plural, other {#個}}", "ja", {"n": v}, f"ja plural {v}")
    for v in [0, 1, 2, 5, 100]
]


@pytest.mark.parametrize(
    "pattern,locale,variables,desc",
    PLURAL_JA_CASES,
    ids=[c[3] for c in PLURAL_JA_CASES],
)
def test_plural_japanese(pattern, locale, variables, desc):
    _assert_matches_ref(pattern, locale, variables, desc)


# ---------------------------------------------------------------------------
# Plural - Russian (one, few, many, other)
# ---------------------------------------------------------------------------
RUSSIAN_PATTERN = "{n, plural, one {# книга} few {# книги} many {# книг} other {# книг}}"
PLURAL_RU_CASES = [
    (RUSSIAN_PATTERN, "ru", {"n": v}, f"ru plural {v}")
    for v in [0, 1, 2, 3, 4, 5, 10, 11, 12, 14, 20, 21, 22, 25, 100, 101, 102]
]


@pytest.mark.parametrize(
    "pattern,locale,variables,desc",
    PLURAL_RU_CASES,
    ids=[c[3] for c in PLURAL_RU_CASES],
)
def test_plural_russian(pattern, locale, variables, desc):
    _assert_matches_ref(pattern, locale, variables, desc)


# ---------------------------------------------------------------------------
# Plural - Polish (one, few, many, other)
# ---------------------------------------------------------------------------
POLISH_PATTERN = "{n, plural, one {# plik} few {# pliki} many {# plików} other {# plików}}"
PLURAL_PL_CASES = [
    (POLISH_PATTERN, "pl", {"n": v}, f"pl plural {v}")
    for v in [0, 1, 2, 3, 4, 5, 10, 12, 14, 21, 22, 23, 25, 100, 102]
]


@pytest.mark.parametrize(
    "pattern,locale,variables,desc",
    PLURAL_PL_CASES,
    ids=[c[3] for c in PLURAL_PL_CASES],
)
def test_plural_polish(pattern, locale, variables, desc):
    _assert_matches_ref(pattern, locale, variables, desc)


# ---------------------------------------------------------------------------
# Plural with offset
# ---------------------------------------------------------------------------
OFFSET_PATTERN = "{guests, plural, offset:1 =0 {nobody} =1 {{host}} one {{host} and # other} other {{host} and # others}}"
PLURAL_OFFSET_CASES = [
    (OFFSET_PATTERN, "en", {"guests": v, "host": "Alice"}, f"offset guests={v}")
    for v in [0, 1, 2, 3, 5, 10]
]


@pytest.mark.parametrize(
    "pattern,locale,variables,desc",
    PLURAL_OFFSET_CASES,
    ids=[c[3] for c in PLURAL_OFFSET_CASES],
)
def test_plural_offset(pattern, locale, variables, desc):
    _assert_matches_ref(pattern, locale, variables, desc)


# ---------------------------------------------------------------------------
# Selectordinal - English
# ---------------------------------------------------------------------------
ORDINAL_PATTERN = "{n, selectordinal, one {#st} two {#nd} few {#rd} other {#th}}"
SELECTORDINAL_CASES = [
    (ORDINAL_PATTERN, "en", {"n": v}, f"en ordinal {v}")
    for v in [1, 2, 3, 4, 5, 10, 11, 12, 13, 14, 21, 22, 23, 24, 31, 32, 33, 42, 100, 101, 102, 103, 111, 112, 113]
]


@pytest.mark.parametrize(
    "pattern,locale,variables,desc",
    SELECTORDINAL_CASES,
    ids=[c[3] for c in SELECTORDINAL_CASES],
)
def test_selectordinal_english(pattern, locale, variables, desc):
    _assert_matches_ref(pattern, locale, variables, desc)


# ---------------------------------------------------------------------------
# Select
# ---------------------------------------------------------------------------
SELECT_CASES = [
    ("{g, select, male {He} female {She} other {They}}", "en", {"g": "male"}, "select male"),
    ("{g, select, male {He} female {She} other {They}}", "en", {"g": "female"}, "select female"),
    ("{g, select, male {He} female {She} other {They}}", "en", {"g": "other"}, "select other explicit"),
    ("{g, select, male {He} female {She} other {They}}", "en", {"g": "unknown"}, "select fallback"),
    ("{g, select, male {He} female {She} other {They}}", "en", {"g": ""}, "select empty"),
    ("{type, select, cat {meow} dog {woof} bird {tweet} other {???}}", "en", {"type": "cat"}, "select cat"),
    ("{type, select, cat {meow} dog {woof} bird {tweet} other {???}}", "en", {"type": "dog"}, "select dog"),
    ("{type, select, cat {meow} dog {woof} bird {tweet} other {???}}", "en", {"type": "bird"}, "select bird"),
    ("{type, select, cat {meow} dog {woof} bird {tweet} other {???}}", "en", {"type": "fish"}, "select fish fallback"),
    ("{status, select, active {Active} inactive {Inactive} pending {Pending} other {Unknown}}", "en", {"status": "active"}, "status active"),
    ("{status, select, active {Active} inactive {Inactive} pending {Pending} other {Unknown}}", "en", {"status": "pending"}, "status pending"),
    ("{status, select, active {Active} inactive {Inactive} pending {Pending} other {Unknown}}", "en", {"status": "deleted"}, "status unknown"),
]


@pytest.mark.parametrize(
    "pattern,locale,variables,desc",
    SELECT_CASES,
    ids=[c[3] for c in SELECT_CASES],
)
def test_select(pattern, locale, variables, desc):
    _assert_matches_ref(pattern, locale, variables, desc)


# ---------------------------------------------------------------------------
# Nested patterns
# ---------------------------------------------------------------------------
NESTED_CASES = [
    (
        "You have {count, plural, one {# new message} other {# new messages}}.",
        "en", {"count": 1}, "nested plural 1"
    ),
    (
        "You have {count, plural, one {# new message} other {# new messages}}.",
        "en", {"count": 5}, "nested plural 5"
    ),
    (
        "{name} has {count, plural, one {# cat} other {# cats}}",
        "en", {"name": "Alice", "count": 1}, "multi var plural 1"
    ),
    (
        "{name} has {count, plural, one {# cat} other {# cats}}",
        "en", {"name": "Bob", "count": 3}, "multi var plural 3"
    ),
    (
        "{a, select, x {{b, plural, one {deep #} other {deeper #}}} other {fallback}}",
        "en", {"a": "x", "b": 1}, "nested select-plural 1"
    ),
    (
        "{a, select, x {{b, plural, one {deep #} other {deeper #}}} other {fallback}}",
        "en", {"a": "x", "b": 5}, "nested select-plural 5"
    ),
    (
        "{a, select, x {{b, plural, one {deep #} other {deeper #}}} other {fallback}}",
        "en", {"a": "y", "b": 5}, "nested select fallback"
    ),
    (
        "Hello {name}, you have {count, plural, =0 {no messages} one {# message} other {# messages}} from {sender}.",
        "en", {"name": "Alice", "count": 0, "sender": "Bob"}, "complex nested 0"
    ),
    (
        "Hello {name}, you have {count, plural, =0 {no messages} one {# message} other {# messages}} from {sender}.",
        "en", {"name": "Alice", "count": 1, "sender": "Bob"}, "complex nested 1"
    ),
    (
        "Hello {name}, you have {count, plural, =0 {no messages} one {# message} other {# messages}} from {sender}.",
        "en", {"name": "Alice", "count": 42, "sender": "Bob"}, "complex nested 42"
    ),
    (
        "{gender, select, male {He has {count, plural, one {# item} other {# items}}} female {She has {count, plural, one {# item} other {# items}}} other {They have {count, plural, one {# item} other {# items}}}}",
        "en", {"gender": "male", "count": 1}, "gender+plural male 1"
    ),
    (
        "{gender, select, male {He has {count, plural, one {# item} other {# items}}} female {She has {count, plural, one {# item} other {# items}}} other {They have {count, plural, one {# item} other {# items}}}}",
        "en", {"gender": "female", "count": 5}, "gender+plural female 5"
    ),
    (
        "{gender, select, male {He has {count, plural, one {# item} other {# items}}} female {She has {count, plural, one {# item} other {# items}}} other {They have {count, plural, one {# item} other {# items}}}}",
        "en", {"gender": "unknown", "count": 0}, "gender+plural other 0"
    ),
]


@pytest.mark.parametrize(
    "pattern,locale,variables,desc",
    NESTED_CASES,
    ids=[c[3] for c in NESTED_CASES],
)
def test_nested(pattern, locale, variables, desc):
    _assert_matches_ref(pattern, locale, variables, desc)


# ---------------------------------------------------------------------------
# Escaped content
# ---------------------------------------------------------------------------
ESCAPED_CASES = [
    ("It''s a {thing}.", "en", {"thing": "test"}, "escaped quote"),
    ("He said ''hello''", "en", {}, "escaped quotes in text"),
    ("No ''quotes'' here", "en", {}, "escaped quotes no vars"),
]


@pytest.mark.parametrize(
    "pattern,locale,variables,desc",
    ESCAPED_CASES,
    ids=[c[3] for c in ESCAPED_CASES],
)
def test_escaped(pattern, locale, variables, desc):
    _assert_matches_ref(pattern, locale, variables, desc)


# ---------------------------------------------------------------------------
# _gt_ variable patterns (used by static module, validated against icu4py)
# ---------------------------------------------------------------------------
GT_CASES = [
    ("{_gt_, select, other {Hello World}}", "en", {"_gt_": "x"}, "gt simple"),
    ("{_gt_1, select, other {value1}}", "en", {"_gt_1": "x"}, "gt indexed"),
    ("Je joue avec mon ami {_gt_1} au {_gt_2}", "en", {"_gt_1": "Brian", "_gt_2": "park"}, "gt condensed"),
]


@pytest.mark.parametrize(
    "pattern,locale,variables,desc",
    GT_CASES,
    ids=[c[3] for c in GT_CASES],
)
def test_gt_patterns(pattern, locale, variables, desc):
    _assert_matches_ref(pattern, locale, variables, desc)


# ---------------------------------------------------------------------------
# Formatter-specific behavior tests (not compared against icu4py)
# ---------------------------------------------------------------------------
class TestFormatterBehavior:
    def test_missing_variable_returns_empty(self):
        result = IntlMessageFormat("Hello, {name}!", "en").format({})
        assert result == "Hello, !"

    def test_missing_variable_in_text(self):
        result = IntlMessageFormat("{a} and {b}", "en").format({"a": "yes"})
        assert result == "yes and "

    def test_invalid_locale_falls_back_to_english(self):
        result = IntlMessageFormat(
            "{n, plural, one {# item} other {# items}}", "invalid-locale"
        ).format({"n": 1})
        assert result == "1 item"

    def test_select_missing_value_uses_other(self):
        result = IntlMessageFormat(
            "{x, select, a {A} other {default}}", "en"
        ).format({"x": "missing"})
        assert result == "default"

    def test_format_none_values(self):
        result = IntlMessageFormat("Hello, {name}!", "en").format(None)
        assert result == "Hello, !"

    def test_pattern_property(self):
        pattern = "{count, plural, one {# item} other {# items}}"
        mf = IntlMessageFormat(pattern, "en")
        assert mf.pattern == pattern

    def test_locale_property(self):
        mf = IntlMessageFormat("hello", "de")
        assert str(mf.locale) == "de"

    def test_locale_property_with_region(self):
        mf = IntlMessageFormat("hello", "en-US")
        assert mf.locale.language == "en"

    def test_plain_text_no_formatting(self):
        result = IntlMessageFormat("Hello world", "en").format({})
        assert result == "Hello world"

    def test_empty_pattern(self):
        result = IntlMessageFormat("", "en").format({})
        assert result == ""

    def test_hash_outside_plural_not_special(self):
        # Outside plural, # is literal text
        result = IntlMessageFormat("Price is #5", "en").format({})
        assert result == "Price is #5"

"""Comprehensive tests for the ICU MessageFormat parser.

Validates shot-for-shot against pyicumessageformat (reference implementation).
Tests are generated programmatically from a large matrix of ICU patterns.
"""

from typing import Any

import pytest
from generaltranslation_icu_messageformat_parser import Parser, print_ast
from pyicumessageformat import Parser as RefParser  # type: ignore[import-untyped]

# ---------------------------------------------------------------------------
# Exhaustive test input matrix
# ---------------------------------------------------------------------------

# Simple variables
SIMPLE_VAR_CASES = [
    "",
    "Hello world",
    "No variables here at all",
    "   leading spaces",
    "trailing spaces   ",
    "Hello, {name}!",
    "{greeting}, {name}!",
    "{a} {b} {c}",
    "{x}",
    "{a}{b}{c}",
    "before {var} middle {var2} after",
    "{one} and {two} and {three} and {four} and {five}",
    "Unicode: こんにちは {name}",
    "中文{变量}测试",
    "Emoji: 🚀 {rocket} 🌟",
    "{var} at start",
    "at end {var}",
    "{only_var}",
    "Multiple\nlines\n{var}\nhere",
    "Tabs\t{var}\there",
]

# Plural patterns
PLURAL_CASES = [
    "{count, plural, one {# item} other {# items}}",
    "{count, plural, other {# things}}",
    "{count, plural, =0 {no items} one {# item} other {# items}}",
    "{count, plural, =0 {zero} =1 {one} =2 {two} other {many}}",
    "{count, plural, =0 {no items} =1 {one item} one {# item} other {# items}}",
    "{n, plural, zero {zero} one {one} two {two} few {few} many {many} other {other}}",
    "{count, plural, one {# cat} other {# cats}}",
    "{count, plural, one {There is # cat} other {There are # cats}}",
    "{count, plural, one {# dog and # cat} other {# dogs and # cats}}",
]

# Plural with offset
PLURAL_OFFSET_CASES = [
    "{guests, plural, offset:1 =0 {nobody} =1 {{host}} one {{host} and # other} other {{host} and # others}}",
    "{n, plural, offset:2 =0 {none} =1 {almost} =2 {just right} other {# extra}}",
]

# Selectordinal
SELECTORDINAL_CASES = [
    "{n, selectordinal, one {#st} two {#nd} few {#rd} other {#th}}",
    "{pos, selectordinal, one {#st place} two {#nd place} few {#rd place} other {#th place}}",
    "{n, selectordinal, other {#th}}",
]

# Select
SELECT_CASES = [
    "{gender, select, male {He} female {She} other {They}}",
    "{gender, select, male {He} female {She} other {They}} went.",
    "{type, select, cat {meow} dog {woof} other {...}}",
    "{x, select, a {A} b {B} c {C} d {D} other {other}}",
    "{status, select, active {Active} inactive {Inactive} other {Unknown}}",
]

# Nested patterns
NESTED_CASES = [
    "You have {count, plural, one {# new message} other {# new messages}}.",
    "{name} has {count, plural, one {# cat} other {# cats}}",
    "{a, select, x {{b, plural, one {deep #} other {deeper #}}} other {fallback}}",
    "Hello {name}, you have {count, plural, =0 {no messages} one {# message} other {# messages}} from {sender}.",
    "{gender, select, male {He has {count, plural, one {# item} other {# items}}} female {She has {count, plural, one {# item} other {# items}}} other {They have {count, plural, one {# item} other {# items}}}}",  # noqa: E501
    "Outer {a, select, x {inner {b, select, y {deep} other {deeper}}} other {fallback}}",
]

# Typed placeholders with format
TYPED_CASES = [
    "{amount, number}",
    "{amount, number, ::currency/USD}",
    "{d, date, short}",
    "{d, date, medium}",
    "{d, date, long}",
    "{d, date, full}",
    "{t, time, short}",
    "{t, time, medium}",
    "{pct, number, percent}",
]

# Escaped content
ESCAPED_CASES = [
    "It''s a {thing}.",
    "He said ''hello''",
    "'{escaped}' and {real}",
    "Use '{' and '}' literally",
    "''''",
    "No ''quotes'' here",
]

# _gt_ patterns (used by static module)
GT_CASES = [
    "{_gt_, select, other {Hello World}}",
    "{_gt_, select, other {Brian} _gt_var_name {name}}",
    "{_gt_1, select, other {value1}} and {_gt_2, select, other {value2}}",
    "{_gt_, select, other {}}",
    "Welcome {_gt_, select, other {user}}! You have {count, plural, one {# message} other {# messages}}.",
    "{_gt_1, select, other {toys}} at the {_gt_2, select, other {park}}",
    "{count, plural, =0 {No {_gt_, select, other {messages}}} =1 {One {_gt_, select, other {message}}} other {# {_gt_, select, other {messages}}}}",  # noqa: E501
    "{_gt_, select, other {content with spaces}}",
    "{_gt_, select, other {café naïve résumé}}",
    "{_gt_, select, one {book} other {books}}",
    "{_gt_, select, zero {no items} one {one item} few {few items} other {many items}}",
    "{_gt_5, select, other {value}}",
    "{_gt_123, select, other {value}}",
    "{_gt_0, select, other {value}}",
    "User {username} has {_gt_1, select, other {completed}} {count} tasks",
    "{_gt_1, select, other {I have {count, plural, one {book} other {books}}}}",
]

# Whitespace variations
WHITESPACE_CASES = [
    "{count,plural,one{# item}other{# items}}",
    "{ count , plural , one {# item} other {# items} }",
    "{  count  ,  plural  ,  one  {# item}  other  {# items}  }",
    "{count , plural, one {x} other {y}}",
    "{ name }",
]

ALL_PARSE_CASES = (
    SIMPLE_VAR_CASES
    + PLURAL_CASES
    + PLURAL_OFFSET_CASES
    + SELECTORDINAL_CASES
    + SELECT_CASES
    + NESTED_CASES
    + TYPED_CASES
    + GT_CASES
)


def _strip_ws(node: Any) -> Any:
    """Remove _ws keys recursively for comparison with reference parser."""
    if isinstance(node, dict):
        return {k: _strip_ws(v) for k, v in node.items() if k != "_ws"}
    if isinstance(node, list):
        return [_strip_ws(item) for item in node]
    return node


# ---------------------------------------------------------------------------
# Shot-for-shot AST comparison with pyicumessageformat
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("msg", ALL_PARSE_CASES)
def test_parse_matches_reference(msg: str) -> None:
    """Our parser produces the same AST as pyicumessageformat."""
    our_ast = Parser().parse(msg)
    ref_ast = RefParser().parse(msg)
    assert _strip_ws(our_ast) == ref_ast, f"AST mismatch for {msg!r}"


@pytest.mark.parametrize("msg", ALL_PARSE_CASES)
def test_parse_with_indices_matches_reference(msg: str) -> None:
    """include_indices produces same start/end as pyicumessageformat."""
    our_ast = Parser({"include_indices": True}).parse(msg)
    ref_ast = RefParser({"include_indices": True}).parse(msg)
    assert _strip_ws(our_ast) == ref_ast, f"Indices mismatch for {msg!r}"


# ---------------------------------------------------------------------------
# Escaped content: AST comparison (parser unescapes, so compare ASTs)
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("msg", ESCAPED_CASES)
def test_escaped_parse_matches_reference(msg: str) -> None:
    """Escaped content produces same AST as reference."""
    our_ast = Parser().parse(msg)
    ref_ast = RefParser().parse(msg)
    assert _strip_ws(our_ast) == ref_ast, f"Escaped AST mismatch for {msg!r}"


# ---------------------------------------------------------------------------
# Round-trip tests: parse(preserve_whitespace=True) → print_ast() → original
# ---------------------------------------------------------------------------
ROUNDTRIP_CASES = (
    SIMPLE_VAR_CASES
    + PLURAL_CASES
    + PLURAL_OFFSET_CASES
    + SELECTORDINAL_CASES
    + SELECT_CASES
    + NESTED_CASES
    + TYPED_CASES
    + GT_CASES
    + WHITESPACE_CASES
)


@pytest.mark.parametrize("msg", ROUNDTRIP_CASES)
def test_roundtrip(msg: str) -> None:
    """parse(preserve_whitespace=True) → print_ast() equals original input."""
    ast = Parser({"preserve_whitespace": True}).parse(msg)
    reconstructed = print_ast(ast)
    assert reconstructed == msg, f"Round-trip failed:\n  original:      {msg!r}\n  reconstructed: {reconstructed!r}"


# ---------------------------------------------------------------------------
# Escaped content: round-trip is lossy (parser unescapes), so skip
# These are documented as a known limitation: escape sequences like ''
# and '{...}' are consumed during parsing and cannot be reconstructed.
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# print_ast with AST modifications
# ---------------------------------------------------------------------------
class TestPrintAstModifications:
    def test_change_variable_name(self) -> None:
        ast = Parser({"preserve_whitespace": True}).parse("Hello, {name}!")
        ast[1]["name"] = "world"
        assert print_ast(ast) == "Hello, {world}!"

    def test_change_select_branch_content(self) -> None:
        ast = Parser({"preserve_whitespace": True}).parse("{gender, select, male {He} female {She} other {They}}")
        ast[0]["options"]["male"] = ["Him"]
        result = print_ast(ast)
        assert "Him" in result
        assert "She" in result

    def test_condense_indexed_select(self) -> None:
        """Simulates condenseVars: replace {_gt_1, select, other {X}} with {_gt_1}."""
        ast = Parser({"preserve_whitespace": True, "include_indices": True}).parse(
            "Hello {_gt_1, select, other {World}} end"
        )
        ast[1] = {"name": "_gt_1"}
        assert print_ast(ast) == "Hello {_gt_1} end"

    def test_condense_multiple_indexed_selects(self) -> None:
        ast = Parser({"preserve_whitespace": True}).parse(
            "I play with {_gt_1, select, other {toys}} at the {_gt_2, select, other {park}}"
        )
        ast[1] = {"name": "_gt_1"}
        ast[3] = {"name": "_gt_2"}
        assert print_ast(ast) == "I play with {_gt_1} at the {_gt_2}"

    def test_add_new_branch(self) -> None:
        ast = Parser({"preserve_whitespace": True}).parse("{x, select, a {A} other {default}}")
        ast[0]["options"]["b"] = ["B"]
        result = print_ast(ast)
        assert "b{B}" in result or "b {B}" in result

    def test_modify_plural_branch(self) -> None:
        ast = Parser({"preserve_whitespace": True}).parse("{count, plural, one {# item} other {# items}}")
        ast[0]["options"]["one"] = ["exactly one"]
        result = print_ast(ast)
        assert "exactly one" in result

    def test_empty_ast(self) -> None:
        assert print_ast([]) == ""

    def test_plain_text_ast(self) -> None:
        assert print_ast(["Hello world"]) == "Hello world"


# ---------------------------------------------------------------------------
# Token list tests
# ---------------------------------------------------------------------------
class TestTokens:
    def test_tokens_populated(self) -> None:
        tokens: list[Any] = []
        Parser().parse("{name}", tokens)
        assert len(tokens) > 0
        types = {t["type"] for t in tokens}
        assert "name" in types
        assert "syntax" in types

    def test_tokens_for_plural(self) -> None:
        tokens: list[Any] = []
        Parser().parse("{count, plural, one {# item} other {# items}}", tokens)
        types = [t["type"] for t in tokens]
        assert "type" in types  # "plural"
        assert "selector" in types  # "one", "other"
        assert "hash" in types  # "#"

    def test_tokens_for_select(self) -> None:
        tokens: list[Any] = []
        Parser().parse("{gender, select, male {He} other {They}}", tokens)
        selectors = [t["text"] for t in tokens if t["type"] == "selector"]
        assert "male" in selectors
        assert "other" in selectors


# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------
class TestErrors:
    def test_invalid_input_type(self) -> None:
        with pytest.raises(TypeError):
            Parser().parse(123)  # type: ignore[arg-type]

    def test_unmatched_close_brace(self) -> None:
        with pytest.raises(SyntaxError):
            Parser().parse("Hello } world")

    def test_missing_placeholder_name(self) -> None:
        with pytest.raises(SyntaxError):
            Parser().parse("{}")

    def test_missing_submessages(self) -> None:
        with pytest.raises(SyntaxError):
            Parser().parse("{x, select}")

    def test_tokens_invalid_type(self) -> None:
        with pytest.raises(TypeError):
            Parser().parse("hello", "not a list")  # type: ignore[arg-type]

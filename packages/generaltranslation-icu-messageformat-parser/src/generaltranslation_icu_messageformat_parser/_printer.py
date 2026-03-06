"""AST to ICU MessageFormat string reconstruction.

Reconstructs an ICU MessageFormat string from an AST produced by
:class:`Parser`. When the AST contains ``_ws`` whitespace metadata
(from ``preserve_whitespace=True``), the reconstruction is lossless.
Otherwise, normalized whitespace (single spaces) is used.
"""

from __future__ import annotations

import re

from . import _constants as constants

_BRACE_RE = re.compile(r"([{}](?:[\s\S]*[{}])?)")


def print_ast(ast: list) -> str:
    """Reconstruct an ICU MessageFormat string from an AST.

    Args:
        ast: The AST as returned by :meth:`Parser.parse`.

    Returns:
        The reconstructed ICU MessageFormat string.
    """
    return _print_nodes(ast)


def _escape_message(message: str) -> str:
    """Wrap the first region containing ``{`` or ``}`` in single quotes.

    Port of JS ``printEscapedMessage``.
    """
    return _BRACE_RE.sub(r"'\1'", message, count=1)


def _print_literal(value: str, is_in_plural: bool, is_first: bool, is_last: bool) -> str:
    """Re-escape a literal text node for safe ICU round-tripping.

    Port of JS ``printLiteralElement``.
    """
    escaped = value

    # Double leading ' when not first element (prevents mis-parse after })
    if not is_first and escaped and escaped[0] == "'":
        escaped = "''" + escaped[1:]

    # Double trailing ' when not last element (prevents mis-parse before {)
    if not is_last and escaped and escaped[-1] == "'":
        escaped = escaped[:-1] + "''"

    # Re-escape {} regions
    escaped = _escape_message(escaped)

    # Re-escape # in plural context
    if is_in_plural:
        escaped = escaped.replace("#", "'#'")

    return escaped


def _print_nodes(nodes: list, is_in_plural: bool = False) -> str:
    parts: list[str] = []
    for i, node in enumerate(nodes):
        if isinstance(node, str):
            parts.append(_print_literal(node, is_in_plural, i == 0, i == len(nodes) - 1))
        elif isinstance(node, dict):
            parts.append(_print_node(node))
    return "".join(parts)


def _print_node(node: dict) -> str:
    ws = node.get("_ws", {})

    # Hash replacement node (#)
    if node.get("hash"):
        return constants.CHAR_HASH

    name = node.get("name", "")
    node_type = node.get("type")

    # Tag node
    if node_type == "tag" or (node_type and node.get("contents") is not None):
        contents = node.get("contents", [])
        return (
            constants.CHAR_TAG_OPEN
            + name
            + constants.CHAR_TAG_END
            + _print_nodes(contents)
            + constants.TAG_END
            + name
            + constants.CHAR_TAG_END
        )

    # Simple variable: {name}
    if node_type is None and "options" not in node and "format" not in node:
        before = ws.get("before_name", "")
        after = ws.get("after_name", "")
        return constants.CHAR_OPEN + before + name + after + constants.CHAR_CLOSE

    # Typed placeholder
    # JS printAST uses no spaces after commas for select/plural but spaces
    # for simple format types (number, date, time).
    has_options = "options" in node
    default_sep = "" if has_options else " "

    before_name = ws.get("before_name", "")
    after_name = ws.get("after_name", "")
    after_type_sep = ws.get("after_type_sep", default_sep)
    after_type = ws.get("after_type", "")
    after_style_sep = ws.get("after_style_sep", default_sep)
    before_close = ws.get("before_close", "")

    result = constants.CHAR_OPEN + before_name + name + after_name

    if node_type:
        result += constants.CHAR_SEP + after_type_sep + node_type + after_type

    # Format string (e.g. {n, number, ::currency/USD})
    if "format" in node:
        result += constants.CHAR_SEP + after_style_sep + node["format"]
        result += before_close + constants.CHAR_CLOSE
        return result

    # Submessages (plural, select, selectordinal)
    if "options" in node:
        result += constants.CHAR_SEP + after_style_sep

        # Offset for plural/selectordinal
        offset = node.get("offset", 0)
        if offset:
            result += f"offset:{offset} "

        options = node["options"]
        options_ws = options.get("_ws", {}) if isinstance(options.get("_ws"), dict) else {}

        child_in_plural = node_type in ("plural", "selectordinal")

        first = True
        for key, value in options.items():
            if key == "_ws":
                continue

            selector_ws = options_ws.get(key, {})
            before_sel = selector_ws.get("before_selector", "" if first else " ")
            after_sel = selector_ws.get("after_selector", "")

            if not first:
                result += before_sel
            else:
                first = False

            result += key + after_sel
            result += constants.CHAR_OPEN
            if isinstance(value, list):
                result += _print_nodes(value, is_in_plural=child_in_plural)
            result += constants.CHAR_CLOSE

        result += before_close + constants.CHAR_CLOSE
        return result

    result += before_close + constants.CHAR_CLOSE
    return result

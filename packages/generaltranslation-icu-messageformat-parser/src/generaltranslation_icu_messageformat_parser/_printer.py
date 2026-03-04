"""AST to ICU MessageFormat string reconstruction.

Reconstructs an ICU MessageFormat string from an AST produced by
:class:`Parser`. When the AST contains ``_ws`` whitespace metadata
(from ``preserve_whitespace=True``), the reconstruction is lossless.
Otherwise, normalized whitespace (single spaces) is used.
"""

from __future__ import annotations

from . import _constants as constants


def print_ast(ast: list) -> str:
    """Reconstruct an ICU MessageFormat string from an AST.

    Args:
        ast: The AST as returned by :meth:`Parser.parse`.

    Returns:
        The reconstructed ICU MessageFormat string.
    """
    return _print_nodes(ast)


def _print_nodes(nodes: list) -> str:
    parts: list[str] = []
    for node in nodes:
        if isinstance(node, str):
            parts.append(node)
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
    before_name = ws.get("before_name", "")
    after_name = ws.get("after_name", "")
    after_type_sep = ws.get("after_type_sep", " ")
    after_type = ws.get("after_type", "")
    after_style_sep = ws.get("after_style_sep", " ")
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
                result += _print_nodes(value)
            result += constants.CHAR_CLOSE

        result += before_close + constants.CHAR_CLOSE
        return result

    result += before_close + constants.CHAR_CLOSE
    return result

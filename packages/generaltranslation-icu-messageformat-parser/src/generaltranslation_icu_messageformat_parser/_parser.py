"""ICU MessageFormat parser.

Derived from pyicumessageformat by Mike deBeaubien (MIT).
Enhanced with whitespace-preserving AST support.
"""

from __future__ import annotations

from typing import cast

from . import _constants as constants

SEP_OR_CLOSE = f"{constants.CHAR_SEP} or {constants.CHAR_CLOSE}"


def _append_token(context: dict, type: str, text: str) -> None:
    if "tokens" in context:
        context["tokens"].append({"type": type, "text": text})


def _is_alpha(char: str) -> bool:
    if not char:
        return False
    code = ord(char)
    return (97 <= code <= 122) or (65 <= code <= 90)


def _is_digit(char: str) -> bool:
    if not char:
        return False
    code = ord(char)
    return 0x30 <= code <= 0x39


def _is_space(char: str) -> bool:
    if not char:
        return False
    code = ord(char)
    return code in constants.SPACE_CHARS or (0x09 <= code <= 0x0D) or (0x2000 <= code <= 0x200D)


def _skip_space(context: dict, ret: bool = False) -> str:
    msg = context["msg"]
    length = context["length"]
    start = context["i"]
    if start >= length:
        return ""

    while context["i"] < length and _is_space(msg[context["i"]]):
        context["i"] += 1

    captured = msg[start : context["i"]]
    if ret:
        return captured
    elif start < context["i"]:
        _append_token(context, "space", captured)
    return captured


def _recursion(context: dict) -> SyntaxError:
    return SyntaxError(f"Too much recursion at position {context['i']}")


def _unexpected(char: str | dict[str, object], index: int | None = None) -> SyntaxError:
    if isinstance(char, dict):
        idx = cast(int, char["i"])
        msg = cast(str, char["msg"])
        length = cast(int, char["length"])
        c = msg[idx] if idx < length else "<EOF>"
        return _unexpected(c, idx)
    return SyntaxError(f'Unexpected "{char}" at position {index}')


def _expected(char: str, found: str | dict[str, object] | None, index: int | None = None) -> SyntaxError:
    if isinstance(found, dict):
        idx = cast(int, found["i"])
        msg = cast(str, found["msg"])
        length = cast(int, found["length"])
        f = msg[idx] if idx < length else "<EOF>"
        return _expected(char, f, idx)
    return SyntaxError(f'Expected {char} at position {index} but found "{found if found else "<EOF>"}"')


class Parser:
    """ICU MessageFormat parser.

    Parses ICU MessageFormat strings into ASTs (list of dicts/strings).

    Args:
        options: Parser configuration dict. Supported keys:

            - ``subnumeric_types``: Types that support ``#`` (default: ``['plural', 'selectordinal']``)
            - ``submessage_types``: Types with sub-messages (default: ``['plural', 'selectordinal', 'select']``)
            - ``maximum_depth``: Max nesting depth (default: ``50``)
            - ``allow_tags``: Enable XML-style tag parsing (default: ``False``)
            - ``strict_tags``: Strict tag parsing mode (default: ``False``)
            - ``tag_prefix``: Required tag name prefix (default: ``None``)
            - ``tag_type``: AST node type for tags (default: ``'tag'``)
            - ``include_indices``: Include ``start``/``end`` in AST nodes (default: ``False``)
            - ``loose_submessages``: Allow loose submessage parsing (default: ``False``)
            - ``allow_format_spaces``: Allow spaces in format strings (default: ``True``)
            - ``require_other``: Require ``other`` branch (default: ``True``)
            - ``preserve_whitespace``: Store whitespace in ``_ws`` dict on AST nodes (default: ``False``)
    """

    def __init__(self, options: dict | None = None) -> None:
        self.options = {
            "subnumeric_types": ["plural", "selectordinal"],
            "submessage_types": ["plural", "selectordinal", "select"],
            "maximum_depth": 50,
            "allow_tags": False,
            "strict_tags": False,
            "tag_prefix": None,
            "tag_type": "tag",
            "include_indices": False,
            "loose_submessages": False,
            "allow_format_spaces": True,
            "require_other": True,
            "preserve_whitespace": False,
        }
        if isinstance(options, dict):
            self.options.update(options)

    def parse(self, input: str, tokens: list | None = None) -> list:
        """Parse an ICU MessageFormat string into an AST.

        Args:
            input: The ICU MessageFormat string to parse.
            tokens: Optional list to populate with token objects.

        Returns:
            A list of AST nodes (strings and dicts).
        """
        if not isinstance(input, str):
            raise TypeError("input must be string")

        context = {
            "msg": input,
            "length": len(input),
            "i": 0,
            "depth": 0,
        }

        if tokens is not None:
            if not isinstance(tokens, list):
                raise TypeError("tokens must be list or None")
            context["tokens"] = tokens

        try:
            return self._parse_ast(context, None)
        except RecursionError:
            raise _recursion(context)
        except IndexError:
            raise SyntaxError

    def _parse_ast(self, context: dict, parent: dict | None) -> list:
        msg = context["msg"]
        length = context["length"]
        start = context["i"]
        out: list = []

        text = self._parse_text(context, parent)
        if text:
            out.append(text)
            _append_token(context, "text", msg[start : context["i"]])

        while context["i"] < length:
            i = context["i"]
            char = msg[i]
            if char == constants.CHAR_CLOSE:
                if not parent:
                    raise _unexpected(context)
                break

            if (
                parent
                and self.options["allow_tags"]
                and msg[i : i + len(constants.TAG_END)] == constants.TAG_END
                and self._can_read_tag(context, parent, True)
            ):
                break

            out.append(self._parse_placeholder(context, parent))
            start = context["i"]
            text = self._parse_text(context, parent)
            if text:
                out.append(text)
                _append_token(context, "text", msg[start : context["i"]])

        return out

    def _can_read_tag(self, context: dict, parent: dict | None, require_closing: bool = False) -> bool:
        msg = context["msg"]
        length = context["length"]
        current = context["i"]
        if not self.options["allow_tags"]:
            return False

        char = msg[current] if current < length else None
        if char != constants.CHAR_TAG_OPEN:
            return False

        if self.options["strict_tags"] and not require_closing:
            return True

        current += 1
        char = msg[current] if current < length else None

        if char == constants.CHAR_TAG_CLOSE:
            if self.options["strict_tags"]:
                return True
            current += 1
            char = msg[current] if current < length else None
        elif require_closing:
            return False

        if self.options["tag_prefix"]:
            prefix = cast(str, self.options["tag_prefix"])
            return prefix == msg[current : current + len(prefix)]
        elif char is not None and _is_alpha(char):
            return True

        return False

    def _parse_text(
        self,
        context: dict,
        parent: dict | None,
        is_arg_style: bool = False,
    ) -> str:
        msg = context["msg"]
        length = context["length"]
        start = context["i"]
        is_hash_special = parent and parent["type"] in self.options["subnumeric_types"]  # type: ignore[operator]
        is_tag_special = self.options["allow_tags"]
        allow_arg_spaces = self.options["allow_format_spaces"]

        text = ""
        trailing_space = 0

        while context["i"] < length:
            char = msg[context["i"]]
            is_sp = _is_space(char)

            if (
                char in constants.VAR_CHARS
                or (is_hash_special and char == constants.CHAR_HASH)
                or (is_tag_special and char == constants.CHAR_TAG_OPEN and self._can_read_tag(context, parent))
                or (is_arg_style and not allow_arg_spaces and is_sp)
            ):
                break

            if is_sp:
                trailing_space += 1
            else:
                trailing_space = 0

            if char == constants.CHAR_ESCAPE:
                context["i"] += 1
                if context["i"] < length:
                    char = msg[context["i"]]
                    if char == constants.CHAR_ESCAPE:
                        text += char
                        context["i"] += 1
                    elif (
                        char in constants.VAR_CHARS
                        or (is_hash_special and char == constants.CHAR_HASH)
                        or char == constants.CHAR_TAG_OPEN
                        or char == constants.CHAR_TAG_END
                        or is_arg_style
                    ):
                        text += char
                        context["i"] += 1
                        while context["i"] < length:
                            nxt = msg[context["i"]]
                            if nxt == constants.CHAR_ESCAPE:
                                context["i"] += 1
                                if context["i"] < length and msg[context["i"]] == constants.CHAR_ESCAPE:
                                    text += nxt
                                else:
                                    break
                            else:
                                text += nxt
                            context["i"] += 1
                    else:
                        context["i"] += 1
                        text += constants.CHAR_ESCAPE + char
                else:
                    text += char
            else:
                text += char
                context["i"] += 1

        if is_arg_style and trailing_space:
            trimmed = len(text) - trailing_space
            if trimmed <= 0:
                context["i"] = start
                return ""
            else:
                context["i"] -= trailing_space
                return text[:trimmed]

        return text

    def _token_indices(self, token: dict, start: int, end: int) -> dict:
        if self.options["include_indices"]:
            token["start"] = start
            token["end"] = end
        return token

    def _parse_placeholder(self, context: dict, parent: dict | None) -> dict:
        msg = context["msg"]
        length = context["length"]
        preserve_ws = bool(self.options["preserve_whitespace"])
        is_hash_special = parent and parent["type"] in self.options["subnumeric_types"]  # type: ignore[operator]

        start_idx = context["i"]
        char = msg[start_idx] if start_idx < length else None
        if is_hash_special and char == constants.CHAR_HASH:
            _append_token(context, "hash", char)
            context["i"] += 1
            assert parent is not None
            return self._token_indices(
                {"type": "number", "name": parent["name"], "hash": True},
                start_idx,
                context["i"],
            )

        tag = self._parse_tag(context, parent)
        if tag:
            return tag

        if char != constants.CHAR_OPEN:
            raise _expected(constants.CHAR_OPEN, context)

        _append_token(context, "syntax", char)
        context["i"] += 1

        ws: dict = {}
        ws_before_name = _skip_space(context, ret=preserve_ws)
        if preserve_ws:
            ws["before_name"] = ws_before_name

        name = self._parse_name(context)
        if not name:
            raise _expected("placeholder name", context)

        _append_token(context, "name", name)
        token: dict = {"name": name}

        ws_after_name = _skip_space(context, ret=preserve_ws)
        if preserve_ws:
            ws["after_name"] = ws_after_name

        char = msg[context["i"]] if context["i"] < length else None

        if char == constants.CHAR_CLOSE:
            _append_token(context, "syntax", char)
            context["i"] += 1
            if preserve_ws and ws:
                token["_ws"] = ws
            return self._token_indices(token, start_idx, context["i"])

        if char != constants.CHAR_SEP:
            raise _expected(SEP_OR_CLOSE, context)

        _append_token(context, "syntax", char)
        context["i"] += 1

        ws_after_type_sep = _skip_space(context, ret=preserve_ws)
        if preserve_ws:
            ws["after_type_sep"] = ws_after_type_sep

        ttype = self._parse_name(context)
        if not ttype:
            raise _expected("placeholder type", context)

        _append_token(context, "type", ttype)
        token["type"] = ttype

        ws_after_type = _skip_space(context, ret=preserve_ws)
        if preserve_ws:
            ws["after_type"] = ws_after_type

        char = msg[context["i"]] if context["i"] < length else None
        if char == constants.CHAR_CLOSE:
            _append_token(context, "syntax", char)
            if ttype in self.options["submessage_types"]:  # type: ignore[operator]
                raise _expected(f"{ttype} sub-messages", context)
            context["i"] += 1
            if preserve_ws and ws:
                token["_ws"] = ws
            return self._token_indices(token, start_idx, context["i"])

        if char != constants.CHAR_SEP:
            raise _expected(SEP_OR_CLOSE, context)

        _append_token(context, "syntax", char)
        context["i"] += 1

        ws_after_style_sep = _skip_space(context, ret=preserve_ws)
        if preserve_ws:
            ws["after_style_sep"] = ws_after_style_sep

        if ttype in self.options["subnumeric_types"]:  # type: ignore[operator]
            offset = self._parse_offset(context)
            token["offset"] = offset if offset else 0
            if offset:
                _skip_space(context)

        if ttype in self.options["submessage_types"]:  # type: ignore[operator]
            messages = self._parse_submessages(context, token)
            if not messages:
                raise _expected(f"{ttype} sub-messages", context)
            token["options"] = messages
        else:
            start = context["i"]
            fmt = self._parse_text(context, token, True)
            if not fmt:
                raise _expected("placeholder style", context)

            end = context["i"]
            spaces = _skip_space(context, True)

            if self.options["loose_submessages"] and context["i"] < length and msg[context["i"]] == constants.CHAR_OPEN:
                context["i"] = start
                messages = self._parse_submessages(context, token)
                if not messages:
                    raise _expected(f"{ttype} sub-messages", context)
                token["options"] = messages
            else:
                token["format"] = fmt
                _append_token(context, "style", msg[start:end])
                if spaces:
                    _append_token(context, "space", spaces)

        ws_before_close = _skip_space(context, ret=preserve_ws)
        if preserve_ws:
            ws["before_close"] = ws_before_close

        char = msg[context["i"]] if context["i"] < length else None
        if char != constants.CHAR_CLOSE:
            raise _expected(constants.CHAR_CLOSE, context)

        _append_token(context, "syntax", char)
        context["i"] += 1

        if preserve_ws and ws:
            token["_ws"] = ws

        return self._token_indices(token, start_idx, context["i"])

    def _parse_tag(self, context: dict, parent: dict | None) -> dict | None:
        if not self.options["allow_tags"]:
            return None

        if not self._can_read_tag(context, parent):
            return None

        msg = context["msg"]
        length = context["length"]
        i = context["i"]
        start_idx = i
        char = msg[i] if i < length else None

        if char != constants.CHAR_TAG_OPEN:
            return None

        if msg[i : i + len(constants.TAG_END)] == constants.TAG_END:
            raise _unexpected(constants.TAG_END, i)

        context["i"] += 1
        name = self._parse_name(context, True)
        if not name:
            if not self.options["strict_tags"]:
                context["i"] = start_idx
                return None
            raise _expected("tag name", context)

        _append_token(context, "syntax", char)
        token: dict = {"type": self.options["tag_type"], "name": name}
        _append_token(context, "name", name)
        _skip_space(context)

        i = context["i"]
        if i < length and msg[i : i + len(constants.TAG_CLOSING)] == constants.TAG_CLOSING:
            _append_token(context, "syntax", constants.TAG_CLOSING)
            context["i"] += len(constants.TAG_CLOSING)
            return self._token_indices(token, start_idx, context["i"])

        char = msg[i] if i < length else None
        if char != constants.CHAR_TAG_END:
            raise _expected(constants.CHAR_TAG_END + " or " + constants.TAG_CLOSING, context)

        _append_token(context, "syntax", char)
        context["i"] += 1

        children = self._parse_ast(context, token)
        if children:
            token["contents"] = children
        end = context["i"]

        if end < length and msg[end : end + len(constants.TAG_END)] != constants.TAG_END:
            raise _expected(constants.TAG_END, context)

        _append_token(context, "syntax", constants.TAG_END)
        context["i"] += len(constants.TAG_END)

        close_name = self._parse_name(context, True)
        if close_name:
            _append_token(context, "name", close_name)
        if close_name != name:
            raise _expected(
                constants.TAG_END + name + constants.CHAR_TAG_END,
                msg[end] if end < length else "<EOF>",
                end,
            )

        _skip_space(context)
        char = msg[context["i"]] if context["i"] < length else None
        if char != constants.CHAR_TAG_END:
            raise _expected(constants.CHAR_TAG_END, context)

        _append_token(context, "syntax", char)
        context["i"] += 1
        return self._token_indices(token, start_idx, context["i"])

    def _parse_name(self, context: dict, is_tag: bool = False) -> str:
        msg = context["msg"]
        length = context["length"]
        name = ""

        while context["i"] < length:
            char = msg[context["i"]]
            if (
                char in constants.VAR_CHARS
                or char == constants.CHAR_SEP
                or char == constants.CHAR_HASH
                or char == constants.CHAR_ESCAPE
                or _is_space(char)
                or (is_tag and char in constants.TAG_CHARS)
            ):
                break
            name += char
            context["i"] += 1

        return name

    def _parse_offset(self, context: dict) -> int:
        msg = context["msg"]
        length = context["length"]
        start = context["i"]

        if start >= length or msg[start : start + len(constants.OFFSET)] != constants.OFFSET:
            return 0

        _append_token(context, "offset", constants.OFFSET)
        context["i"] += len(constants.OFFSET)
        _skip_space(context)

        start = context["i"]
        while context["i"] < length and (
            _is_digit(msg[context["i"]]) or (context["i"] == start and msg[context["i"]] == "-")
        ):
            context["i"] += 1

        if start == context["i"]:
            raise _expected("offset number", context)

        offset = msg[start : context["i"]]
        _append_token(context, "number", offset)
        return int(offset, 10)

    def _parse_submessages(self, context: dict, parent: dict) -> dict | None:
        msg = context["msg"]
        length = context["length"]
        preserve_ws = bool(self.options["preserve_whitespace"])
        options: dict = {}

        context["depth"] += 1

        while context["i"] < length and msg[context["i"]] != constants.CHAR_CLOSE:
            # Save position before consuming space so we can rewind if we hit }
            pre_space_pos = context["i"]
            ws_before_selector = _skip_space(context, ret=preserve_ws) if preserve_ws else _skip_space(context)

            if context["i"] >= length or msg[context["i"]] == constants.CHAR_CLOSE:
                # Rewind: this trailing space belongs to the outer placeholder's before_close
                if preserve_ws:
                    context["i"] = pre_space_pos
                break

            selector = self._parse_name(context)
            if not selector:
                raise _expected("sub-message selector", context)
            _append_token(context, "selector", selector)

            ws_after_selector = _skip_space(context, ret=preserve_ws) if preserve_ws else _skip_space(context)

            submessage = self._parse_submessage(context, parent)

            if preserve_ws:
                # Store whitespace metadata on the submessage list
                # We use a wrapper dict so we can attach _ws
                options[selector] = submessage
                # Store selector whitespace as metadata on the options dict
                if "_ws" not in options:
                    options["_ws"] = {}
                options["_ws"][selector] = {
                    "before_selector": ws_before_selector or "",
                    "after_selector": ws_after_selector or "",
                }
            else:
                options[selector] = submessage

            if not preserve_ws:
                _skip_space(context)

        context["depth"] -= 1

        if not options or (len(options) == 1 and "_ws" in options):
            return None

        req = self.options["require_other"]
        ttype = parent["type"] if parent else None
        if req == "all":
            req = True
        elif req == "subnumeric":
            req = self.options["subnumeric_types"]
        elif req and not isinstance(req, list):
            req = self.options["submessage_types"]
        if isinstance(req, list):
            req = ttype in req

        if req and "other" not in options:
            raise _expected(f"{ttype} sub-message other", context)

        return options

    def _parse_submessage(self, context: dict, parent: dict) -> list:
        if context["depth"] >= self.options["maximum_depth"]:
            raise _recursion(context)

        msg = context["msg"]
        length = context["length"]
        if context["i"] >= length or msg[context["i"]] != constants.CHAR_OPEN:
            raise _expected(constants.CHAR_OPEN, context)

        _append_token(context, "syntax", constants.CHAR_OPEN)
        context["i"] += 1

        message = self._parse_ast(context, parent)

        char = msg[context["i"]] if context["i"] < length else None
        if char != constants.CHAR_CLOSE:
            raise _expected(constants.CHAR_CLOSE, context)

        _append_token(context, "syntax", constants.CHAR_CLOSE)
        context["i"] += 1

        return message

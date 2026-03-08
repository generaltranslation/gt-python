"""Tests for msg(), decode_msg(), decode_options() — verified against JS fixtures."""

import base64
import json
from pathlib import Path
from typing import Any

from gt_i18n import decode_msg, decode_options, msg

FIXTURES = json.loads((Path(__file__).parent / "fixtures" / "js_msg_parity.json").read_text())

# Mapping from JS $-prefixed keys to Python _-prefixed keys
_JS_TO_PY_KEY_MAP: dict[str, str] = {
    "$context": "_context",
    "$id": "_id",
    "$max_chars": "_max_chars",
    "$_source": "__source",
    "$_hash": "__hash",
}


def _convert_keys(d: dict[str, Any]) -> dict[str, Any]:
    """Convert JS-style $-prefixed keys to Python-style _-prefixed keys."""
    return {_JS_TO_PY_KEY_MAP.get(k, k): v for k, v in d.items()}


def _convert_encoded_string(encoded: str) -> str:
    """Re-encode a JS-style encoded message with Python-style keys.

    Takes 'message:base64payload', decodes the payload, converts
    $-prefixed keys to _-prefixed, and re-encodes.
    """
    idx = encoded.rfind(":")
    if idx == -1:
        return encoded
    msg_part = encoded[:idx]
    payload = json.loads(base64.b64decode(encoded[idx + 1:]).decode())
    converted = _convert_keys(payload)
    new_b64 = base64.b64encode(json.dumps(converted).encode()).decode()
    return f"{msg_part}:{new_b64}"


class TestMsg:
    def test_no_options(self) -> None:
        f = FIXTURES["msg"]["no_options"]
        assert msg(f["args"][0]) == f["result"]

    def test_with_vars(self) -> None:
        f = FIXTURES["msg"]["with_vars"]
        py_args = _convert_keys(f["args"][1])
        result = msg(f["args"][0], **py_args)
        assert decode_msg(result) == decode_msg(f["result"])
        py_opts = decode_options(result)
        assert py_opts is not None
        js_opts = _convert_keys(FIXTURES["decodeOptions"]["encoded"]["result"])
        assert py_opts["__hash"] == js_opts["__hash"]
        assert py_opts["__source"] == js_opts["__source"]
        assert py_opts["name"] == js_opts["name"]

    def test_with_context(self) -> None:
        f = FIXTURES["msg"]["with_context"]
        py_args = _convert_keys(f["args"][1])
        result = msg(f["args"][0], **py_args)
        assert ":" in result
        assert decode_msg(result) == "Save"
        opts = decode_options(result)
        assert opts is not None
        assert opts["_context"] == "button"
        f_opts = decode_options(f["result"])
        assert f_opts is not None
        f_opts_py = _convert_keys(f_opts)
        assert opts["__hash"] == f_opts_py["__hash"]

    def test_with_id(self) -> None:
        f = FIXTURES["msg"]["with_id"]
        py_args = _convert_keys(f["args"][1])
        result = msg(f["args"][0], **py_args)
        assert ":" in result
        assert decode_msg(result) == "Hello"
        opts = decode_options(result)
        assert opts is not None
        assert opts["_id"] == "greeting"
        f_opts = decode_options(f["result"])
        assert f_opts is not None
        f_opts_py = _convert_keys(f_opts)
        assert opts["__hash"] == f_opts_py["__hash"]

    def test_with_id_and_var(self) -> None:
        f = FIXTURES["msg"]["with_id_and_var"]
        py_args = _convert_keys(f["args"][1])
        result = msg(f["args"][0], **py_args)
        assert decode_msg(result) == "Hi, Bob!"
        opts = decode_options(result)
        assert opts is not None
        assert opts["name"] == "Bob"
        assert opts["_id"] == "greet"
        f_opts = decode_options(f["result"])
        assert f_opts is not None
        f_opts_py = _convert_keys(f_opts)
        assert opts["__hash"] == f_opts_py["__hash"]


class TestDecodeMsg:
    def test_encoded(self) -> None:
        f = FIXTURES["decodeMsg"]["encoded"]
        assert decode_msg(f["input"]) == f["result"]

    def test_plain_text(self) -> None:
        f = FIXTURES["decodeMsg"]["plain"]
        assert decode_msg(f["input"]) == f["result"]

    def test_no_opts(self) -> None:
        f = FIXTURES["decodeMsg"]["no_opts"]
        assert decode_msg(f["input"]) == f["result"]

    def test_with_colon(self) -> None:
        f = FIXTURES["decodeMsg"]["with_colon"]
        assert decode_msg(f["input"]) == f["result"]


class TestDecodeOptions:
    def test_encoded(self) -> None:
        f = FIXTURES["decodeOptions"]["encoded"]
        converted_input = _convert_encoded_string(f["input"])
        result = decode_options(converted_input)
        expected = _convert_keys(f["result"])
        assert result is not None
        assert result["__hash"] == expected["__hash"]
        assert result["__source"] == expected["__source"]
        assert result["name"] == expected["name"]

    def test_plain_returns_none(self) -> None:
        f = FIXTURES["decodeOptions"]["plain"]
        assert decode_options(f["input"]) == f["result"]

    def test_no_opts_returns_none(self) -> None:
        f = FIXTURES["decodeOptions"]["no_opts"]
        assert decode_options(f["input"]) == f["result"]

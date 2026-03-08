"""Tests for msg(), decode_msg(), decode_options() — verified against JS fixtures."""

import json
from pathlib import Path

from gt_i18n import decode_msg, decode_options, msg
from helpers import convert_encoded_string, convert_keys

FIXTURES = json.loads((Path(__file__).parent / "fixtures" / "js_msg_parity.json").read_text())


class TestMsg:
    def test_no_options(self) -> None:
        f = FIXTURES["msg"]["no_options"]
        assert msg(f["args"][0]) == f["result"]

    def test_with_vars(self) -> None:
        f = FIXTURES["msg"]["with_vars"]
        py_args = convert_keys(f["args"][1])
        result = msg(f["args"][0], **py_args)
        assert decode_msg(result) == decode_msg(f["result"])
        py_opts = decode_options(result)
        assert py_opts is not None
        js_opts = convert_keys(FIXTURES["decodeOptions"]["encoded"]["result"])
        assert py_opts["__hash"] == js_opts["__hash"]
        assert py_opts["__source"] == js_opts["__source"]
        assert py_opts["name"] == js_opts["name"]

    def test_with_context(self) -> None:
        f = FIXTURES["msg"]["with_context"]
        py_args = convert_keys(f["args"][1])
        result = msg(f["args"][0], **py_args)
        assert ":" in result
        assert decode_msg(result) == "Save"
        opts = decode_options(result)
        assert opts is not None
        assert opts["_context"] == "button"
        f_opts = decode_options(f["result"])
        assert f_opts is not None
        f_opts_py = convert_keys(f_opts)
        assert opts["__hash"] == f_opts_py["__hash"]

    def test_with_id(self) -> None:
        f = FIXTURES["msg"]["with_id"]
        py_args = convert_keys(f["args"][1])
        result = msg(f["args"][0], **py_args)
        assert ":" in result
        assert decode_msg(result) == "Hello"
        opts = decode_options(result)
        assert opts is not None
        assert opts["_id"] == "greeting"
        f_opts = decode_options(f["result"])
        assert f_opts is not None
        f_opts_py = convert_keys(f_opts)
        assert opts["__hash"] == f_opts_py["__hash"]

    def test_with_id_and_var(self) -> None:
        f = FIXTURES["msg"]["with_id_and_var"]
        py_args = convert_keys(f["args"][1])
        result = msg(f["args"][0], **py_args)
        assert decode_msg(result) == "Hi, Bob!"
        opts = decode_options(result)
        assert opts is not None
        assert opts["name"] == "Bob"
        assert opts["_id"] == "greet"
        f_opts = decode_options(f["result"])
        assert f_opts is not None
        f_opts_py = convert_keys(f_opts)
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
        converted_input = convert_encoded_string(f["input"])
        result = decode_options(converted_input)
        expected = convert_keys(f["result"])
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

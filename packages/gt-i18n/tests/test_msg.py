"""Tests for msg(), decode_msg(), decode_options() — verified against JS fixtures."""

import json
from pathlib import Path

from gt_i18n import decode_msg, decode_options, msg

FIXTURES = json.loads(
    (Path(__file__).parent / "fixtures" / "js_msg_parity.json").read_text()
)


class TestMsg:
    def test_no_options(self):
        f = FIXTURES["msg"]["no_options"]
        assert msg(f["args"][0]) == f["result"]

    def test_with_vars(self):
        f = FIXTURES["msg"]["with_vars"]
        result = msg(f["args"][0], **f["args"][1])
        assert decode_msg(result) == decode_msg(f["result"])
        py_opts = decode_options(result)
        js_opts = FIXTURES["decodeOptions"]["encoded"]["result"]
        assert py_opts["$_hash"] == js_opts["$_hash"]
        assert py_opts["$_source"] == js_opts["$_source"]
        assert py_opts["name"] == js_opts["name"]

    def test_with_context(self):
        f = FIXTURES["msg"]["with_context"]
        result = msg(f["args"][0], **f["args"][1])
        assert ":" in result
        assert decode_msg(result) == "Save"
        opts = decode_options(result)
        assert opts is not None
        assert opts["$context"] == "button"
        assert opts["$_hash"] == decode_options(f["result"])["$_hash"]

    def test_with_id(self):
        f = FIXTURES["msg"]["with_id"]
        result = msg(f["args"][0], **f["args"][1])
        assert ":" in result
        assert decode_msg(result) == "Hello"
        opts = decode_options(result)
        assert opts is not None
        assert opts["$id"] == "greeting"
        assert opts["$_hash"] == decode_options(f["result"])["$_hash"]

    def test_with_id_and_var(self):
        f = FIXTURES["msg"]["with_id_and_var"]
        result = msg(f["args"][0], **f["args"][1])
        assert decode_msg(result) == "Hi, Bob!"
        opts = decode_options(result)
        assert opts is not None
        assert opts["name"] == "Bob"
        assert opts["$id"] == "greet"
        assert opts["$_hash"] == decode_options(f["result"])["$_hash"]


class TestDecodeMsg:
    def test_encoded(self):
        f = FIXTURES["decodeMsg"]["encoded"]
        assert decode_msg(f["input"]) == f["result"]

    def test_plain_text(self):
        f = FIXTURES["decodeMsg"]["plain"]
        assert decode_msg(f["input"]) == f["result"]

    def test_no_opts(self):
        f = FIXTURES["decodeMsg"]["no_opts"]
        assert decode_msg(f["input"]) == f["result"]

    def test_with_colon(self):
        f = FIXTURES["decodeMsg"]["with_colon"]
        assert decode_msg(f["input"]) == f["result"]


class TestDecodeOptions:
    def test_encoded(self):
        f = FIXTURES["decodeOptions"]["encoded"]
        result = decode_options(f["input"])
        assert result is not None
        assert result["$_hash"] == f["result"]["$_hash"]
        assert result["$_source"] == f["result"]["$_source"]
        assert result["name"] == f["result"]["name"]

    def test_plain_returns_none(self):
        f = FIXTURES["decodeOptions"]["plain"]
        assert decode_options(f["input"]) == f["result"]

    def test_no_opts_returns_none(self):
        f = FIXTURES["decodeOptions"]["no_opts"]
        assert decode_options(f["input"]) == f["result"]

"""Tests for m_fallback() and t_fallback() — verified against JS fixtures."""

import base64
import json
from pathlib import Path
from typing import Any

from gt_i18n import m_fallback, t_fallback

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


class TestMFallback:
    def test_encoded_message(self) -> None:
        f = FIXTURES["mFallback"]["encoded"]
        converted_input = _convert_encoded_string(f["input"])
        assert m_fallback(converted_input) == f["result"]

    def test_plain_text(self) -> None:
        f = FIXTURES["mFallback"]["plain"]
        assert m_fallback(f["input"]) == f["result"]

    def test_no_opts_message(self) -> None:
        f = FIXTURES["mFallback"]["no_opts"]
        assert m_fallback(f["input"]) == f["result"]

    def test_null_input(self) -> None:
        f = FIXTURES["mFallback"]["null_input"]
        assert m_fallback(f["input"]) == f["result"]


class TestTFallback:
    def test_plain(self) -> None:
        f = FIXTURES["gtFallback"]["plain"]
        assert t_fallback(f["input"][0]) == f["result"]

    def test_with_vars(self) -> None:
        f = FIXTURES["gtFallback"]["with_vars"]
        py_args = _convert_keys(f["input"][1])
        assert t_fallback(f["input"][0], **py_args) == f["result"]

    def test_declare_var(self) -> None:
        f = FIXTURES["gtFallback"]["declare_var"]
        assert t_fallback(f["input"][0]) == f["result"]

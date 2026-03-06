"""Tests for m_fallback() and t_fallback() — verified against JS fixtures."""

import json
from pathlib import Path

from gt_i18n import m_fallback, t_fallback

FIXTURES = json.loads((Path(__file__).parent / "fixtures" / "js_msg_parity.json").read_text())


class TestMFallback:
    def test_encoded_message(self) -> None:
        f = FIXTURES["mFallback"]["encoded"]
        assert m_fallback(f["input"]) == f["result"]

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
        assert t_fallback(f["input"][0], **f["input"][1]) == f["result"]

    def test_declare_var(self) -> None:
        f = FIXTURES["gtFallback"]["declare_var"]
        assert t_fallback(f["input"][0]) == f["result"]

"""Tests for msg() encoding/decoding roundtrip."""

from gt_i18n import decode_msg, decode_options, msg
from gt_i18n.translation_functions._hash_message import hash_message


def test_msg_roundtrip():
    encoded = msg("Hello, {name}!", name="Alice")
    result = decode_msg(encoded)
    assert result == "Hello, Alice!"


def test_decode_options():
    encoded = msg("Hello, {name}!", name="Alice")
    opts = decode_options(encoded)
    assert opts["$_source"] == "Hello, {name}!"
    assert opts["$_hash"] == hash_message("Hello, {name}!")
    assert opts["name"] == "Alice"


def test_msg_no_variables():
    encoded = msg("Hello, world!")
    result = decode_msg(encoded)
    assert result == "Hello, world!"


def test_msg_with_context():
    encoded = msg("Save", **{"$context": "button"})
    opts = decode_options(encoded)
    assert opts["$_hash"] == hash_message("Save", context="button")
    # $context is filtered out (it's a $-key)
    assert "$context" not in opts

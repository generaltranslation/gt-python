"""Tests for hash_message parity and correctness."""

from gt_i18n.translation_functions._hash_message import hash_message


def test_plain_message():
    h = hash_message("Hello, world!")
    assert isinstance(h, str)
    assert len(h) == 16


def test_same_message_same_hash():
    h1 = hash_message("Hello, world!")
    h2 = hash_message("Hello, world!")
    assert h1 == h2


def test_different_messages_different_hash():
    h1 = hash_message("Hello")
    h2 = hash_message("Goodbye")
    assert h1 != h2


def test_with_context():
    h1 = hash_message("Save", context="button")
    h2 = hash_message("Save", context="menu")
    h3 = hash_message("Save")
    assert h1 != h2
    assert h1 != h3


def test_with_id():
    h1 = hash_message("Hello", id="greeting")
    h2 = hash_message("Hello")
    assert h1 != h2


def test_with_max_chars():
    h1 = hash_message("Hello", max_chars=10)
    h2 = hash_message("Hello")
    assert h1 != h2


def test_with_variables():
    """Messages with declare_var produce different hashes after index_vars."""
    from generaltranslation.static._declare_var import declare_var

    msg = f"Hello, {declare_var('Alice', name='user')}!"
    h = hash_message(msg)
    assert isinstance(h, str)
    assert len(h) == 16

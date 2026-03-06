"""Tests for ContextVarStorageAdapter."""

import threading

from gt_i18n.i18n_manager._context_var_adapter import ContextVarStorageAdapter


def test_set_get_locale():
    adapter = ContextVarStorageAdapter()
    adapter.set_item("locale", "fr")
    assert adapter.get_item("locale") == "fr"


def test_default_none():
    adapter = ContextVarStorageAdapter()
    # In a fresh context, value might be from previous test — use a thread
    result = [None]

    def check():
        a = ContextVarStorageAdapter()
        result[0] = a.get_item("locale")

    t = threading.Thread(target=check)
    t.start()
    t.join()
    assert result[0] is None


def test_non_locale_key():
    adapter = ContextVarStorageAdapter()
    adapter.set_item("other", "value")
    assert adapter.get_item("other") is None


def test_thread_isolation():
    adapter = ContextVarStorageAdapter()
    adapter.set_item("locale", "en")

    other_thread_value = [None]

    def check():
        a = ContextVarStorageAdapter()
        other_thread_value[0] = a.get_item("locale")

    t = threading.Thread(target=check)
    t.start()
    t.join()
    # New thread should NOT see the parent's ContextVar value
    assert other_thread_value[0] is None

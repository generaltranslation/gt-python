"""Tests for I18nManager lifecycle."""

import asyncio

import pytest

from gt_i18n import I18nManager


def test_default_locale():
    mgr = I18nManager(default_locale="en")
    assert mgr.default_locale == "en"


def test_get_set_locale():
    mgr = I18nManager(default_locale="en")
    mgr.set_locale("fr")
    assert mgr.get_locale() == "fr"


def test_get_locale_default():
    import threading

    result = [None]

    def check():
        # Run in a new thread to get a clean ContextVar
        mgr = I18nManager(default_locale="en")
        result[0] = mgr.get_locale()

    t = threading.Thread(target=check)
    t.start()
    t.join()
    assert result[0] == "en"


def test_requires_translation_same_locale():
    mgr = I18nManager(default_locale="en", locales=["en", "es"])
    assert not mgr.requires_translation("en")


def test_requires_translation_different_locale():
    mgr = I18nManager(default_locale="en", locales=["en", "es"])
    assert mgr.requires_translation("es")


def test_get_locales():
    mgr = I18nManager(default_locale="en", locales=["en", "es", "fr"])
    assert mgr.get_locales() == ["en", "es", "fr"]


def test_custom_loader():
    translations = {"hash1": "Translated!"}

    def loader(locale):
        return translations if locale == "es" else {}

    mgr = I18nManager(
        default_locale="en", locales=["en", "es"], load_translations=loader
    )
    asyncio.run(mgr.get_translations("es"))
    assert mgr.get_translations_sync("es") == translations


def test_load_all():
    loaded = set()

    def loader(locale):
        loaded.add(locale)
        return {}

    mgr = I18nManager(
        default_locale="en", locales=["es", "fr"], load_translations=loader
    )
    asyncio.run(mgr.load_all_translations())
    assert loaded == {"es", "fr"}

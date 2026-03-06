"""Tests for I18nManager lifecycle."""

import asyncio

from gt_i18n import I18nManager


def test_default_locale() -> None:
    mgr = I18nManager(default_locale="en")
    assert mgr.default_locale == "en"


def test_get_set_locale() -> None:
    mgr = I18nManager(default_locale="en")
    mgr.set_locale("fr")
    assert mgr.get_locale() == "fr"


def test_get_locale_default() -> None:
    import threading

    result: list[str | None] = [None]

    def check() -> None:
        # Run in a new thread to get a clean ContextVar
        mgr = I18nManager(default_locale="en")
        result[0] = mgr.get_locale()

    t = threading.Thread(target=check)
    t.start()
    t.join()
    assert result[0] == "en"


def test_requires_translation_same_locale() -> None:
    mgr = I18nManager(default_locale="en", locales=["en", "es"])
    assert not mgr.requires_translation("en")


def test_requires_translation_different_locale() -> None:
    mgr = I18nManager(default_locale="en", locales=["en", "es"])
    assert mgr.requires_translation("es")


def test_get_locales() -> None:
    mgr = I18nManager(default_locale="en", locales=["en", "es", "fr"])
    assert mgr.get_locales() == ["en", "es", "fr"]


def test_custom_loader() -> None:
    translations = {"hash1": "Translated!"}

    def loader(locale: str) -> dict[str, str]:
        return translations if locale == "es" else {}

    mgr = I18nManager(default_locale="en", locales=["en", "es"], load_translations=loader)
    asyncio.run(mgr.get_translations("es"))
    assert mgr.get_translations_sync("es") == translations


def test_load_all() -> None:
    loaded = set()

    def loader(locale: str) -> dict[str, str]:
        loaded.add(locale)
        return {}

    mgr = I18nManager(default_locale="en", locales=["es", "fr"], load_translations=loader)
    asyncio.run(mgr.load_all_translations())
    assert loaded == {"es", "fr"}

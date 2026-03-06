"""Tests for the t() function with mock translations."""

from collections.abc import Generator
from typing import Any

import pytest
from gt_i18n import I18nManager, set_i18n_manager, t
from gt_i18n.translation_functions._hash_message import hash_message


@pytest.fixture(autouse=True)
def _reset_singleton() -> Generator[None, None, None]:
    """Reset singleton after each test."""
    import gt_i18n.i18n_manager._singleton as mod

    old = mod._manager
    yield
    mod._manager = old


def _make_manager(translations_by_locale: dict[str, dict[str, str]] | None = None, **kwargs: Any) -> I18nManager:
    """Create a manager with a custom loader."""
    translations_by_locale = translations_by_locale or {}

    def loader(locale: str) -> dict[str, str]:
        return translations_by_locale.get(locale, {})

    manager = I18nManager(load_translations=loader, **kwargs)
    set_i18n_manager(manager)
    return manager


def test_source_locale_no_translation() -> None:
    """Source locale returns interpolated source."""
    _make_manager(default_locale="en", locales=["en", "es"])
    manager = _make_manager(default_locale="en", locales=["en", "es"])
    manager.set_locale("en")
    result = t("Hello, {name}!", name="Alice")
    assert result == "Hello, Alice!"


def test_target_locale_with_translation() -> None:
    """Target locale with matching translation."""
    h = hash_message("Hello, world!")
    translations = {"es": {h: "Hola, mundo!"}}
    manager = _make_manager(
        translations_by_locale=translations,
        default_locale="en",
        locales=["en", "es"],
    )
    manager.set_locale("es")
    # Pre-load translations synchronously via the cache
    import asyncio

    asyncio.run(manager.get_translations("es"))

    result = t("Hello, world!")
    assert result == "Hola, mundo!"


def test_target_locale_missing_translation() -> None:
    """Target locale without translation falls back to source."""
    manager = _make_manager(
        translations_by_locale={"es": {}},
        default_locale="en",
        locales=["en", "es"],
    )
    manager.set_locale("es")
    result = t("Hello, world!")
    assert result == "Hello, world!"


def test_variable_interpolation_in_translation() -> None:
    """Variables are interpolated in the translated string."""
    h = hash_message("Hello, {name}!")
    translations = {"es": {h: "Hola, {name}!"}}
    manager = _make_manager(
        translations_by_locale=translations,
        default_locale="en",
        locales=["en", "es"],
    )
    manager.set_locale("es")
    import asyncio

    asyncio.run(manager.get_translations("es"))

    result = t("Hello, {name}!", name="Carlos")
    assert result == "Hola, Carlos!"


def test_t_raises_without_init() -> None:
    """t() raises RuntimeError if manager not initialized."""
    import gt_i18n.i18n_manager._singleton as mod

    mod._manager = None
    with pytest.raises(RuntimeError, match="not initialized"):
        t("Hello")

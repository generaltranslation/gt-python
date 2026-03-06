"""Tests for TranslationsManager."""

import asyncio

import pytest
from gt_i18n.i18n_manager._translations_manager import TranslationsManager


@pytest.fixture
def sample_translations() -> dict[str, str]:
    return {"greeting_hash": "Hola, mundo!"}


def test_custom_loader(sample_translations: dict[str, str]) -> None:
    def loader(locale: str) -> dict[str, str]:
        if locale == "es":
            return sample_translations
        return {}

    mgr = TranslationsManager(loader)
    result = asyncio.run(mgr.get_translations("es"))
    assert result == sample_translations


def test_cache_hit(sample_translations: dict[str, str]) -> None:
    call_count = [0]

    def loader(locale: str) -> dict[str, str]:
        call_count[0] += 1
        return sample_translations

    mgr = TranslationsManager(loader, cache_expiry_time=60_000)
    asyncio.run(mgr.get_translations("es"))
    asyncio.run(mgr.get_translations("es"))
    assert call_count[0] == 1


def test_sync_returns_cached(sample_translations: dict[str, str]) -> None:
    def loader(locale: str) -> dict[str, str]:
        return sample_translations

    mgr = TranslationsManager(loader)
    # Before loading, sync returns empty
    assert mgr.get_translations_sync("es") == {}
    # After loading
    asyncio.run(mgr.get_translations("es"))
    assert mgr.get_translations_sync("es") == sample_translations


def test_load_all() -> None:
    loaded = []

    def loader(locale: str) -> dict[str, str]:
        loaded.append(locale)
        return {f"{locale}_hash": f"{locale}_value"}

    mgr = TranslationsManager(loader)
    asyncio.run(mgr.load_all(["en", "es", "fr"]))
    assert set(loaded) == {"en", "es", "fr"}
    assert mgr.get_translations_sync("es") == {"es_hash": "es_value"}


def test_loader_error_returns_empty() -> None:
    def loader(locale: str) -> dict[str, str]:
        raise RuntimeError("fail")

    mgr = TranslationsManager(loader)
    result = asyncio.run(mgr.get_translations("es"))
    assert result == {}


def test_async_loader() -> None:
    async def loader(locale: str) -> dict[str, str]:
        return {"async_hash": "async_value"}

    mgr = TranslationsManager(loader)
    result = asyncio.run(mgr.get_translations("es"))
    assert result == {"async_hash": "async_value"}

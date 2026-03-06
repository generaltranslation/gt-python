"""Translation cache with configurable loader and expiry."""

from __future__ import annotations

import asyncio
import inspect
import time
from typing import Awaitable, Callable

TranslationsLoader = Callable[[str], dict[str, str] | Awaitable[dict[str, str]]]


class _CacheEntry:
    __slots__ = ("translations", "loaded_at")

    def __init__(self, translations: dict[str, str], loaded_at: float) -> None:
        self.translations = translations
        self.loaded_at = loaded_at


class TranslationsManager:
    """Caches ``dict[str, str]`` (hash -> translated string) per locale."""

    def __init__(
        self,
        loader: TranslationsLoader,
        cache_expiry_time: int = 60_000,
    ) -> None:
        self._loader = loader
        self._cache_expiry_ms = cache_expiry_time
        self._cache: dict[str, _CacheEntry] = {}
        self._loading: dict[str, asyncio.Task[dict[str, str]]] = {}

    def _is_expired(self, entry: _CacheEntry) -> bool:
        elapsed_ms = (time.monotonic() - entry.loaded_at) * 1000
        return elapsed_ms > self._cache_expiry_ms

    async def _call_loader(self, locale: str) -> dict[str, str]:
        result = self._loader(locale)
        if inspect.isawaitable(result):
            return await result
        return result  # type: ignore[return-value]

    async def get_translations(self, locale: str) -> dict[str, str]:
        """Load translations for *locale*, using cache when valid."""
        entry = self._cache.get(locale)
        if entry is not None and not self._is_expired(entry):
            return entry.translations

        # Deduplicate concurrent loads
        if locale in self._loading:
            return await self._loading[locale]

        task = asyncio.ensure_future(self._call_loader(locale))
        self._loading[locale] = task
        try:
            translations = await task
        except Exception:
            translations = {}
        finally:
            self._loading.pop(locale, None)

        self._cache[locale] = _CacheEntry(translations, time.monotonic())
        return translations

    def get_translations_sync(self, locale: str) -> dict[str, str]:
        """Return cached translations or empty dict (never blocks)."""
        entry = self._cache.get(locale)
        if entry is not None and not self._is_expired(entry):
            return entry.translations
        return {}

    async def load_all(self, locales: list[str]) -> None:
        """Eagerly fetch translations for all *locales*."""
        await asyncio.gather(
            *(self.get_translations(loc) for loc in locales)
        )

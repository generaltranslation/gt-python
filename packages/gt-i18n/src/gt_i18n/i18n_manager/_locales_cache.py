"""Outer cache: locale → TranslationsCache with TTL.

Port of the JS ``LocalesCache`` introduced in gt PR #1207. Wraps the user's
``load_translations`` loader and builds a per-locale ``TranslationsCache``
on miss. Enforces a TTL on each locale entry; concurrent misses for the same
locale dedup via the ``Cache`` base.

Loader failures propagate to the caller (and do NOT poison the cache — the
next miss retries).
"""

from __future__ import annotations

import inspect
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any, cast

from gt_i18n.i18n_manager._cache import Cache
from gt_i18n.i18n_manager._lifecycle import LifecycleCallbacks
from gt_i18n.i18n_manager._translations_cache import TranslationsCache


@dataclass
class _LocaleEntry:
    """One cached locale: its TranslationsCache, raw translations snapshot, and expiry."""

    translations_cache: TranslationsCache
    translations: dict[str, str]  # snapshot for hit/miss callback payloads
    expires_at: float  # time.monotonic() seconds


class LocalesCache(Cache[str, str, _LocaleEntry, TranslationsCache]):
    """Cache keyed on locale. ``get()`` returns the locale's TranslationsCache if fresh."""

    def __init__(
        self,
        *,
        load_translations: Callable[[str], dict[str, str] | Awaitable[dict[str, str]]],
        create_translate_many: Callable[[str], Callable[[dict[str, Any]], Awaitable[dict[str, Any]]]],
        ttl_ms: int = 60_000,
        batch_size: int = 25,
        batch_interval_ms: int = 50,
        max_concurrent_requests: int = 100,
        lifecycle: LifecycleCallbacks | None = None,
    ) -> None:
        super().__init__()
        self._load_translations = load_translations
        self._create_translate_many = create_translate_many
        self._ttl_s = ttl_ms / 1000
        self._batch_size = batch_size
        self._batch_interval_ms = batch_interval_ms
        self._max_concurrent_requests = max_concurrent_requests
        self._lifecycle: LifecycleCallbacks = lifecycle or {}

    # -- Cache API --------------------------------------------------------

    def _gen_key(self, locale: str) -> str:
        return locale

    def get(self, locale: str) -> TranslationsCache | None:
        """Return the cached TranslationsCache for ``locale`` if present and fresh."""
        entry = self._cache.get(locale)
        if entry is None:
            return None
        if entry.expires_at < time.monotonic():
            # Expired — evict and treat as miss.
            del self._cache[locale]
            return None
        self._fire("on_locales_cache_hit", locale=locale, value=dict(entry.translations))
        return entry.translations_cache

    async def miss(self, locale: str) -> TranslationsCache:
        """Fast-path to ``get()``; otherwise dedup-protected loader fallback."""
        cached = self.get(locale)
        if cached is not None:
            return cached
        entry = await self._miss_cache(locale)
        assert entry is not None, "_fallback returned None, which should not happen"
        return entry.translations_cache

    async def _fallback(self, locale: str) -> _LocaleEntry:
        """Invoke the user loader, build a new TranslationsCache, cache the entry."""
        maybe = self._load_translations(locale)
        translations: dict[str, str] = (
            await maybe if inspect.isawaitable(maybe) else maybe  # type: ignore[assignment]
        )

        tc = TranslationsCache(
            locale=locale,
            translate_many=self._create_translate_many(locale),
            initial=translations,
            batch_size=self._batch_size,
            batch_interval_ms=self._batch_interval_ms,
            max_concurrent_requests=self._max_concurrent_requests,
            lifecycle=self._lifecycle,
        )
        entry = _LocaleEntry(
            translations_cache=tc,
            translations=dict(translations),
            expires_at=time.monotonic() + self._ttl_s,
        )
        self._cache[locale] = entry
        self._fire("on_locales_cache_miss", locale=locale, value=dict(translations))
        return entry

    # -- helpers ----------------------------------------------------------

    def _fire(self, name: str, **kwargs: Any) -> None:
        cb = cast(Callable[..., Any] | None, self._lifecycle.get(name))  # type: ignore[misc]
        if cb is not None:
            cb(**kwargs)

"""Abstract two-phase cache with in-flight request deduplication.

Port of the JS ``Cache<InputKey, CacheKey, CacheValue, OutputValue>`` base
introduced in gt PR #1207. Provides the shared dedup primitive used by
``LocalesCache`` and ``TranslationsCache``: if two callers miss() for the
same cache key while the first is still in flight, they share one
``_fallback()`` invocation rather than firing two concurrent requests.
"""

from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

_InputKey = TypeVar("_InputKey")
_CacheKey = TypeVar("_CacheKey")
_CacheValue = TypeVar("_CacheValue")
_OutputValue = TypeVar("_OutputValue")


class Cache(ABC, Generic[_InputKey, _CacheKey, _CacheValue, _OutputValue]):
    """Abstract cache with synchronous ``get()`` and async dedup-fallback ``_miss_cache()``.

    Subclasses implement:
      * ``_gen_key(input)`` — map the external key to the internal cache key.
      * ``_fallback(input)`` — async work to populate the cache on a miss.
      * ``get(input)`` — synchronous lookup (never blocks, never fires network).
      * ``miss(input)`` — the public async entry point, orchestrating get/fallback.

    The base provides ``_miss_cache(input)``: a dedup wrapper around ``_fallback``
    keyed on ``CacheKey``. Concurrent callers with the same computed key share
    one in-flight future. Exceptions propagate to all awaiters but the pending
    entry is cleared so subsequent calls can retry cleanly.
    """

    def __init__(self) -> None:
        self._cache: dict[Any, _CacheValue] = {}
        self._pending: dict[Any, asyncio.Future[_CacheValue | None]] = {}

    @abstractmethod
    def _gen_key(self, input_key: _InputKey, /) -> _CacheKey:
        """Map the external input key to the internal cache key."""

    @abstractmethod
    async def _fallback(self, input_key: _InputKey, /) -> _CacheValue | None:
        """Populate the cache on miss. Runs at most once per in-flight window per key."""

    @abstractmethod
    def get(self, input_key: _InputKey, /) -> _OutputValue | None:
        """Synchronous accessor. Returns ``None`` on miss; never triggers work."""

    async def _miss_cache(self, input_key: _InputKey, /) -> _CacheValue | None:
        """Dedup concurrent misses by cache key, invoking ``_fallback`` exactly once."""
        key = self._gen_key(input_key)
        pending = self._pending.get(key)
        if pending is not None:
            return await pending

        loop = asyncio.get_running_loop()
        future: asyncio.Future[_CacheValue | None] = loop.create_future()
        self._pending[key] = future
        try:
            value = await self._fallback(input_key)
            future.set_result(value)
        except BaseException as exc:  # noqa: BLE001 — propagate to all awaiters via the future
            future.set_exception(exc)
        finally:
            self._pending.pop(key, None)

        # Always consume the future — returns the result or re-raises its exception.
        return await future

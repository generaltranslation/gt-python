"""Translation cache with configurable loader and expiry."""

from __future__ import annotations

import asyncio
import inspect
import threading
import time
from collections.abc import Awaitable, Callable
from concurrent.futures import ThreadPoolExecutor
from typing import Any

TranslationsLoader = Callable[[str], dict[str, str] | Awaitable[dict[str, str]]]


class _CacheEntry:
    __slots__ = ("translations", "loaded_at")

    def __init__(self, translations: dict[str, str], loaded_at: float) -> None:
        self.translations = translations
        self.loaded_at = loaded_at


async def _await(awaitable: Awaitable[Any]) -> Any:
    return await awaitable


def _run_blocking(awaitable: Awaitable[Any]) -> Any:
    """Run *awaitable* to completion from synchronous code."""
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(_await(awaitable))
    # A loop is already running in this thread, so run it on a fresh one in another thread.
    with ThreadPoolExecutor(max_workers=1) as pool:
        return pool.submit(asyncio.run, _await(awaitable)).result()


def _is_async(loader: TranslationsLoader) -> bool:
    """Whether *loader* is an ``async def`` function or an object whose ``__call__`` is one."""
    return inspect.iscoroutinefunction(loader) or inspect.iscoroutinefunction(getattr(loader, "__call__", None))


class TranslationsManager:
    """Caches ``dict[str, str]`` (hash -> translated string) per locale.

    An entry expires ``cache_expiry_time`` ms after it loads. An expired entry
    keeps being served while one reload runs in the background, and a reload
    that fails keeps the previous translations, so a slow or failing loader
    never drops a loaded locale back to the source text. Only a locale's first
    load makes its callers wait.

    From async code, an async loader runs on the caller's event loop, so a
    loader that holds a client bound to that loop keeps working, and its loads
    of a locale on that loop share one task. If the loop closes before a load
    finishes, as a one-off ``asyncio.run()`` does, the load finishes on a
    thread. Every other load runs on a thread and holds the locale's lock. In
    both cases, a reload and ``load_all`` for the same locale share one load.
    """

    def __init__(
        self,
        loader: TranslationsLoader,
        cache_expiry_time: int = 60_000,
    ) -> None:
        self._loader = loader
        self._loader_is_async = _is_async(loader)
        self._cache_expiry_ms = cache_expiry_time
        self._cache: dict[str, _CacheEntry] = {}
        self._loading: dict[str, asyncio.Task[None]] = {}
        self._locks: dict[str, threading.Lock] = {}
        self._locks_guard = threading.Lock()

    def _is_expired(self, entry: _CacheEntry) -> bool:
        elapsed_ms = (time.monotonic() - entry.loaded_at) * 1000
        return elapsed_ms > self._cache_expiry_ms

    def _fresh(self, locale: str) -> dict[str, str] | None:
        entry = self._cache.get(locale)
        if entry is not None and not self._is_expired(entry):
            return entry.translations
        return None

    def _store(self, locale: str, translations: dict[str, str] | None) -> dict[str, str]:
        """Cache a load result; ``None`` is a failed load, which keeps the previous translations."""
        if translations is None:
            previous = self._cache.get(locale)
            translations = previous.translations if previous is not None else {}
        self._cache[locale] = _CacheEntry(translations, time.monotonic())
        return translations

    # Async path (FastAPI and other asyncio code)

    async def _load_async(self, locale: str) -> dict[str, str] | None:
        try:
            result = self._loader(locale)
            return await result if inspect.isawaitable(result) else result
        except Exception:
            return None

    async def _load_and_store(self, locale: str) -> None:
        if self._loader_is_async:
            self._store(locale, await self._load_async(locale))
        else:
            # A synchronous loader runs on a worker thread, off the event loop.
            await asyncio.to_thread(self._load_locked, locale)

    def _start_load(self, locale: str) -> asyncio.Task[None]:
        """Start a load for *locale* on the running loop, or join the one already running there."""
        loop = asyncio.get_running_loop()
        task = self._loading.get(locale)
        if task is None or task.done() or task.get_loop() is not loop:
            task = loop.create_task(self._load_and_store(locale))
            self._loading[locale] = task
            task.add_done_callback(lambda done: self._load_finished(locale, done))
        return task

    def _load_finished(self, locale: str, task: asyncio.Task[None]) -> None:
        if self._loading.get(locale) is task:
            del self._loading[locale]
        if task.cancelled():
            # The loop closed before the load finished, so it finishes on a thread.
            self._refresh_in_background(locale)

    async def get_translations(self, locale: str) -> dict[str, str]:
        """Return translations for *locale*, loading them if missing and reloading in the background if expired."""
        fresh = self._fresh(locale)
        if fresh is not None:
            return fresh
        entry = self._cache.get(locale)
        if entry is not None:
            if not self._loader_is_async:
                # The reload runs on a thread, so it outlives this call's event loop.
                self._refresh_in_background(locale)
            elif not self._lock_for(locale).locked():  # unless a thread is reloading it already
                # An async loader reloads on this loop, which it may hold a client for.
                self._start_load(locale)
            return entry.translations
        # Shielded, so a cancelled caller does not cancel the load for the others.
        await asyncio.shield(self._start_load(locale))
        return self.get_translations_sync(locale)

    async def load_all(self, locales: list[str]) -> None:
        """Eagerly fetch translations for all *locales*, waiting for every load."""
        tasks = [self._start_load(loc) for loc in locales if self._fresh(loc) is None]
        if tasks:
            await asyncio.gather(*(asyncio.shield(task) for task in tasks))

    # Blocking path (Flask and other synchronous code)

    def _lock_for(self, locale: str) -> threading.Lock:
        with self._locks_guard:
            return self._locks.setdefault(locale, threading.Lock())

    def _load_blocking(self, locale: str) -> dict[str, str] | None:
        try:
            result = self._loader(locale)
            return _run_blocking(result) if inspect.isawaitable(result) else result
        except Exception:
            return None

    def _load_locked(self, locale: str) -> None:
        """Load *locale* on this thread unless it is fresh, after any load of it already running on a thread."""
        with self._lock_for(locale):
            if self._fresh(locale) is None:
                self._store(locale, self._load_blocking(locale))

    def _reload_in_background(self, locale: str, lock: threading.Lock) -> None:
        try:
            self._store(locale, self._load_blocking(locale))
        finally:
            lock.release()

    def _refresh_in_background(self, locale: str) -> None:
        """Load *locale* on a daemon thread, unless a thread is loading it already."""
        lock = self._lock_for(locale)
        if not lock.acquire(blocking=False):
            return
        if self._fresh(locale) is not None:  # another reload finished in the meantime
            lock.release()
            return
        try:
            threading.Thread(target=self._reload_in_background, args=(locale, lock), daemon=True).start()
        except BaseException:
            lock.release()
            raise

    def get_translations_blocking(self, locale: str) -> dict[str, str]:
        """Return translations for *locale* from synchronous code.

        The first load blocks the callers for that locale. After that, an
        expired entry is returned at once while one background thread reloads it.
        """
        fresh = self._fresh(locale)
        if fresh is not None:
            return fresh
        entry = self._cache.get(locale)
        if entry is not None:
            self._refresh_in_background(locale)
            return entry.translations
        with self._lock_for(locale):
            entry = self._cache.get(locale)
            if entry is not None:
                return entry.translations
            return self._store(locale, self._load_blocking(locale))

    def load_all_blocking(self, locales: list[str]) -> None:
        """Eagerly fetch translations for all *locales* from synchronous code, waiting for every load."""
        stale = [loc for loc in locales if self._fresh(loc) is None]
        if stale:
            with ThreadPoolExecutor() as pool:
                list(pool.map(self._load_locked, stale))

    def get_translations_sync(self, locale: str) -> dict[str, str]:
        """Return the last loaded translations, even if expired, or an empty dict (never blocks)."""
        entry = self._cache.get(locale)
        return entry.translations if entry is not None else {}

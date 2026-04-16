"""Inner cache: hash → translation with batched runtime fetch.

Port of the JS ``TranslationsCache`` introduced in gt PR #1207. One instance
per locale. Batches concurrent misses into ``translate_many`` calls, dedups
in-flight requests for the same hash, and caps concurrent HTTP calls.

Usage (typically instantiated by ``LocalesCache``):

    cache = TranslationsCache(
        locale="es",
        translate_many=lambda sources: gt.translate_many(sources, {"target_locale": "es"}),
        initial={"h1": "Hola"},  # translations pre-loaded for the locale
    )
    cached = cache.get({"message": "Hello", "options": {"_format": "STRING"}})     # sync
    translation = await cache.miss({"message": "Hi", "options": {"_format": "STRING"}})  # async
"""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from typing import Any, cast

from generaltranslation._id._hash import hash_source
from generaltranslation.static._index_vars import index_vars

from gt_i18n.i18n_manager._lifecycle import LifecycleCallbacks


def _compute_hash(message: str, options: dict[str, Any]) -> str:
    """Compute the cache hash for a (message, options) lookup key.

    Mirrors ``hash_message`` semantics but inlined to avoid a circular import
    through ``gt_i18n.translation_functions`` (whose ``__init__.py`` imports
    ``_t`` which depends on the I18nManager this cache is owned by).
    """
    fmt = options.get("_format", "ICU")
    source = index_vars(message) if fmt == "ICU" else message
    return hash_source(
        source,
        context=options.get("_context"),
        id=options.get("_id"),
        max_chars=options.get("_max_chars"),
        data_format=fmt,
    )


def _build_metadata(hash_: str, options: dict[str, Any]) -> dict[str, Any]:
    """Build the camelCase metadata block for the translate_many wire body."""
    metadata: dict[str, Any] = {
        "hash": hash_,
        "dataFormat": options.get("_format", "ICU"),
    }
    if options.get("_context") is not None:
        metadata["context"] = options["_context"]
    if options.get("_id") is not None:
        metadata["id"] = options["_id"]
    if options.get("_max_chars") is not None:
        metadata["maxChars"] = options["_max_chars"]
    return metadata


class TranslationsCache:
    """Hash-keyed cache with batched runtime translate fetch.

    Constructor kwargs:
        locale: The target locale this cache serves.
        translate_many: Async callable ``(sources_dict) -> response_dict`` pre-bound
            to this locale (see ``_translate_many_factory``).
        initial: Optional seed translations loaded from the user's loader.
        batch_size: Maximum entries per ``translate_many`` call. Default 25.
        batch_interval_ms: Debounce interval before draining the queue. Default 50ms.
        max_concurrent_requests: Cap on simultaneous in-flight ``translate_many``
            calls. Default 100.
        lifecycle: Optional observability callbacks.
    """

    def __init__(
        self,
        *,
        locale: str,
        translate_many: Callable[[dict[str, Any]], Awaitable[dict[str, Any]]],
        initial: dict[str, str] | None = None,
        batch_size: int = 25,
        batch_interval_ms: int = 50,
        max_concurrent_requests: int = 100,
        lifecycle: LifecycleCallbacks | None = None,
    ) -> None:
        self._locale = locale
        self._translate_many = translate_many
        self._cache: dict[str, str] = dict(initial or {})
        self._pending: dict[str, asyncio.Future[str | None]] = {}
        self._queue: list[tuple[str, str, dict[str, Any]]] = []  # [(hash, message, options)]
        self._batch_size = batch_size
        self._batch_interval_ms = batch_interval_ms
        self._max_concurrent_requests = max_concurrent_requests
        self._lifecycle: LifecycleCallbacks = lifecycle or {}
        self._batch_timer: asyncio.Task[None] | None = None
        self._active_requests = 0

    # -- public ------------------------------------------------------------

    def get(self, key: dict[str, Any]) -> str | None:
        """Synchronous lookup. Fires ``on_translations_cache_hit`` if cached."""
        message = key["message"]
        options = key.get("options", {})
        hash_ = _compute_hash(message, options)
        value = self._cache.get(hash_)
        if value is not None:
            self._fire("on_translations_cache_hit", locale=self._locale, hash=hash_, value=value)
            return value
        return None

    async def miss(self, key: dict[str, Any]) -> str | None:
        """Return cached value, dedup in-flight, or enqueue a runtime fetch."""
        message = key["message"]
        options = key.get("options", {})
        hash_ = _compute_hash(message, options)

        # Cache hit
        if hash_ in self._cache:
            value = self._cache[hash_]
            self._fire("on_translations_cache_hit", locale=self._locale, hash=hash_, value=value)
            return value

        # Dedup in-flight
        if hash_ in self._pending:
            return await self._pending[hash_]

        # New miss — enqueue + await
        loop = asyncio.get_running_loop()
        future: asyncio.Future[str | None] = loop.create_future()
        self._pending[hash_] = future
        self._queue.append((hash_, message, options))

        if len(self._queue) >= self._batch_size:
            self._drain_queue()
        else:
            self._schedule_batch()

        return await future

    # -- batching ----------------------------------------------------------

    def _schedule_batch(self) -> None:
        """Start a batch timer if none is currently running."""
        if self._batch_timer is None or self._batch_timer.done():
            self._batch_timer = asyncio.create_task(self._timer_body())

    async def _timer_body(self) -> None:
        """Sleep for the batch interval, then drain whatever's queued."""
        await asyncio.sleep(self._batch_interval_ms / 1000)
        self._drain_queue()

    def _drain_queue(self) -> None:
        """Split the queue into batches and spawn send tasks (respecting concurrency cap)."""
        while self._queue and self._active_requests < self._max_concurrent_requests:
            batch = self._queue[: self._batch_size]
            del self._queue[: self._batch_size]
            self._active_requests += 1
            asyncio.create_task(self._send_batch(batch))

    async def _send_batch(self, batch: list[tuple[str, str, dict[str, Any]]]) -> None:
        """Build the request, call translate_many, resolve per-entry futures."""
        try:
            sources = {
                hash_: {"source": message, "metadata": _build_metadata(hash_, options)}
                for hash_, message, options in batch
            }
            try:
                response = await self._translate_many(sources)
            except BaseException as exc:  # noqa: BLE001 — propagate to all awaiters
                for hash_, _, _ in batch:
                    fut = self._pending.pop(hash_, None)
                    if fut is not None and not fut.done():
                        fut.set_exception(exc)
                return

            for hash_, _message, _options in batch:
                result: dict[str, Any] = response.get(hash_) or {"success": False}
                fut = self._pending.pop(hash_, None)
                if result.get("success"):
                    value = cast(str, result["translation"])
                    self._cache[hash_] = value
                    self._fire("on_translations_cache_miss", locale=self._locale, hash=hash_, value=value)
                    if fut is not None and not fut.done():
                        fut.set_result(value)
                else:
                    # Failure: do NOT cache; resolve future with None so callers fall back.
                    if fut is not None and not fut.done():
                        fut.set_result(None)
        finally:
            self._active_requests -= 1
            # Admit any waiting batches now that a slot has opened up.
            self._drain_queue()

    # -- lifecycle helpers -------------------------------------------------

    def _fire(self, name: str, **kwargs: Any) -> None:
        cb = cast(Callable[..., Any] | None, self._lifecycle.get(name))  # type: ignore[misc]
        if cb is not None:
            cb(**kwargs)

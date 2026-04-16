"""Golden-standard tests for ``LocalesCache``.

``LocalesCache`` is the outer cache in the two-level hierarchy introduced by
gt PR #1207. It maps ``locale → TranslationsCache``, enforces a TTL, and
invokes the user's ``load_translations`` loader exactly once per locale
per TTL window (with concurrent callers deduped via the same in-flight task).

These tests lock the externally-observable behavior. They exercise the
private ``_locales_cache`` module directly because ``LocalesCache`` is the
contract that ``I18nManager`` depends on — if the shape changes, callers
upstream break.

All tests in this file should FAIL until PR #1207 is ported (the module,
class, and constructor kwargs don't exist yet).
"""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from typing import Any

import pytest

# Imports deliberately reference the not-yet-existent modules. These will
# ImportError until implementation lands — that's the point of the golden tests.
from gt_i18n.i18n_manager._locales_cache import LocalesCache  # noqa: E402


def _noop_translate_many_factory(locale: str) -> Callable[[dict[str, Any]], Awaitable[dict[str, Any]]]:
    """Dummy ``create_translate_many`` factory — returns a callable that never runs.

    LocalesCache tests don't exercise runtime translation; they only care about the
    locale-level loader behavior. Pass this when the test doesn't use translate_many.
    """

    async def _never(sources: dict[str, Any]) -> dict[str, Any]:
        raise AssertionError("translate_many should not be called by LocalesCache tests")

    return _never


# ---------------------------------------------------------------------------
# test_miss_calls_loader_once
#
# Example:
#     cache = LocalesCache(load_translations=loader, ...)
#     await cache.miss("es")  # loader invoked, result cached
#     await cache.miss("es")  # within TTL: cached, loader NOT invoked again
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_miss_calls_loader_once() -> None:
    """Within the TTL window, a locale's loader is called once even across multiple misses."""
    call_count = 0

    def loader(locale: str) -> dict[str, str]:
        nonlocal call_count
        call_count += 1
        return {"hash_greeting": "Hola"}

    cache = LocalesCache(
        load_translations=loader,
        create_translate_many=_noop_translate_many_factory,
        ttl_ms=60_000,
    )

    first = await cache.miss("es")
    second = await cache.miss("es")

    assert call_count == 1, "loader should have been invoked exactly once"
    # Both calls return the same TranslationsCache instance — we have a single canonical cache per locale.
    assert first is second


# ---------------------------------------------------------------------------
# test_expired_entry_triggers_reload
#
# Example:
#     cache = LocalesCache(ttl_ms=10, ...)
#     await cache.miss("es")
#     await asyncio.sleep(0.02)   # exceed the 10ms TTL
#     await cache.miss("es")       # loader invoked again
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_expired_entry_triggers_reload() -> None:
    """After the TTL elapses, the next access re-invokes the loader."""
    call_count = 0

    def loader(locale: str) -> dict[str, str]:
        nonlocal call_count
        call_count += 1
        return {}

    cache = LocalesCache(
        load_translations=loader,
        create_translate_many=_noop_translate_many_factory,
        ttl_ms=10,  # 10ms TTL for fast test
    )

    await cache.miss("es")
    assert call_count == 1
    await asyncio.sleep(0.02)  # 20ms > 10ms TTL
    await cache.miss("es")
    assert call_count == 2, "loader should have been re-invoked after TTL expiry"


# ---------------------------------------------------------------------------
# test_concurrent_miss_for_same_locale_dedups
#
# Mirrors the JS Cache.fallbackPromises pattern: if two callers miss() for the
# same locale while the loader is still in flight, they share one task and
# one loader invocation.
#
# Example:
#     async def slow_loader(locale):
#         await asyncio.sleep(0.02)
#         return {}
#     results = await asyncio.gather(cache.miss("es"), cache.miss("es"))
#     # loader called ONCE
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_concurrent_miss_for_same_locale_dedups() -> None:
    """Concurrent misses for the same locale share one in-flight loader task."""
    call_count = 0

    async def slow_loader(locale: str) -> dict[str, str]:
        nonlocal call_count
        call_count += 1
        await asyncio.sleep(0.02)
        return {"hash_greeting": "Bonjour"}

    cache = LocalesCache(
        load_translations=slow_loader,
        create_translate_many=_noop_translate_many_factory,
        ttl_ms=60_000,
    )

    a, b, c = await asyncio.gather(cache.miss("fr"), cache.miss("fr"), cache.miss("fr"))

    assert call_count == 1, "concurrent misses should dedupe to a single loader invocation"
    assert a is b is c, "all concurrent callers should receive the same TranslationsCache"


# ---------------------------------------------------------------------------
# test_loader_exception_does_not_poison_cache
#
# If the loader raises once, the next miss() should retry — a poisoned cache
# would leave the locale permanently broken.
#
# Example:
#     counter = [0]
#     def flaky_loader(locale):
#         counter[0] += 1
#         if counter[0] == 1:
#             raise RuntimeError("transient")
#         return {"hash_x": "OK"}
#     # first miss raises; second miss succeeds.
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_loader_exception_does_not_poison_cache() -> None:
    """A loader failure is transient — subsequent misses retry and can succeed."""
    attempts = 0

    def flaky_loader(locale: str) -> dict[str, str]:
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            raise RuntimeError("transient network failure")
        return {"hash_x": "OK"}

    cache = LocalesCache(
        load_translations=flaky_loader,
        create_translate_many=_noop_translate_many_factory,
        ttl_ms=60_000,
    )

    with pytest.raises(RuntimeError, match="transient"):
        await cache.miss("de")

    # Second attempt should retry the loader — NOT return cached failure.
    result = await cache.miss("de")
    assert attempts == 2
    assert result is not None


# ---------------------------------------------------------------------------
# test_on_locales_cache_miss_fires_on_loader_invocation
#
# The lifecycle callback receives the resolved ``value`` (dict of translations
# from the loader) along with the locale.
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_on_locales_cache_miss_fires_on_loader_invocation() -> None:
    """``on_locales_cache_miss`` fires with the loaded translations payload."""
    observed: list[dict[str, Any]] = []

    def on_miss(*, locale: str, value: dict[str, str]) -> None:
        observed.append({"locale": locale, "value": value})

    def loader(locale: str) -> dict[str, str]:
        return {"hash_a": "A", "hash_b": "B"}

    cache = LocalesCache(
        load_translations=loader,
        create_translate_many=_noop_translate_many_factory,
        ttl_ms=60_000,
        lifecycle={"on_locales_cache_miss": on_miss},
    )

    await cache.miss("es")

    assert len(observed) == 1
    assert observed[0]["locale"] == "es"
    assert observed[0]["value"] == {"hash_a": "A", "hash_b": "B"}


# ---------------------------------------------------------------------------
# test_on_locales_cache_hit_fires_on_cached_access
#
# When a cached locale is re-accessed within the TTL, ``on_locales_cache_hit``
# fires (and ``on_locales_cache_miss`` does not fire on that access).
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_on_locales_cache_hit_fires_on_cached_access() -> None:
    """``on_locales_cache_hit`` fires on repeated access within TTL; miss does not re-fire."""
    hits: list[dict[str, Any]] = []
    misses: list[dict[str, Any]] = []

    cache = LocalesCache(
        load_translations=lambda locale: {"hash_a": "A"},
        create_translate_many=_noop_translate_many_factory,
        ttl_ms=60_000,
        lifecycle={
            "on_locales_cache_hit": lambda *, locale, value: hits.append({"locale": locale, "value": value}),
            "on_locales_cache_miss": lambda *, locale, value: misses.append({"locale": locale, "value": value}),
        },
    )

    # First access: miss fires.
    await cache.miss("es")
    assert len(misses) == 1
    assert len(hits) == 0

    # Second access: hit fires; miss does not fire again.
    # Note: `get()` is the sync accessor — it returns the TranslationsCache if cached.
    cached = cache.get("es")
    assert cached is not None
    assert len(hits) == 1
    assert hits[0] == {"locale": "es", "value": {"hash_a": "A"}}
    assert len(misses) == 1  # unchanged

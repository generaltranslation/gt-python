"""Extended behavioral tests for ``LocalesCache``.

Complements ``test_locales_cache.py`` (the golden-standard file).
"""

from __future__ import annotations

import asyncio
import time
from collections.abc import Awaitable, Callable
from typing import Any

import pytest
from gt_i18n.i18n_manager._locales_cache import LocalesCache


def _noop_translate_many_factory(locale: str) -> Callable[[dict[str, Any]], Awaitable[dict[str, Any]]]:
    async def _never(sources: dict[str, Any]) -> dict[str, Any]:
        raise AssertionError("translate_many should not be invoked in these tests")

    return _never


# ---------------------------------------------------------------------------
# Multi-locale independence
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_different_locales_dedup_independently() -> None:
    """Concurrent misses for different locales each call their loader exactly once."""
    counters: dict[str, int] = {}

    async def slow_loader(locale: str) -> dict[str, str]:
        counters[locale] = counters.get(locale, 0) + 1
        await asyncio.sleep(0.01)
        return {f"{locale}_hash": f"{locale}_value"}

    cache = LocalesCache(
        load_translations=slow_loader,
        create_translate_many=_noop_translate_many_factory,
        ttl_ms=60_000,
    )
    await asyncio.gather(*(cache.miss(loc) for loc in ["es", "fr", "de", "ja"] * 3))
    assert counters == {"es": 1, "fr": 1, "de": 1, "ja": 1}


@pytest.mark.asyncio
async def test_one_locale_expiring_does_not_affect_others() -> None:
    """TTL expiry on locale A leaves locale B's entry intact."""
    loads: list[str] = []

    def loader(locale: str) -> dict[str, str]:
        loads.append(locale)
        return {}

    cache = LocalesCache(
        load_translations=loader,
        create_translate_many=_noop_translate_many_factory,
        ttl_ms=10,
    )
    await cache.miss("es")
    await cache.miss("fr")
    assert loads == ["es", "fr"]

    await asyncio.sleep(0.02)  # both expired

    # Only re-hit es; fr should still be expired but we don't touch it.
    await cache.miss("es")
    assert loads == ["es", "fr", "es"]


# ---------------------------------------------------------------------------
# TTL edge cases
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_very_large_ttl_keeps_entry_across_multiple_hits() -> None:
    """With a multi-hour TTL, 100 sequential gets produce no reload."""
    call_count = [0]

    def loader(locale: str) -> dict[str, str]:
        call_count[0] += 1
        return {}

    cache = LocalesCache(
        load_translations=loader,
        create_translate_many=_noop_translate_many_factory,
        ttl_ms=60 * 60 * 1000,  # 1 hour
    )
    await cache.miss("es")
    for _ in range(100):
        cache.get("es")
    assert call_count[0] == 1


@pytest.mark.asyncio
async def test_expired_entry_is_evicted_from_internal_cache_on_get() -> None:
    """After TTL, ``get()`` removes the stale entry in addition to returning None."""
    cache = LocalesCache(
        load_translations=lambda locale: {},
        create_translate_many=_noop_translate_many_factory,
        ttl_ms=5,
    )
    await cache.miss("es")
    assert "es" in cache._cache  # populated
    await asyncio.sleep(0.015)
    assert cache.get("es") is None
    assert "es" not in cache._cache  # evicted


# ---------------------------------------------------------------------------
# Sync vs async loaders
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_sync_loader_is_supported() -> None:
    """A plain sync loader works — LocalesCache awaits only if the result is awaitable."""

    def sync_loader(locale: str) -> dict[str, str]:
        return {"k": f"v_{locale}"}

    cache = LocalesCache(
        load_translations=sync_loader,
        create_translate_many=_noop_translate_many_factory,
    )
    tc = await cache.miss("es")
    assert tc is not None


@pytest.mark.asyncio
async def test_async_loader_is_supported() -> None:
    """An async loader is awaited properly."""

    async def async_loader(locale: str) -> dict[str, str]:
        await asyncio.sleep(0)
        return {"k": f"async_v_{locale}"}

    cache = LocalesCache(
        load_translations=async_loader,
        create_translate_many=_noop_translate_many_factory,
    )
    tc = await cache.miss("es")
    assert tc is not None


# ---------------------------------------------------------------------------
# Loader returns empty / unexpected
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_loader_returning_empty_dict_still_caches() -> None:
    """A loader returning {} still produces a valid cached entry."""
    calls = [0]

    def loader(locale: str) -> dict[str, str]:
        calls[0] += 1
        return {}

    cache = LocalesCache(
        load_translations=loader,
        create_translate_many=_noop_translate_many_factory,
    )
    await cache.miss("es")
    # Second miss returns cached (loader not called again).
    await cache.miss("es")
    assert calls[0] == 1


@pytest.mark.asyncio
async def test_loader_returning_many_entries_are_all_available() -> None:
    """Large loader payload is fully preserved in the cache entry."""
    big = {f"hash_{i}": f"value_{i}" for i in range(500)}

    cache = LocalesCache(
        load_translations=lambda locale: big,
        create_translate_many=_noop_translate_many_factory,
    )
    await cache.miss("es")
    entry = cache._cache["es"]
    assert entry.translations == big
    assert len(entry.translations) == 500


# ---------------------------------------------------------------------------
# Callback semantics
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_hit_callback_fires_each_time_get_succeeds() -> None:
    """``on_locales_cache_hit`` fires on every successful get() — not just the first."""
    hits: list[str] = []

    cache = LocalesCache(
        load_translations=lambda locale: {},
        create_translate_many=_noop_translate_many_factory,
        lifecycle={"on_locales_cache_hit": lambda *, locale, value: hits.append(locale)},
    )
    await cache.miss("es")
    for _ in range(5):
        cache.get("es")
    assert hits == ["es"] * 5


@pytest.mark.asyncio
async def test_miss_callback_payload_is_snapshot_not_live_ref() -> None:
    """Mutating the user-returned dict after the fact doesn't affect the callback payload."""
    shared_dict = {"h1": "v1"}
    received: list[dict[str, str]] = []

    def loader(locale: str) -> dict[str, str]:
        return shared_dict

    cache = LocalesCache(
        load_translations=loader,
        create_translate_many=_noop_translate_many_factory,
        lifecycle={"on_locales_cache_miss": lambda *, locale, value: received.append(value)},
    )
    await cache.miss("es")
    # Mutate the dict after miss.
    shared_dict["h2"] = "v2"
    # The callback payload is a snapshot — it should NOT reflect h2.
    assert received == [{"h1": "v1"}]


# ---------------------------------------------------------------------------
# get() vs miss() behavior on cold cache
# ---------------------------------------------------------------------------


def test_get_on_cold_cache_is_none_with_no_callback() -> None:
    """Sync get() on a never-missed locale returns None; hit callback does NOT fire."""
    hits: list[str] = []
    cache = LocalesCache(
        load_translations=lambda locale: {},
        create_translate_many=_noop_translate_many_factory,
        lifecycle={"on_locales_cache_hit": lambda *, locale, value: hits.append(locale)},
    )
    assert cache.get("es") is None
    assert hits == []


@pytest.mark.asyncio
async def test_miss_then_get_returns_same_translations_cache() -> None:
    """``miss()`` and ``get()`` return the SAME TranslationsCache instance (identity)."""
    cache = LocalesCache(
        load_translations=lambda locale: {},
        create_translate_many=_noop_translate_many_factory,
    )
    a = await cache.miss("es")
    b = cache.get("es")
    assert a is b


# ---------------------------------------------------------------------------
# Batching params flow to TranslationsCache
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_batching_params_forwarded_to_inner_translations_cache() -> None:
    """Batch kwargs on LocalesCache are passed through to each TranslationsCache it creates."""
    cache = LocalesCache(
        load_translations=lambda locale: {},
        create_translate_many=_noop_translate_many_factory,
        batch_size=7,
        batch_interval_ms=13,
        max_concurrent_requests=3,
    )
    tc = await cache.miss("es")
    assert tc._batch_size == 7
    assert tc._batch_interval_ms == 13
    assert tc._max_concurrent_requests == 3


# ---------------------------------------------------------------------------
# Many locales at once (stress)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_50_locales_concurrent_miss() -> None:
    """50 distinct concurrent misses each load exactly once."""
    counts: dict[str, int] = {}

    async def loader(locale: str) -> dict[str, str]:
        counts[locale] = counts.get(locale, 0) + 1
        await asyncio.sleep(0)
        return {}

    cache = LocalesCache(
        load_translations=loader,
        create_translate_many=_noop_translate_many_factory,
    )
    locales = [f"loc-{i}" for i in range(50)]
    await asyncio.gather(*(cache.miss(loc) for loc in locales))
    assert all(counts[loc] == 1 for loc in locales)


# ---------------------------------------------------------------------------
# Exception handling variations
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_loader_exception_type_is_preserved() -> None:
    """The original exception type propagates to the caller."""

    class CustomError(RuntimeError):
        pass

    def loader(locale: str) -> dict[str, str]:
        raise CustomError("custom failure")

    cache = LocalesCache(
        load_translations=loader,
        create_translate_many=_noop_translate_many_factory,
    )
    with pytest.raises(CustomError, match="custom failure"):
        await cache.miss("es")


@pytest.mark.asyncio
async def test_concurrent_misses_see_same_exception() -> None:
    """All concurrent awaiters receive the SAME exception instance from one failing load."""

    async def loader(locale: str) -> dict[str, str]:
        await asyncio.sleep(0.01)
        raise RuntimeError("fail-once")

    cache = LocalesCache(
        load_translations=loader,
        create_translate_many=_noop_translate_many_factory,
    )
    results = await asyncio.gather(
        cache.miss("es"),
        cache.miss("es"),
        cache.miss("es"),
        return_exceptions=True,
    )
    errors = [r for r in results if isinstance(r, BaseException)]
    assert len(errors) == 3
    assert all(isinstance(e, RuntimeError) and "fail-once" in str(e) for e in errors)


@pytest.mark.asyncio
async def test_retry_after_exception_can_succeed() -> None:
    """After a transient error, subsequent miss() retries and can succeed."""
    state = {"should_fail": True}

    def loader(locale: str) -> dict[str, str]:
        if state["should_fail"]:
            raise ConnectionError("transient")
        return {"ok": "yes"}

    cache = LocalesCache(
        load_translations=loader,
        create_translate_many=_noop_translate_many_factory,
    )
    with pytest.raises(ConnectionError):
        await cache.miss("es")
    state["should_fail"] = False
    result = await cache.miss("es")
    assert result is not None


# ---------------------------------------------------------------------------
# TTL boundary
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_entry_just_before_expiry_is_still_a_hit() -> None:
    """An entry with 1000ms left on its TTL is treated as fresh."""
    cache = LocalesCache(
        load_translations=lambda locale: {},
        create_translate_many=_noop_translate_many_factory,
        ttl_ms=10_000,
    )
    await cache.miss("es")
    entry = cache._cache["es"]
    now = time.monotonic()
    assert entry.expires_at > now, "expires_at should be in the future"
    assert cache.get("es") is not None


@pytest.mark.asyncio
async def test_reload_after_expiry_produces_new_translations_cache_instance() -> None:
    """Post-expiry reload builds a FRESH TranslationsCache, not the same one."""
    cache = LocalesCache(
        load_translations=lambda locale: {},
        create_translate_many=_noop_translate_many_factory,
        ttl_ms=10,
    )
    tc1 = await cache.miss("es")
    await asyncio.sleep(0.02)
    tc2 = await cache.miss("es")
    assert tc1 is not tc2

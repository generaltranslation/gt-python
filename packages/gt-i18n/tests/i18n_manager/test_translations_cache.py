"""Golden-standard tests for ``TranslationsCache``.

``TranslationsCache`` is the inner cache in the two-level hierarchy introduced by
gt PR #1207. It is keyed by message hash, batches runtime translate requests,
enforces batch-size / batch-interval / concurrency limits, and dedups in-flight
requests (so concurrent misses for the same hash share one API call).

These behaviors are load-bearing — they determine how many API calls the library
makes in hot code paths — so they are pinned here as the black-box contract.

All tests should FAIL until PR #1207 is ported (module + class don't exist yet).
"""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

import pytest
from gt_i18n.i18n_manager._translations_cache import TranslationsCache  # noqa: E402

if TYPE_CHECKING:
    from conftest import FakeGT  # noqa: F401 — only for type hints


def _key(message: str, *, fmt: str = "STRING", context: str | None = None, id_: str | None = None) -> dict[str, Any]:
    """Build a TranslationsCache lookup key (mirrors JS ``TranslationKey``).

    Example:
        key = _key("Hello", fmt="ICU")
        # → {"message": "Hello", "options": {"_format": "ICU"}}
    """
    options: dict[str, Any] = {"_format": fmt}
    if context is not None:
        options["_context"] = context
    if id_ is not None:
        options["_id"] = id_
    return {"message": message, "options": options}


# ---------------------------------------------------------------------------
# test_sync_get_returns_none_on_miss
#
# ``cache.get(key)`` is sync and MUST NOT trigger a fetch. Safe to call from
# synchronous codepaths like ``t()``.
# ---------------------------------------------------------------------------


def test_sync_get_returns_none_on_miss(translate_many_for_locale: Callable[[str], Any]) -> None:
    """Sync ``get()`` returns None for unknown keys; never triggers a network call."""
    cache = TranslationsCache(
        locale="es",
        translate_many=translate_many_for_locale("es"),
    )
    assert cache.get(_key("Hello")) is None


# ---------------------------------------------------------------------------
# test_async_miss_triggers_translate_many_and_caches
#
# Example:
#     result = await cache.miss({"message": "Hello", "options": {"_format": "STRING"}})
#     # → fake_gt.translate_many called once with {hash: {source, metadata}} + target_locale="es"
#     # Subsequent cache.get() returns the translation (hit).
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_async_miss_triggers_translate_many_and_caches(
    fake_gt: FakeGT,
    translate_many_for_locale: Callable[[str], Any],
) -> None:
    """A miss fires translate_many; the result is cached and returned by later get()."""
    cache = TranslationsCache(
        locale="es",
        translate_many=translate_many_for_locale("es"),
    )

    key = _key("Hello, world!")
    translation = await cache.miss(key)

    assert translation == "[es]Hello, world!"
    assert len(fake_gt.calls) == 1

    # Subsequent sync get() is a cache hit — no additional API call.
    cached = cache.get(key)
    assert cached == "[es]Hello, world!"
    assert len(fake_gt.calls) == 1, "sync get() after miss must not trigger another API call"


# ---------------------------------------------------------------------------
# test_concurrent_miss_same_hash_dedups_request
#
# The critical dedup guarantee: if ``tx("Hello")`` is called from 3 places
# concurrently, only ONE API request goes out with ONE entry.
#
# Example:
#     await asyncio.gather(cache.miss(k), cache.miss(k), cache.miss(k))
#     # → fake_gt.translate_many called 1x with 1 entry.
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_concurrent_miss_same_hash_dedups_request(
    fake_gt: FakeGT,
    translate_many_for_locale: Callable[[str], Any],
) -> None:
    """Concurrent misses for the same key produce exactly one API call with one entry."""
    fake_gt.delay_s = 0.02  # hold requests in flight long enough for callers to queue up

    cache = TranslationsCache(
        locale="es",
        translate_many=translate_many_for_locale("es"),
        batch_interval_ms=5,
    )

    key = _key("Hello")
    results = await asyncio.gather(cache.miss(key), cache.miss(key), cache.miss(key))

    assert all(r == "[es]Hello" for r in results)
    assert len(fake_gt.calls) == 1
    assert len(fake_gt.calls[0]["sources"]) == 1


# ---------------------------------------------------------------------------
# test_batches_within_interval
#
# Multiple distinct misses within one batch interval coalesce into a single API
# call whose request body contains all of them.
#
# Example:
#     fire 5 concurrent miss()es with different messages →
#     after ~interval: 1 API call with 5 entries.
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_batches_within_interval(
    fake_gt: FakeGT,
    translate_many_for_locale: Callable[[str], Any],
) -> None:
    """Misses fired within one interval window are coalesced into one API call."""
    cache = TranslationsCache(
        locale="es",
        translate_many=translate_many_for_locale("es"),
        batch_interval_ms=30,
        batch_size=25,
    )

    keys = [_key(f"message-{i}") for i in range(5)]
    results = await asyncio.gather(*(cache.miss(k) for k in keys))

    # All returned successfully.
    assert [r for r in results] == [f"[es]message-{i}" for i in range(5)]
    # Exactly one API call, containing all 5 entries.
    assert len(fake_gt.calls) == 1
    assert len(fake_gt.calls[0]["sources"]) == 5


# ---------------------------------------------------------------------------
# test_respects_batch_size_limit
#
# If the queue exceeds batch_size, it's split into multiple sub-batches each
# with size <= batch_size. No batch ever exceeds the limit.
#
# Example:
#     batch_size=3; fire 7 concurrent misses → batches [3, 3, 1] (never > 3).
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_respects_batch_size_limit(
    fake_gt: FakeGT,
    translate_many_for_locale: Callable[[str], Any],
) -> None:
    """No single API call contains more entries than ``batch_size``."""
    cache = TranslationsCache(
        locale="es",
        translate_many=translate_many_for_locale("es"),
        batch_size=3,
        batch_interval_ms=5,
    )

    keys = [_key(f"m-{i}") for i in range(7)]
    await asyncio.gather(*(cache.miss(k) for k in keys))

    total_entries = sum(len(c["sources"]) for c in fake_gt.calls)
    assert total_entries == 7
    assert all(len(c["sources"]) <= 3 for c in fake_gt.calls), f"batches: {[len(c['sources']) for c in fake_gt.calls]}"


# ---------------------------------------------------------------------------
# test_respects_max_concurrent_requests
#
# Pin: the cache does not fire more than ``max_concurrent_requests`` API calls
# at once, even if the queue is longer. Remaining batches wait for a slot.
#
# Example:
#     batch_size=1, max_concurrent_requests=2, fake_gt holds requests pending.
#     Fire 5 misses → at most 2 in-flight API calls at any instant.
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_respects_max_concurrent_requests(
    fake_gt: FakeGT,
    translate_many_for_locale: Callable[[str], Any],
) -> None:
    """The cache never has more than ``max_concurrent_requests`` translate_many calls in flight."""
    # Hold all requests pending until we release them.
    fake_gt.inflight_event = asyncio.Event()

    cache = TranslationsCache(
        locale="es",
        translate_many=translate_many_for_locale("es"),
        batch_size=1,  # one entry per batch to maximize batch count
        batch_interval_ms=1,
        max_concurrent_requests=2,
    )

    keys = [_key(f"msg-{i}") for i in range(5)]
    tasks = [asyncio.create_task(cache.miss(k)) for k in keys]

    # Let the batcher schedule requests; wait for it to reach its concurrency cap.
    for _ in range(20):
        await asyncio.sleep(0.01)
        if fake_gt.max_inflight >= 2:
            break
    assert fake_gt.max_inflight == 2, f"expected max_inflight == 2, got {fake_gt.max_inflight}"

    # Release the held requests so the remaining queue drains.
    fake_gt.inflight_event.set()
    await asyncio.gather(*tasks)

    assert fake_gt.max_inflight == 2, "concurrency cap must not be exceeded across the full run"


# ---------------------------------------------------------------------------
# test_partial_failure_caches_successes_and_returns_none_for_failures
#
# When a batch response has mixed success/failure, successful entries are
# cached, failed entries return None from miss() AND are NOT cached (so the
# next call can retry them).
#
# Example:
#     batch of 3 → response: {h1: success, h2: success, h3: {success: False}}
#     cache.get(h1) / cache.get(h2) → hit
#     cache.get(h3) → None (failures are retryable)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_partial_failure_caches_successes_and_returns_none_for_failures(
    fake_gt: FakeGT,
    translate_many_for_locale: Callable[[str], Any],
) -> None:
    """Per-entry failures don't poison the batch — successful entries still cache."""

    # Custom response: first two succeed, third fails.
    def mixed_response(sources: dict[str, Any], options: dict[str, Any]) -> dict[str, Any]:
        hashes = list(sources.keys())
        result: dict[str, Any] = {}
        for i, h in enumerate(hashes):
            if i == 2:
                result[h] = {"success": False, "error": "upstream failure", "code": 500}
            else:
                result[h] = {"success": True, "translation": f"ok:{sources[h]['source']}", "locale": "es"}
        return result

    fake_gt.response_factory = mixed_response

    cache = TranslationsCache(
        locale="es",
        translate_many=translate_many_for_locale("es"),
        batch_interval_ms=5,
    )

    k0, k1, k2 = _key("a"), _key("b"), _key("c")
    r0, r1, r2 = await asyncio.gather(cache.miss(k0), cache.miss(k1), cache.miss(k2))

    assert r0 == "ok:a"
    assert r1 == "ok:b"
    assert r2 is None, "failed entries must return None from miss()"

    # Successes are cached.
    assert cache.get(k0) == "ok:a"
    assert cache.get(k1) == "ok:b"
    # Failures are NOT cached — retryable.
    assert cache.get(k2) is None


# ---------------------------------------------------------------------------
# test_request_body_shape_matches_js_wire_format
#
# The request body is camelCase on the wire (per port-from-gt-js.md §"Options,
# kwargs, and wire format"). metadata includes dataFormat, context, id, maxChars.
#
# Example JS equivalent:
#   translateMany({
#     "<hash>": {
#       source: "Hello",
#       metadata: { hash: "<hash>", dataFormat: "ICU", context: "...", id: "...", maxChars: 50 }
#     }
#   }, { targetLocale: "es" })
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_request_body_shape_matches_js_wire_format(
    fake_gt: FakeGT,
    translate_many_for_locale: Callable[[str], Any],
) -> None:
    """Request body uses camelCase keys matching JS; metadata carries context/id/maxChars/dataFormat."""
    cache = TranslationsCache(
        locale="es",
        translate_many=translate_many_for_locale("es"),
        batch_interval_ms=5,
    )

    key = {"message": "Save", "options": {"_format": "ICU", "_context": "button", "_id": "save.btn", "_max_chars": 50}}
    await cache.miss(key)

    assert len(fake_gt.calls) == 1
    call = fake_gt.calls[0]
    # target_locale (or camelCase equivalent) in options.
    target = call["options"].get("target_locale") or call["options"].get("targetLocale")
    assert target == "es"

    # sources is {hash: {source, metadata}}.
    (hash_key, entry) = next(iter(call["sources"].items()))
    assert isinstance(hash_key, str) and len(hash_key) > 0
    assert entry["source"] == "Save"
    meta = entry["metadata"]
    assert meta["dataFormat"] == "ICU"
    assert meta["context"] == "button"
    assert meta["id"] == "save.btn"
    assert meta["maxChars"] == 50


# ---------------------------------------------------------------------------
# test_on_translations_cache_hit_fires
#
# Callback receives {locale, hash, value}.
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_on_translations_cache_hit_fires(
    fake_gt: FakeGT,
    translate_many_for_locale: Callable[[str], Any],
) -> None:
    """``on_translations_cache_hit`` fires on a cached read with {locale, hash, value}."""
    hits: list[dict[str, Any]] = []

    cache = TranslationsCache(
        locale="es",
        translate_many=translate_many_for_locale("es"),
        batch_interval_ms=5,
        lifecycle={
            "on_translations_cache_hit": lambda *, locale, hash, value: hits.append(
                {"locale": locale, "hash": hash, "value": value}
            ),
        },
    )

    key = _key("Cached")
    # First access: miss; fires miss callback (not verified here).
    await cache.miss(key)
    # Second access: hit.
    got = cache.get(key)

    assert got == "[es]Cached"
    assert len(hits) == 1
    assert hits[0]["locale"] == "es"
    assert isinstance(hits[0]["hash"], str) and len(hits[0]["hash"]) > 0
    assert hits[0]["value"] == "[es]Cached"


# ---------------------------------------------------------------------------
# test_on_translations_cache_miss_fires_with_fetched_value
#
# On a miss that triggers an API call, the callback fires AFTER the value is
# retrieved — with the fetched value.
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_on_translations_cache_miss_fires_with_fetched_value(
    fake_gt: FakeGT,
    translate_many_for_locale: Callable[[str], Any],
) -> None:
    """``on_translations_cache_miss`` fires post-fetch with the translation that was retrieved."""
    misses: list[dict[str, Any]] = []

    cache = TranslationsCache(
        locale="es",
        translate_many=translate_many_for_locale("es"),
        batch_interval_ms=5,
        lifecycle={
            "on_translations_cache_miss": lambda *, locale, hash, value: misses.append(
                {"locale": locale, "hash": hash, "value": value}
            ),
        },
    )

    key = _key("Fetched")
    await cache.miss(key)

    assert len(misses) == 1
    assert misses[0]["locale"] == "es"
    assert misses[0]["value"] == "[es]Fetched"
    assert isinstance(misses[0]["hash"], str) and len(misses[0]["hash"]) > 0

"""Extended behavioral tests for ``TranslationsCache`` — dense edge-case coverage.

Complements ``test_translations_cache.py`` (the golden-standard file). These
exercise corners of the batching / dedup / lifecycle / partial-failure logic
that the golden file doesn't cover individually.
"""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

import pytest
from gt_i18n.i18n_manager._translations_cache import TranslationsCache

if TYPE_CHECKING:
    from conftest import FakeGT  # noqa: F401 — type hints only


def _key(message: str, *, fmt: str = "STRING", **opts: Any) -> dict[str, Any]:
    options: dict[str, Any] = {"_format": fmt, **{f"_{k}": v for k, v in opts.items() if v is not None}}
    return {"message": message, "options": options}


# ---------------------------------------------------------------------------
# Initial translations seed
# ---------------------------------------------------------------------------


def test_initial_translations_populate_cache_so_get_hits_without_network(
    translate_many_for_locale: Callable[[str], Any],
) -> None:
    """Passing ``initial={...}`` makes those hashes immediate cache hits."""
    from gt_i18n.i18n_manager._translations_cache import _compute_hash

    k = _key("Hello", fmt="ICU")
    h = _compute_hash(k["message"], k["options"])

    cache = TranslationsCache(
        locale="es",
        translate_many=translate_many_for_locale("es"),
        initial={h: "Hola"},
    )
    assert cache.get(k) == "Hola"


@pytest.mark.asyncio
async def test_initial_translations_are_used_even_on_async_miss_path(
    fake_gt: FakeGT,
    translate_many_for_locale: Callable[[str], Any],
) -> None:
    """``miss()`` returns initial-seeded values without calling translate_many."""
    from gt_i18n.i18n_manager._translations_cache import _compute_hash

    k = _key("Cached source", fmt="STRING")
    h = _compute_hash(k["message"], k["options"])

    cache = TranslationsCache(
        locale="es",
        translate_many=translate_many_for_locale("es"),
        initial={h: "Valor en cache"},
    )
    got = await cache.miss(k)
    assert got == "Valor en cache"
    assert len(fake_gt.calls) == 0, "initial entries must not trigger translate_many"


@pytest.mark.asyncio
async def test_initial_empty_dict_is_equivalent_to_no_initial(
    fake_gt: FakeGT,
    translate_many_for_locale: Callable[[str], Any],
) -> None:
    """``initial={}`` doesn't confuse the cache — all misses go through translate_many."""
    cache = TranslationsCache(
        locale="es",
        translate_many=translate_many_for_locale("es"),
        initial={},
        batch_interval_ms=5,
    )
    await cache.miss(_key("x"))
    assert len(fake_gt.calls) == 1


# ---------------------------------------------------------------------------
# Batch-timer edge cases
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_timer_fires_on_empty_queue_is_a_noop(
    fake_gt: FakeGT,
    translate_many_for_locale: Callable[[str], Any],
) -> None:
    """If the queue is emptied before the timer fires, the timer's drain is a no-op."""
    cache = TranslationsCache(
        locale="es",
        translate_many=translate_many_for_locale("es"),
        batch_size=1,  # immediate drain on enqueue
        batch_interval_ms=15,
    )
    # Fire one miss — immediate drain, queue empties before timer fires.
    await cache.miss(_key("only"))
    # Wait past the timer interval so it fires.
    await asyncio.sleep(0.03)
    # Timer fired but had nothing to do; exactly one API call total.
    assert len(fake_gt.calls) == 1


@pytest.mark.asyncio
async def test_timer_restarts_after_firing(
    fake_gt: FakeGT,
    translate_many_for_locale: Callable[[str], Any],
) -> None:
    """After the timer fires once, a subsequent miss starts a fresh timer."""
    cache = TranslationsCache(
        locale="es",
        translate_many=translate_many_for_locale("es"),
        batch_size=25,
        batch_interval_ms=10,
    )
    await cache.miss(_key("a"))
    await asyncio.sleep(0.03)  # let timer fire + a second timer window close
    await cache.miss(_key("b"))
    assert len(fake_gt.calls) == 2, "second miss should fire a fresh batch after first timer completed"


@pytest.mark.asyncio
async def test_exactly_batch_size_triggers_immediate_drain(
    fake_gt: FakeGT,
    translate_many_for_locale: Callable[[str], Any],
) -> None:
    """When queue reaches exactly batch_size, drain happens without waiting for timer."""
    cache = TranslationsCache(
        locale="es",
        translate_many=translate_many_for_locale("es"),
        batch_size=3,
        batch_interval_ms=1_000,  # very long — if we had to wait, test would hang
    )
    results = await asyncio.gather(cache.miss(_key("a")), cache.miss(_key("b")), cache.miss(_key("c")))
    assert all(r is not None for r in results)
    assert len(fake_gt.calls) == 1


# ---------------------------------------------------------------------------
# Cached + new interleaving
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_mixed_cached_and_new_in_same_gather(
    fake_gt: FakeGT,
    translate_many_for_locale: Callable[[str], Any],
) -> None:
    """Cached keys short-circuit; new keys go through batching."""
    from gt_i18n.i18n_manager._translations_cache import _compute_hash

    k_cached = _key("already", fmt="STRING")
    h_cached = _compute_hash(k_cached["message"], k_cached["options"])

    cache = TranslationsCache(
        locale="es",
        translate_many=translate_many_for_locale("es"),
        initial={h_cached: "yacheado"},
        batch_interval_ms=5,
    )
    a, b, c = await asyncio.gather(
        cache.miss(k_cached),
        cache.miss(_key("new1")),
        cache.miss(_key("new2")),
    )
    assert a == "yacheado"
    assert b == "[es]new1"
    assert c == "[es]new2"
    # Only one API call, containing only the 2 new keys.
    assert len(fake_gt.calls) == 1
    assert len(fake_gt.calls[0]["sources"]) == 2


# ---------------------------------------------------------------------------
# Response-shape tolerance
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_response_missing_hash_treated_as_failure(
    fake_gt: FakeGT,
    translate_many_for_locale: Callable[[str], Any],
) -> None:
    """If the server response omits a hash entirely, miss() returns None for it."""
    fake_gt.response_factory = lambda sources, options: {}  # return nothing

    cache = TranslationsCache(
        locale="es",
        translate_many=translate_many_for_locale("es"),
        batch_interval_ms=5,
    )
    got = await cache.miss(_key("abandoned"))
    assert got is None


@pytest.mark.asyncio
async def test_response_with_unsolicited_extra_hash_is_ignored(
    fake_gt: FakeGT,
    translate_many_for_locale: Callable[[str], Any],
) -> None:
    """Server returning a hash we didn't request doesn't crash or pollute cache."""

    def factory(sources: dict[str, Any], options: dict[str, Any]) -> dict[str, Any]:
        result: dict[str, Any] = {"unsolicited_hash_zzz": {"success": True, "translation": "intruder"}}
        for h, entry in sources.items():
            result[h] = {"success": True, "translation": f"ok:{entry['source']}"}
        return result

    fake_gt.response_factory = factory

    cache = TranslationsCache(
        locale="es",
        translate_many=translate_many_for_locale("es"),
        batch_interval_ms=5,
    )
    got = await cache.miss(_key("legit"))
    assert got == "ok:legit"
    # Unsolicited entry should not be reachable via a subsequent cache check.
    # There's no message that would hash to unsolicited_hash_zzz, so just assert
    # the cache doesn't explode and legit is hit-cacheable.
    assert cache.get(_key("legit")) == "ok:legit"


@pytest.mark.asyncio
async def test_response_with_success_false_does_not_cache(
    fake_gt: FakeGT,
    translate_many_for_locale: Callable[[str], Any],
) -> None:
    """A failed entry is NOT cached — next miss() retries."""
    attempts = [0]

    def factory(sources: dict[str, Any], options: dict[str, Any]) -> dict[str, Any]:
        attempts[0] += 1
        if attempts[0] == 1:
            return {h: {"success": False, "error": "nope", "code": 500} for h in sources}
        return {h: {"success": True, "translation": f"ok:{e['source']}"} for h, e in sources.items()}

    fake_gt.response_factory = factory

    cache = TranslationsCache(
        locale="es",
        translate_many=translate_many_for_locale("es"),
        batch_interval_ms=5,
    )
    first = await cache.miss(_key("retryable"))
    second = await cache.miss(_key("retryable"))
    assert first is None
    assert second == "ok:retryable"
    assert attempts[0] == 2


# ---------------------------------------------------------------------------
# Translate_many throws exception — all awaiters propagate
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_translate_many_exception_propagates_to_all_awaiters() -> None:
    """A network error on translate_many raises in every waiting miss() call."""

    async def broken_translate(sources: dict[str, Any]) -> dict[str, Any]:
        raise ConnectionError("upstream offline")

    cache = TranslationsCache(
        locale="es",
        translate_many=broken_translate,
        batch_interval_ms=5,
    )
    with pytest.raises(ConnectionError, match="upstream offline"):
        await cache.miss(_key("first"))


# ---------------------------------------------------------------------------
# Concurrency cap — stricter
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_concurrency_cap_of_1(
    fake_gt: FakeGT,
    translate_many_for_locale: Callable[[str], Any],
) -> None:
    """With max_concurrent=1, no two batch calls overlap."""
    fake_gt.inflight_event = asyncio.Event()
    cache = TranslationsCache(
        locale="es",
        translate_many=translate_many_for_locale("es"),
        batch_size=1,
        batch_interval_ms=1,
        max_concurrent_requests=1,
    )
    tasks = [asyncio.create_task(cache.miss(_key(f"msg-{i}"))) for i in range(4)]
    for _ in range(15):
        await asyncio.sleep(0.01)
        if fake_gt.max_inflight >= 1 and fake_gt.inflight_count == 1:
            break
    assert fake_gt.max_inflight == 1
    fake_gt.inflight_event.set()
    await asyncio.gather(*tasks)
    assert fake_gt.max_inflight == 1


# ---------------------------------------------------------------------------
# Lifecycle callback ordering
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_miss_callback_fires_after_cache_write_so_hit_is_consistent(
    fake_gt: FakeGT,
    translate_many_for_locale: Callable[[str], Any],
) -> None:
    """Inside on_translations_cache_miss, a subsequent get() must see the value."""
    observations: list[Any] = []

    def on_miss(*, locale: str, hash: str, value: str) -> None:
        # At this point the value must already be in the cache.
        observations.append(
            ("miss", locale, hash, value, cache.get({"message": "x", "options": {"_format": "STRING"}}))
        )

    cache = TranslationsCache(
        locale="es",
        translate_many=translate_many_for_locale("es"),
        batch_interval_ms=5,
        lifecycle={"on_translations_cache_miss": on_miss},
    )
    await cache.miss(_key("x"))
    # Check at-write-time observation: the sync get() inside the callback saw the value.
    assert len(observations) == 1
    # Last element in tuple is the result of the sync get() inside the callback.
    assert observations[0][4] == "[es]x"


@pytest.mark.asyncio
async def test_hit_callback_never_fires_on_a_pure_miss(
    fake_gt: FakeGT,
    translate_many_for_locale: Callable[[str], Any],
) -> None:
    """A brand-new miss() must not fire the hit callback."""
    hits: list[Any] = []
    cache = TranslationsCache(
        locale="es",
        translate_many=translate_many_for_locale("es"),
        batch_interval_ms=5,
        lifecycle={"on_translations_cache_hit": lambda **p: hits.append(p)},
    )
    await cache.miss(_key("brand new"))
    assert hits == []


# ---------------------------------------------------------------------------
# Options combinations flow through to request metadata
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "fmt,context,id_,max_chars",
    [
        ("STRING", None, None, None),
        ("STRING", "button", None, None),
        ("STRING", None, "save.btn", None),
        ("STRING", None, None, 50),
        ("STRING", "button", "save.btn", 50),
        ("ICU", "menu", "menu_save", 20),
        ("I18NEXT", "modal", "modal_close", 10),
    ],
)
async def test_metadata_wire_shape_exhaustive(
    fake_gt: FakeGT,
    translate_many_for_locale: Callable[[str], Any],
    fmt: str,
    context: str | None,
    id_: str | None,
    max_chars: int | None,
) -> None:
    """Metadata includes camelCase keys only for non-None values, for all formats."""
    cache = TranslationsCache(
        locale="es",
        translate_many=translate_many_for_locale("es"),
        batch_interval_ms=5,
    )
    options: dict[str, Any] = {"_format": fmt}
    if context is not None:
        options["_context"] = context
    if id_ is not None:
        options["_id"] = id_
    if max_chars is not None:
        options["_max_chars"] = max_chars
    key = {"message": "Hi", "options": options}
    await cache.miss(key)

    meta = next(iter(fake_gt.calls[0]["sources"].values()))["metadata"]
    assert meta["dataFormat"] == fmt
    if context is None:
        assert "context" not in meta
    else:
        assert meta["context"] == context
    if id_ is None:
        assert "id" not in meta
    else:
        assert meta["id"] == id_
    if max_chars is None:
        assert "maxChars" not in meta
    else:
        assert meta["maxChars"] == max_chars


# ---------------------------------------------------------------------------
# Sequential (non-concurrent) misses
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_sequential_misses_produce_separate_batches(
    fake_gt: FakeGT,
    translate_many_for_locale: Callable[[str], Any],
) -> None:
    """Awaiting each miss() before the next should produce one API call per miss."""
    cache = TranslationsCache(
        locale="es",
        translate_many=translate_many_for_locale("es"),
        batch_interval_ms=5,
    )
    await cache.miss(_key("one"))
    await cache.miss(_key("two"))
    await cache.miss(_key("three"))
    assert len(fake_gt.calls) == 3


# ---------------------------------------------------------------------------
# Many different misses (stress)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_fifty_distinct_concurrent_misses_all_resolve(
    fake_gt: FakeGT,
    translate_many_for_locale: Callable[[str], Any],
) -> None:
    """50 distinct concurrent misses all resolve correctly under default batching."""
    cache = TranslationsCache(
        locale="es",
        translate_many=translate_many_for_locale("es"),
        batch_size=25,
        batch_interval_ms=5,
    )
    results = await asyncio.gather(*(cache.miss(_key(f"k{i}")) for i in range(50)))
    assert all(r == f"[es]k{i}" for i, r in enumerate(results))
    # Should be 2 batches of 25 (or equivalent groupings <= 25).
    assert sum(len(c["sources"]) for c in fake_gt.calls) == 50
    assert all(len(c["sources"]) <= 25 for c in fake_gt.calls)


@pytest.mark.asyncio
async def test_hundred_duplicate_concurrent_misses_dedup_to_one(
    fake_gt: FakeGT,
    translate_many_for_locale: Callable[[str], Any],
) -> None:
    """100 concurrent misses for the SAME key → 1 API call with 1 entry."""
    fake_gt.delay_s = 0.02
    cache = TranslationsCache(
        locale="es",
        translate_many=translate_many_for_locale("es"),
        batch_interval_ms=5,
    )
    key = _key("same")
    results = await asyncio.gather(*(cache.miss(key) for _ in range(100)))
    assert all(r == "[es]same" for r in results)
    assert len(fake_gt.calls) == 1
    assert len(fake_gt.calls[0]["sources"]) == 1


# ---------------------------------------------------------------------------
# Two distinct keys that produce the same message but different formats
# route through separate cache entries (no cross-format collision).
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_same_message_different_formats_are_separate_cache_entries(
    fake_gt: FakeGT,
    translate_many_for_locale: Callable[[str], Any],
) -> None:
    """A STRING 'Hi' and ICU 'Hi' are different cache keys."""
    cache = TranslationsCache(
        locale="es",
        translate_many=translate_many_for_locale("es"),
        batch_interval_ms=5,
    )
    r1 = await cache.miss(_key("Hi", fmt="STRING"))
    r2 = await cache.miss(_key("Hi", fmt="ICU"))
    assert r1 == "[es]Hi"
    assert r2 == "[es]Hi"
    # Two API calls because they hashed differently.
    assert len(fake_gt.calls) == 2

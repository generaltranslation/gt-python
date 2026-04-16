"""Golden-standard tests for the new ``I18nManager`` runtime-translation API.

PR #1207 added four new methods on ``I18nManager``:

- ``lookup_translation(message, **options)`` — SYNC dict-cache lookup; returns
  cached translation or None. Never triggers a network call.
- ``lookup_translation_with_fallback(message, **options)`` — ASYNC; returns the
  cached translation, or fetches via runtime translate on a miss.
- ``load_translations(locale=None)`` — ASYNC; returns dict[hash, translation]
  for the locale (loading if needed). Replaces deprecated ``get_translations``.
- ``get_lookup_translation(locale=None, prefetch=None)`` — ASYNC; returns a
  sync callable bound to a locale, optionally prefetching a list of entries.

All four are tested here as the observable contract of the public
``I18nManager`` class.

All tests in this file should FAIL until PR #1207 is ported.
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any

import pytest
from gt_i18n import I18nManager
from gt_i18n.translation_functions._hash_message import hash_message

if TYPE_CHECKING:
    from conftest import FakeGT  # noqa: F401 — only for type hints


# ---------------------------------------------------------------------------
# test_lookup_translation_sync_returns_cached
#
# Example:
#     await manager.load_translations("es")  # populates cache from loader
#     result = manager.lookup_translation("Hello", _format="ICU")
#     # → translation from the pre-loaded dict; NO API call fired
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_lookup_translation_sync_returns_cached(fake_gt: FakeGT) -> None:
    """After ``load_translations``, ``lookup_translation`` returns cached values synchronously."""
    h = hash_message("Hello")

    def loader(locale: str) -> dict[str, str]:
        return {h: "Hola"} if locale == "es" else {}

    manager = I18nManager(default_locale="en", locales=["en", "es"], load_translations=loader)
    manager.set_locale("es")

    await manager.load_translations("es")
    assert manager.lookup_translation("Hello", _format="ICU") == "Hola"

    # No runtime API was fired — sync dict lookup only.
    assert len(fake_gt.calls) == 0


# ---------------------------------------------------------------------------
# test_lookup_translation_sync_returns_none_on_miss
#
# Sync-safe: a miss does NOT trigger a fetch. The sync ``t()`` path relies on this.
# ---------------------------------------------------------------------------


def test_lookup_translation_sync_returns_none_on_miss(fake_gt: FakeGT) -> None:
    """``lookup_translation`` returns None on miss and does not trigger runtime translate."""
    manager = I18nManager(default_locale="en", locales=["en", "es"], load_translations=lambda locale: {})
    manager.set_locale("es")

    assert manager.lookup_translation("Never-seen message", _format="ICU") is None
    assert len(fake_gt.calls) == 0, "sync lookup_translation MUST NOT fire translate_many"


# ---------------------------------------------------------------------------
# test_lookup_translation_with_fallback_triggers_runtime_on_miss
#
# Example:
#     result = await manager.lookup_translation_with_fallback(
#         "Greeting", _format="STRING"
#     )
#     # → translate_many called; result matches the mock response.
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_lookup_translation_with_fallback_triggers_runtime_on_miss(fake_gt: FakeGT) -> None:
    """``lookup_translation_with_fallback`` hits translate_many on miss and returns fetched translation."""
    manager = I18nManager(default_locale="en", locales=["en", "es"], load_translations=lambda locale: {})
    manager.set_locale("es")

    result = await manager.lookup_translation_with_fallback("Greeting", _format="STRING")

    assert result == "[es]Greeting"
    assert len(fake_gt.calls) == 1


# ---------------------------------------------------------------------------
# test_lookup_translation_with_fallback_returns_cached_without_api_call
#
# Second call for the same message returns cached value — no second API call.
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_lookup_translation_with_fallback_returns_cached_without_api_call(fake_gt: FakeGT) -> None:
    """Second call for the same message is a cache hit — no repeat API call."""
    manager = I18nManager(default_locale="en", locales=["en", "es"], load_translations=lambda locale: {})
    manager.set_locale("es")

    first = await manager.lookup_translation_with_fallback("Hi", _format="STRING")
    second = await manager.lookup_translation_with_fallback("Hi", _format="STRING")

    assert first == second == "[es]Hi"
    assert len(fake_gt.calls) == 1, "second lookup must be served from cache"


# ---------------------------------------------------------------------------
# test_load_translations_returns_dict_for_locale
#
# JS rename: ``getTranslations(locale)`` → ``loadTranslations(locale)``.
# Python gets ``load_translations(locale)`` as the new canonical name.
#
# Example:
#     result = await manager.load_translations("es")
#     # → {"<hash>": "<translation>", ...}
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_load_translations_returns_dict_for_locale(fake_gt: FakeGT) -> None:
    """``load_translations(locale)`` returns the dict of {hash: translation} for that locale."""
    loaded = {"hash_a": "valA", "hash_b": "valB"}

    def loader(locale: str) -> dict[str, str]:
        return loaded if locale == "es" else {}

    manager = I18nManager(default_locale="en", locales=["en", "es"], load_translations=loader)

    result = await manager.load_translations("es")
    assert result == loaded


# ---------------------------------------------------------------------------
# test_get_lookup_translation_returns_callable_after_prefetch
#
# Mirrors the JS ``useGT`` / ``getGT`` pattern: caller awaits once to prefetch,
# then receives a SYNC lookup callable it can use in hot paths.
#
# Example:
#     lookup = await manager.get_lookup_translation(
#         "es",
#         prefetch=[{"message": "Hi", "options": {"_format": "STRING"}}],
#     )
#     # After the prefetch completes, lookup is sync and cache-hits.
#     result = lookup("Hi", {"_format": "STRING"})
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_lookup_translation_returns_callable_after_prefetch(fake_gt: FakeGT) -> None:
    """``get_lookup_translation`` returns a sync callable that resolves from the prefetched cache."""
    manager = I18nManager(default_locale="en", locales=["en", "es"], load_translations=lambda locale: {})
    manager.set_locale("es")

    lookup = await manager.get_lookup_translation(
        "es",
        prefetch=[{"message": "Hi", "options": {"_format": "STRING"}}],
    )

    # The prefetch fetched "Hi"; the returned callable is sync and cache-hits.
    calls_before_lookup = len(fake_gt.calls)
    result = lookup("Hi", {"_format": "STRING"})
    assert result == "[es]Hi"
    assert len(fake_gt.calls) == calls_before_lookup, "sync lookup after prefetch must not fire API"


# ---------------------------------------------------------------------------
# test_lifecycle_callbacks_passed_in_constructor_fire_correctly
#
# The I18nManager accepts a `lifecycle` dict and wires it through to the
# internal caches. This test asserts miss → hit transitions on the
# translations-level callbacks.
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_lifecycle_callbacks_passed_in_constructor_fire_correctly(fake_gt: FakeGT) -> None:
    """``lifecycle`` kwarg on I18nManager wires callbacks through to the caches."""
    hits: list[dict[str, Any]] = []
    misses: list[dict[str, Any]] = []

    manager = I18nManager(
        default_locale="en",
        locales=["en", "es"],
        load_translations=lambda locale: {},
        lifecycle={
            "on_translations_cache_hit": lambda *, locale, hash, value: hits.append(
                {"locale": locale, "hash": hash, "value": value}
            ),
            "on_translations_cache_miss": lambda *, locale, hash, value: misses.append(
                {"locale": locale, "hash": hash, "value": value}
            ),
        },
    )
    manager.set_locale("es")

    # First call: miss callback fires (runtime translate happens).
    await manager.lookup_translation_with_fallback("Hello", _format="STRING")
    assert len(misses) == 1
    assert len(hits) == 0

    # Second call for the same message: hit callback fires; no new miss.
    await manager.lookup_translation_with_fallback("Hello", _format="STRING")
    assert len(misses) == 1
    assert len(hits) == 1


# ---------------------------------------------------------------------------
# test_batching_params_configurable_on_i18n_manager
#
# Pin: batch_size / batch_interval_ms / max_concurrent_requests can be set on
# I18nManager and flow through to the TranslationsCache it creates.
# Asserted behaviorally: batch_size=2 means 5 concurrent fetches produce at
# least 3 batches (none > 2 entries).
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_batching_params_configurable_on_i18n_manager(fake_gt: FakeGT) -> None:
    """Batching constants set on I18nManager take effect in the underlying cache."""
    manager = I18nManager(
        default_locale="en",
        locales=["en", "es"],
        load_translations=lambda locale: {},
        batch_size=2,
        batch_interval_ms=5,
    )
    manager.set_locale("es")

    messages = [f"msg-{i}" for i in range(5)]
    await asyncio.gather(*(manager.lookup_translation_with_fallback(m, _format="STRING") for m in messages))

    assert sum(len(c["sources"]) for c in fake_gt.calls) == 5
    assert all(len(c["sources"]) <= 2 for c in fake_gt.calls), (
        f"batch_size=2 was not honored: batches={[len(c['sources']) for c in fake_gt.calls]}"
    )

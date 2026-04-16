"""Extended integration tests for ``I18nManager``.

Dense coverage for locale switching, preloading, deprecation parity across
many inputs, and source-locale short-circuit semantics.
"""

from __future__ import annotations

import asyncio
import warnings
from typing import TYPE_CHECKING, Any

import pytest
from gt_i18n import I18nManager

if TYPE_CHECKING:
    from conftest import FakeGT  # noqa: F401


# ---------------------------------------------------------------------------
# Locale switching
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_locale_switch_midflight_routes_to_correct_locale(fake_gt: FakeGT) -> None:
    """Switching manager's locale between calls sends each to the correct target."""
    manager = I18nManager(default_locale="en", locales=["en", "es", "fr", "de"], load_translations=lambda loc: {})

    manager.set_locale("es")
    await manager.lookup_translation_with_fallback("Hello", _format="STRING")
    manager.set_locale("fr")
    await manager.lookup_translation_with_fallback("Hello", _format="STRING")
    manager.set_locale("de")
    await manager.lookup_translation_with_fallback("Hello", _format="STRING")

    targets = [c["options"].get("target_locale") or c["options"].get("targetLocale") for c in fake_gt.calls]
    assert set(targets) == {"es", "fr", "de"}


@pytest.mark.asyncio
async def test_per_call_locale_override_does_not_change_manager_state(fake_gt: FakeGT) -> None:
    """``_locale=...`` on a single call does NOT mutate manager.get_locale()."""
    manager = I18nManager(default_locale="en", locales=["en", "es", "fr"], load_translations=lambda loc: {})
    manager.set_locale("es")
    await manager.lookup_translation_with_fallback("Hi", _format="STRING", _locale="fr")
    assert manager.get_locale() == "es"  # unchanged


# ---------------------------------------------------------------------------
# Preload + sync lookup path
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_load_all_preloads_every_configured_locale(fake_gt: FakeGT) -> None:
    """``load_all_translations`` calls the loader once per locale."""
    loaded: list[str] = []

    def loader(locale: str) -> dict[str, str]:
        loaded.append(locale)
        return {}

    manager = I18nManager(default_locale="en", locales=["en", "es", "fr", "ja"], load_translations=loader)
    await manager.load_all_translations()
    assert set(loaded) == {"en", "es", "fr", "ja"}


@pytest.mark.asyncio
async def test_sync_lookup_after_preload_hits_cache_every_time(fake_gt: FakeGT) -> None:
    """Preloaded translations are available to sync ``lookup_translation``."""
    from gt_i18n.translation_functions._hash_message import hash_message

    h = hash_message("Hello, {name}!", format="ICU")

    def loader(locale: str) -> dict[str, str]:
        return {h: "Hola, {name}!"} if locale == "es" else {}

    manager = I18nManager(default_locale="en", locales=["en", "es"], load_translations=loader)
    await manager.load_translations("es")
    manager.set_locale("es")

    for _ in range(10):
        assert manager.lookup_translation("Hello, {name}!", _format="ICU") == "Hola, {name}!"
    assert len(fake_gt.calls) == 0


# ---------------------------------------------------------------------------
# Source-locale short circuits
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_lookup_with_fallback_at_source_locale_returns_none_and_no_api(fake_gt: FakeGT) -> None:
    """For the source locale, lookup_translation_with_fallback returns None and skips API."""
    manager = I18nManager(default_locale="en", locales=["en", "es"], load_translations=lambda loc: {})
    manager.set_locale("en")
    result = await manager.lookup_translation_with_fallback("Hello", _format="STRING")
    assert result is None
    assert len(fake_gt.calls) == 0


def test_sync_lookup_at_source_locale_returns_none_without_touching_cache(fake_gt: FakeGT) -> None:
    """Source-locale sync lookup returns None early, never reads the cache."""
    manager = I18nManager(default_locale="en", locales=["en", "es"], load_translations=lambda loc: {})
    manager.set_locale("en")
    assert manager.lookup_translation("Hello", _format="STRING") is None


# ---------------------------------------------------------------------------
# load_translations behavior
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_load_translations_twice_uses_cache(fake_gt: FakeGT) -> None:
    """Second call to load_translations for the same locale doesn't re-invoke the loader."""
    calls = [0]

    def loader(locale: str) -> dict[str, str]:
        calls[0] += 1
        return {"h": "v"}

    manager = I18nManager(default_locale="en", locales=["en", "es"], load_translations=loader)
    a = await manager.load_translations("es")
    b = await manager.load_translations("es")
    assert a == b == {"h": "v"}
    assert calls[0] == 1


@pytest.mark.asyncio
async def test_load_translations_uses_current_locale_when_none_given(fake_gt: FakeGT) -> None:
    """Calling load_translations() with no arg uses the manager's current locale."""
    loaded: list[str] = []

    def loader(locale: str) -> dict[str, str]:
        loaded.append(locale)
        return {}

    manager = I18nManager(default_locale="en", locales=["en", "fr"], load_translations=loader)
    manager.set_locale("fr")
    await manager.load_translations()
    assert loaded == ["fr"]


# ---------------------------------------------------------------------------
# get_lookup_translation semantics
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_lookup_translation_without_prefetch_still_returns_callable(
    fake_gt: FakeGT,
) -> None:
    """``get_lookup_translation`` with no prefetch still returns a working sync callable."""
    manager = I18nManager(default_locale="en", locales=["en", "es"], load_translations=lambda loc: {})
    lookup = await manager.get_lookup_translation("es")
    # Nothing prefetched → cache cold → lookup misses.
    result = lookup("Hello", {"_format": "STRING"})
    assert result is None


@pytest.mark.asyncio
async def test_get_lookup_translation_with_multi_prefetch_warms_all(fake_gt: FakeGT) -> None:
    """Every entry in ``prefetch`` becomes a cache hit on the returned callable."""
    manager = I18nManager(
        default_locale="en", locales=["en", "es"], load_translations=lambda loc: {}, batch_interval_ms=5
    )
    manager.set_locale("es")
    prefetch = [
        {"message": "one", "options": {"_format": "STRING"}},
        {"message": "two", "options": {"_format": "STRING"}},
        {"message": "three", "options": {"_format": "STRING"}},
    ]
    lookup = await manager.get_lookup_translation("es", prefetch=prefetch)
    assert lookup("one", {"_format": "STRING"}) == "[es]one"
    assert lookup("two", {"_format": "STRING"}) == "[es]two"
    assert lookup("three", {"_format": "STRING"}) == "[es]three"


@pytest.mark.asyncio
async def test_get_lookup_translation_with_empty_prefetch_list(fake_gt: FakeGT) -> None:
    """``prefetch=[]`` is valid and equivalent to no prefetch."""
    manager = I18nManager(default_locale="en", locales=["en", "es"], load_translations=lambda loc: {})
    lookup = await manager.get_lookup_translation("es", prefetch=[])
    assert lookup("x", {"_format": "STRING"}) is None


# ---------------------------------------------------------------------------
# Deprecation parity (matrix)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "message,options",
    [
        ("Hello", {"_format": "ICU"}),
        ("Save", {"_format": "ICU", "_context": "button"}),
        ("Long message with {vars}", {"_format": "ICU"}),
        ("Plain STRING", {"_format": "STRING"}),
        ("{{i18next}}", {"_format": "I18NEXT"}),
    ],
)
async def test_resolve_translation_sync_parity_with_lookup_translation(
    fake_gt: FakeGT, message: str, options: dict[str, Any]
) -> None:
    """Deprecated ``resolve_translation_sync`` must return identical results to ``lookup_translation``."""
    manager = I18nManager(default_locale="en", locales=["en", "es"], load_translations=lambda loc: {})
    manager.set_locale("es")

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        a = manager.resolve_translation_sync(message, options)
    b = manager.lookup_translation(message, **options)
    assert a == b


@pytest.mark.asyncio
async def test_get_translations_parity_with_load_translations_for_multi_locale(fake_gt: FakeGT) -> None:
    """Deprecated ``get_translations`` returns the same dict as ``load_translations`` for each locale."""
    data = {"es": {"h1": "es1"}, "fr": {"h2": "fr2"}, "de": {"h3": "de3"}}

    def loader(locale: str) -> dict[str, str]:
        return data.get(locale, {})

    manager = I18nManager(default_locale="en", locales=["en", *data.keys()], load_translations=loader)

    for loc in data:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            old = await manager.get_translations(loc)
        new = await manager.load_translations(loc)
        assert old == new == data[loc]


def test_get_translation_loader_returns_same_callable_as_constructed() -> None:
    """``get_translation_loader`` returns the loader that was passed in."""

    def my_loader(locale: str) -> dict[str, str]:
        return {}

    manager = I18nManager(default_locale="en", locales=["en", "es"], load_translations=my_loader)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        got = manager.get_translation_loader()
    assert got is my_loader


# ---------------------------------------------------------------------------
# Deprecation warning contents
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_translations_warning_message_mentions_load_translations() -> None:
    manager = I18nManager(default_locale="en", locales=["en", "es"], load_translations=lambda loc: {})
    with pytest.warns(DeprecationWarning, match="load_translations") as record:
        await manager.get_translations("es")
    assert len(record) >= 1


@pytest.mark.asyncio
async def test_get_translation_resolver_warning_mentions_get_lookup_translation() -> None:
    manager = I18nManager(default_locale="en", locales=["en", "es"], load_translations=lambda loc: {})
    with pytest.warns(DeprecationWarning, match="get_lookup_translation"):
        await manager.get_translation_resolver("es")


def test_resolve_translation_sync_warning_mentions_lookup_translation() -> None:
    manager = I18nManager(default_locale="en", locales=["en", "es"], load_translations=lambda loc: {})
    manager.set_locale("es")
    with pytest.warns(DeprecationWarning, match="lookup_translation"):
        manager.resolve_translation_sync("Hi", {"_format": "ICU"})


def test_get_translation_loader_warning_mentions_load_translations() -> None:
    manager = I18nManager(default_locale="en", locales=["en", "es"], load_translations=lambda loc: {})
    with pytest.warns(DeprecationWarning, match="load_translations"):
        manager.get_translation_loader()


# ---------------------------------------------------------------------------
# Batching param defaults + overrides
# ---------------------------------------------------------------------------


def test_default_batching_params_match_js_defaults() -> None:
    """Default batch_size/interval/concurrency values match JS constants."""
    manager = I18nManager(default_locale="en", locales=["en", "es"], load_translations=lambda loc: {})
    tc = asyncio.run(manager._locales_cache.miss("es"))
    assert tc._batch_size == 25
    assert tc._batch_interval_ms == 50
    assert tc._max_concurrent_requests == 100


@pytest.mark.asyncio
async def test_batching_kwargs_flow_through_to_translations_cache(fake_gt: FakeGT) -> None:
    """Custom batching constants reach the TranslationsCache instances."""
    manager = I18nManager(
        default_locale="en",
        locales=["en", "es"],
        load_translations=lambda loc: {},
        batch_size=7,
        batch_interval_ms=13,
        max_concurrent_requests=3,
    )
    tc = await manager._locales_cache.miss("es")
    assert tc._batch_size == 7
    assert tc._batch_interval_ms == 13
    assert tc._max_concurrent_requests == 3


# ---------------------------------------------------------------------------
# Lifecycle callback fanout
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_lifecycle_is_shared_between_locales(fake_gt: FakeGT) -> None:
    """The same lifecycle dict fires callbacks for every locale served."""
    misses: list[str] = []

    manager = I18nManager(
        default_locale="en",
        locales=["en", "es", "fr"],
        load_translations=lambda loc: {},
        lifecycle={
            "on_translations_cache_miss": lambda *, locale, hash, value: misses.append(locale),
        },
    )
    manager.set_locale("es")
    await manager.lookup_translation_with_fallback("A", _format="STRING")
    manager.set_locale("fr")
    await manager.lookup_translation_with_fallback("B", _format="STRING")
    assert misses == ["es", "fr"]


@pytest.mark.asyncio
async def test_lifecycle_locales_miss_fires_for_each_locale_load(fake_gt: FakeGT) -> None:
    """Each locale's initial load fires ``on_locales_cache_miss`` once."""
    observed: list[str] = []

    manager = I18nManager(
        default_locale="en",
        locales=["en", "es", "fr"],
        load_translations=lambda loc: {},
        lifecycle={"on_locales_cache_miss": lambda *, locale, value: observed.append(locale)},
    )
    await manager.load_translations("es")
    await manager.load_translations("fr")
    assert observed == ["es", "fr"]


# ---------------------------------------------------------------------------
# Translation timeout forwarding
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_translation_timeout_ms_reaches_translate_many(fake_gt: FakeGT) -> None:
    """``translation_timeout_ms`` kwarg is passed through to GT.translate_many calls."""
    manager = I18nManager(
        default_locale="en",
        locales=["en", "es"],
        load_translations=lambda loc: {},
        translation_timeout_ms=1234,
    )
    manager.set_locale("es")
    await manager.lookup_translation_with_fallback("Hi", _format="STRING")
    assert fake_gt.calls[0]["timeout"] == 1234

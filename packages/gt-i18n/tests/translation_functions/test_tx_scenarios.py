"""Extended scenarios for the public ``tx()`` async translator.

Covers option permutations, concurrency, format variations, unicode, caching,
and source-locale bypass at scale.
"""

from __future__ import annotations

import asyncio
from collections.abc import Generator
from typing import TYPE_CHECKING

import pytest
from gt_i18n import I18nManager, set_i18n_manager, tx

if TYPE_CHECKING:
    from conftest import FakeGT  # noqa: F401


@pytest.fixture
def _manager(fake_gt: FakeGT) -> Generator[I18nManager, None, None]:
    m = I18nManager(
        default_locale="en",
        locales=["en", "es", "fr", "de", "ja"],
        load_translations=lambda loc: {},
        batch_interval_ms=5,
    )
    set_i18n_manager(m)
    yield m


# ---------------------------------------------------------------------------
# Smoke variations
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_tx_returns_str(_manager: I18nManager) -> None:
    _manager.set_locale("es")
    result = await tx("Hello")
    assert isinstance(result, str)


@pytest.mark.asyncio
async def test_tx_with_empty_content(_manager: I18nManager) -> None:
    _manager.set_locale("es")
    result = await tx("")
    # Empty source + fake returning "[es]" → "[es]"
    assert result == "[es]"


@pytest.mark.asyncio
async def test_tx_with_very_long_content(_manager: I18nManager) -> None:
    _manager.set_locale("es")
    long_msg = "x" * 5000
    result = await tx(long_msg)
    assert result == f"[es]{long_msg}"


@pytest.mark.asyncio
async def test_tx_with_unicode_content(_manager: I18nManager) -> None:
    _manager.set_locale("es")
    result = await tx("こんにちは")
    assert result == "[es]こんにちは"


@pytest.mark.asyncio
async def test_tx_with_emoji_content(_manager: I18nManager) -> None:
    _manager.set_locale("es")
    result = await tx("🎉 party!")
    assert result == "[es]🎉 party!"


@pytest.mark.asyncio
async def test_tx_with_multiline_content(_manager: I18nManager) -> None:
    _manager.set_locale("es")
    result = await tx("line1\nline2\nline3")
    assert result == "[es]line1\nline2\nline3"


# ---------------------------------------------------------------------------
# Format overrides
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.parametrize("fmt", ["STRING", "ICU", "I18NEXT"])
async def test_tx_format_override_reaches_request_metadata(fake_gt: FakeGT, _manager: I18nManager, fmt: str) -> None:
    _manager.set_locale("es")
    await tx(f"content-{fmt}", _format=fmt)
    meta = next(iter(fake_gt.calls[0]["sources"].values()))["metadata"]
    assert meta["dataFormat"] == fmt


# ---------------------------------------------------------------------------
# Caching
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_tx_identical_calls_do_not_refire_api(fake_gt: FakeGT, _manager: I18nManager) -> None:
    """Second tx() for same content returns cached result — zero extra API calls."""
    _manager.set_locale("es")
    a = await tx("repeat")
    b = await tx("repeat")
    assert a == b == "[es]repeat"
    assert len(fake_gt.calls) == 1


@pytest.mark.asyncio
async def test_tx_different_contexts_produce_separate_cache_entries(fake_gt: FakeGT, _manager: I18nManager) -> None:
    """Same message with different _context hits the API twice (different cache keys)."""
    _manager.set_locale("es")
    await tx("Save", _context="button")
    await tx("Save", _context="menu")
    assert len(fake_gt.calls) == 2


@pytest.mark.asyncio
async def test_tx_different_ids_produce_separate_cache_entries(fake_gt: FakeGT, _manager: I18nManager) -> None:
    _manager.set_locale("es")
    await tx("Go", _id="btn1")
    await tx("Go", _id="btn2")
    assert len(fake_gt.calls) == 2


@pytest.mark.asyncio
async def test_tx_max_chars_variation_produces_separate_cache_entries(fake_gt: FakeGT, _manager: I18nManager) -> None:
    _manager.set_locale("es")
    await tx("Hi", _max_chars=10)
    await tx("Hi", _max_chars=20)
    assert len(fake_gt.calls) == 2


# ---------------------------------------------------------------------------
# Source-locale short circuit permutations
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.parametrize("fmt", ["STRING", "ICU", "I18NEXT"])
async def test_tx_source_locale_skips_api_for_any_format(fake_gt: FakeGT, _manager: I18nManager, fmt: str) -> None:
    _manager.set_locale("en")  # source
    result = await tx("Hello", _format=fmt)
    assert result == "Hello"
    assert len(fake_gt.calls) == 0


@pytest.mark.asyncio
async def test_tx_per_call_locale_override_routes_even_when_manager_is_source(
    fake_gt: FakeGT, _manager: I18nManager
) -> None:
    """Per-call _locale override: even if manager is at source, a different _locale hits API."""
    _manager.set_locale("en")
    await tx("Hello", _locale="fr")
    assert len(fake_gt.calls) == 1
    target = fake_gt.calls[0]["options"].get("target_locale") or fake_gt.calls[0]["options"].get("targetLocale")
    assert target == "fr"


# ---------------------------------------------------------------------------
# Concurrency + batching
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_tx_ten_concurrent_distinct_calls_batch_into_one_request(fake_gt: FakeGT, _manager: I18nManager) -> None:
    _manager.set_locale("es")
    results = await asyncio.gather(*(tx(f"msg-{i}") for i in range(10)))
    assert [r for r in results] == [f"[es]msg-{i}" for i in range(10)]
    assert len(fake_gt.calls) == 1
    assert len(fake_gt.calls[0]["sources"]) == 10


@pytest.mark.asyncio
async def test_tx_hundred_concurrent_duplicate_calls_dedup_to_one(fake_gt: FakeGT, _manager: I18nManager) -> None:
    fake_gt.delay_s = 0.02
    _manager.set_locale("es")
    results = await asyncio.gather(*(tx("same") for _ in range(100)))
    assert all(r == "[es]same" for r in results)
    assert len(fake_gt.calls) == 1


@pytest.mark.asyncio
async def test_tx_concurrent_different_locales_each_get_their_own_call(fake_gt: FakeGT, _manager: I18nManager) -> None:
    _manager.set_locale("es")
    results = await asyncio.gather(
        tx("Hi", _locale="es"),
        tx("Hi", _locale="fr"),
        tx("Hi", _locale="de"),
        tx("Hi", _locale="ja"),
    )
    # Each distinct locale gets its own TranslationsCache → one request per locale.
    assert results == ["[es]Hi", "[fr]Hi", "[de]Hi", "[ja]Hi"]
    assert len(fake_gt.calls) == 4


# ---------------------------------------------------------------------------
# Error paths
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_tx_returns_source_when_translation_explicitly_fails(fake_gt: FakeGT, _manager: I18nManager) -> None:
    fake_gt.response_factory = lambda sources, options: {
        h: {"success": False, "error": "upstream", "code": 500} for h in sources
    }
    _manager.set_locale("es")
    assert await tx("Fallback me") == "Fallback me"


# ---------------------------------------------------------------------------
# Options propagation exhaustive matrix
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "opts",
    [
        {"_context": "button"},
        {"_id": "save_btn"},
        {"_max_chars": 15},
        {"_context": "menu", "_id": "menu_save"},
        {"_context": "menu", "_max_chars": 30},
        {"_id": "menu_save", "_max_chars": 30},
        {"_context": "modal", "_id": "modal_close", "_max_chars": 10},
    ],
)
async def test_tx_options_reach_metadata(fake_gt: FakeGT, _manager: I18nManager, opts: dict[str, object]) -> None:
    _manager.set_locale("es")
    await tx("Save", **opts)
    meta = next(iter(fake_gt.calls[0]["sources"].values()))["metadata"]
    if "_context" in opts:
        assert meta["context"] == opts["_context"]
    if "_id" in opts:
        assert meta["id"] == opts["_id"]
    if "_max_chars" in opts:
        assert meta["maxChars"] == opts["_max_chars"]


# ---------------------------------------------------------------------------
# Cache hit path exercises hash computation including options
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_tx_repeated_call_same_options_cache_hit(fake_gt: FakeGT, _manager: I18nManager) -> None:
    _manager.set_locale("es")
    await tx("Save", _context="button", _id="save", _max_chars=20)
    calls_before = len(fake_gt.calls)
    result = await tx("Save", _context="button", _id="save", _max_chars=20)
    assert result == "[es]Save"
    assert len(fake_gt.calls) == calls_before


# ---------------------------------------------------------------------------
# Public export shape
# ---------------------------------------------------------------------------


def test_tx_is_importable_from_multiple_paths() -> None:
    """``tx`` is reachable from top-level and from the translation_functions module."""
    from gt_i18n import tx as a
    from gt_i18n.translation_functions import tx as b
    from gt_i18n.translation_functions._tx import tx as c

    assert a is b is c


def test_tx_coroutine_signature() -> None:
    import inspect

    sig = inspect.signature(tx)
    params = list(sig.parameters.keys())
    # tx(content, **kwargs)
    assert params[0] == "content"
    # kwargs via var keyword
    assert any(p.kind == inspect.Parameter.VAR_KEYWORD for p in sig.parameters.values())

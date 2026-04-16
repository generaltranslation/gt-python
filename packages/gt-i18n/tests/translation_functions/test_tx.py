"""Golden-standard tests for the new public ``tx()`` function.

``tx()`` is the Python mirror of the JS ``tx()`` added in gt PR #1207:
an async function that translates a string at runtime via
``GT.translate_many``, with batching, dedup, and source-fallback on error.

Contract:
- Default format is STRING (matches JS `$format: 'STRING'`).
- Caches successful translations; concurrent calls dedup + batch.
- Returns the interpolated SOURCE on any failure (never raises or returns None).
- Skips the API entirely when target == source locale.

All tests should FAIL until PR #1207 is ported (``tx`` is not yet exported).
"""

from __future__ import annotations

import asyncio
from collections.abc import Generator
from typing import TYPE_CHECKING, Any

import pytest
from gt_i18n import I18nManager, set_i18n_manager, tx  # `tx` does not exist yet

if TYPE_CHECKING:
    from conftest import FakeGT  # noqa: F401 — only for type hints


@pytest.fixture
def _install_manager(fake_gt: FakeGT) -> Generator[I18nManager, None, None]:
    """Install an I18nManager as the module singleton for ``tx()`` to consume."""
    manager = I18nManager(
        default_locale="en",
        locales=["en", "es", "fr"],
        load_translations=lambda locale: {},
        batch_interval_ms=5,
    )
    set_i18n_manager(manager)
    yield manager


# ---------------------------------------------------------------------------
# test_tx_fetches_and_interpolates
#
# Example:
#     result = await tx("Hello, {name}!", name="Alice", _locale="es", _format="ICU")
#     # → Mock returns "[es]Hello, {name}!" → interpolation yields "[es]Hello, Alice!"
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_tx_fetches_and_interpolates(_install_manager: I18nManager, fake_gt: FakeGT) -> None:
    """``tx()`` fetches a runtime translation and interpolates variables into the result."""
    _install_manager.set_locale("es")

    result = await tx("Hello, {name}!", name="Alice", _locale="es", _format="ICU")

    assert result == "[es]Hello, Alice!"
    assert len(fake_gt.calls) == 1


# ---------------------------------------------------------------------------
# test_tx_falls_back_to_source_on_api_error
#
# When the batch response indicates failure, ``tx()`` returns the
# interpolated SOURCE — never raises, never returns None.
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_tx_falls_back_to_source_on_api_error(_install_manager: I18nManager, fake_gt: FakeGT) -> None:
    """A per-entry failure in the batch response → ``tx()`` returns the interpolated source."""

    def all_failed(sources: dict[str, Any], options: dict[str, Any]) -> dict[str, Any]:
        return {h: {"success": False, "error": "upstream", "code": 500} for h in sources.keys()}

    fake_gt.response_factory = all_failed
    _install_manager.set_locale("es")

    result = await tx("Hello", _locale="es")

    # Interpolated source is returned (for "Hello" with no vars, that's just "Hello").
    assert result == "Hello"


# ---------------------------------------------------------------------------
# test_tx_source_locale_skips_api
#
# When target locale == default/source locale, there's nothing to translate.
# ``tx()`` short-circuits: no API call, returns the interpolated source.
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_tx_source_locale_skips_api(_install_manager: I18nManager, fake_gt: FakeGT) -> None:
    """``tx()`` with target == source locale skips the API and returns the source."""
    _install_manager.set_locale("en")  # default_locale is "en"

    result = await tx("Hello, {name}!", name="Alice", _format="ICU")

    assert result == "Hello, Alice!"
    assert len(fake_gt.calls) == 0, "target == source locale must not fire translate_many"


# ---------------------------------------------------------------------------
# test_tx_passes_context_id_max_chars_to_request_metadata
#
# Per-call options flow through to the request body's `metadata`:
#   metadata = {context, id, maxChars, dataFormat: "STRING", hash}
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_tx_passes_context_id_max_chars_to_request_metadata(
    _install_manager: I18nManager, fake_gt: FakeGT
) -> None:
    """``tx()`` propagates ``_context`` / ``_id`` / ``_max_chars`` into request metadata."""
    _install_manager.set_locale("es")

    await tx("Save", _context="button", _id="save.button", _max_chars=20, _locale="es")

    assert len(fake_gt.calls) == 1
    entry = next(iter(fake_gt.calls[0]["sources"].values()))
    meta = entry["metadata"]
    assert meta["context"] == "button"
    assert meta["id"] == "save.button"
    assert meta["maxChars"] == 20
    assert meta["dataFormat"] == "STRING", "tx() defaults $format=STRING, mirroring JS"


# ---------------------------------------------------------------------------
# test_tx_batches_concurrent_calls
#
# Multiple concurrent ``tx()`` calls coalesce into a single API request.
# This is the dedup/batching guarantee that makes ``tx()`` safe in hot paths.
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_tx_batches_concurrent_calls(_install_manager: I18nManager, fake_gt: FakeGT) -> None:
    """Concurrent distinct ``tx()`` calls are batched into one translate_many call."""
    _install_manager.set_locale("es")

    results = await asyncio.gather(
        tx("alpha", _locale="es"),
        tx("beta", _locale="es"),
        tx("gamma", _locale="es"),
    )

    assert results == ["[es]alpha", "[es]beta", "[es]gamma"]
    assert len(fake_gt.calls) == 1
    assert len(fake_gt.calls[0]["sources"]) == 3


# ---------------------------------------------------------------------------
# test_tx_locale_override_per_call
#
# Passing ``_locale`` per call overrides the manager's current locale for
# THIS call only. Enables "translate THIS into French" on the fly.
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_tx_locale_override_per_call(_install_manager: I18nManager, fake_gt: FakeGT) -> None:
    """``_locale`` per-call override targets that locale instead of the manager's current one."""
    _install_manager.set_locale("es")  # current locale is Spanish

    # …but this call asks for French.
    result = await tx("Hello", _locale="fr")

    assert result == "[fr]Hello"
    assert len(fake_gt.calls) == 1
    target = fake_gt.calls[0]["options"].get("target_locale") or fake_gt.calls[0]["options"].get("targetLocale")
    assert target == "fr"


# ---------------------------------------------------------------------------
# test_tx_public_export
#
# Smoke test: ``tx`` is importable from the top-level ``gt_i18n`` package
# and is an async callable.
# ---------------------------------------------------------------------------


def test_tx_public_export() -> None:
    """``tx`` is a public export and is a coroutine function."""
    import gt_i18n

    assert hasattr(gt_i18n, "tx"), "gt_i18n.tx should be a public export"
    assert asyncio.iscoroutinefunction(gt_i18n.tx)
    assert "tx" in gt_i18n.__all__

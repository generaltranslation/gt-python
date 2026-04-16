"""Shared test infrastructure for gt-i18n.

Makes the tests directory importable (so ``helpers.py`` can be used),
provides the shared ``fake_gt`` fixture used by runtime-translation tests,
and resets the I18nManager singleton between tests.
"""

from __future__ import annotations

import asyncio
import sys
from collections.abc import Awaitable, Callable, Generator
from pathlib import Path
from typing import Any

import pytest

sys.path.insert(0, str(Path(__file__).parent))


# ---------------------------------------------------------------------------
# FakeGT — test double for the GT class used for runtime translation.
# ---------------------------------------------------------------------------


class FakeGT:
    """Test double mirroring ``GT.translate_many`` for runtime-translation tests.

    Records every call and returns a configurable response. Supports simulating
    slow / pending requests for concurrency / batching tests.

    Example:
        gt = FakeGT()
        # Default response: echo each source prefixed with [locale].
        result = await gt.translate_many(
            {"h1": {"source": "Hello", "metadata": {"dataFormat": "STRING"}}},
            {"target_locale": "es"},
        )
        # → {"h1": {"success": True, "translation": "[es]Hello", "locale": "es"}}
    """

    def __init__(self) -> None:
        # Each entry: {"sources": dict, "options": dict, "timeout": int | None}
        self.calls: list[dict[str, Any]] = []

        # Default: echo with [locale] prefix. Override to return custom payloads.
        def _default_factory(sources: dict[str, Any], options: dict[str, Any]) -> dict[str, Any]:
            locale = options.get("target_locale", options.get("targetLocale", "?"))
            return {
                h: {
                    "success": True,
                    "translation": f"[{locale}]{entry['source']}",
                    "locale": locale,
                }
                for h, entry in sources.items()
            }

        self.response_factory: Callable[[dict[str, Any], dict[str, Any]], dict[str, Any]] = _default_factory

        # Added sleep before returning a response. Used for concurrency tests.
        self.delay_s: float = 0.0

        # When set, the mock awaits this event before returning. Used to hold
        # requests "in flight" so we can observe max-concurrency behavior.
        self.inflight_event: asyncio.Event | None = None

        # Running count of in-flight requests (increments on entry, decrements on exit).
        self.inflight_count: int = 0
        self.max_inflight: int = 0

    async def translate_many(
        self,
        sources: dict[str, Any] | list[Any],
        options: dict[str, Any] | str,
        timeout: int | None = None,
    ) -> dict[str, Any] | list[Any]:
        """Mirror ``GT.translate_many(sources, options, timeout)`` signature."""
        if isinstance(options, str):
            options = {"target_locale": options}
        if isinstance(sources, list):
            raise AssertionError(
                "FakeGT only supports dict `sources` — runtime translation batches are dict-keyed by hash."
            )
        self.calls.append({"sources": dict(sources), "options": dict(options), "timeout": timeout})

        self.inflight_count += 1
        self.max_inflight = max(self.max_inflight, self.inflight_count)
        try:
            if self.inflight_event is not None:
                await self.inflight_event.wait()
            if self.delay_s:
                await asyncio.sleep(self.delay_s)
            return self.response_factory(sources, options)
        finally:
            self.inflight_count -= 1


@pytest.fixture
def fake_gt(monkeypatch: pytest.MonkeyPatch) -> FakeGT:
    """Install a ``FakeGT`` in place of any ``GT`` instance the I18nManager constructs.

    Patches both ``I18nManager.get_gt_instance`` and the ``GT`` class import inside the
    internal i18n-manager modules, so regardless of how the implementation wires up
    runtime translation, tests still route through the fake.

    Tests that drive the public API (``tx()``, ``I18nManager``) get the fake automatically.
    Tests that instantiate ``TranslationsCache`` directly can bind ``fake_gt.translate_many``
    as the ``translate_many`` callable.
    """
    gt = FakeGT()

    try:
        from gt_i18n import I18nManager

        monkeypatch.setattr(I18nManager, "get_gt_instance", lambda self: gt)
    except ImportError:
        pass

    for path in (
        "gt_i18n.i18n_manager._i18n_manager.GT",
        "gt_i18n.i18n_manager._translations_cache.GT",
        "gt_i18n.i18n_manager._locales_cache.GT",
    ):
        try:
            monkeypatch.setattr(path, lambda *a, **kw: gt, raising=False)
        except (ModuleNotFoundError, ImportError):
            pass

    return gt


@pytest.fixture
def translate_many_for_locale(
    fake_gt: FakeGT,
) -> Callable[[str], Callable[[dict[str, Any]], Awaitable[dict[str, Any]]]]:
    """Return a factory that binds ``fake_gt.translate_many`` to a specific target locale.

    Mirrors the JS ``createTranslateMany(locale) => (sources) => gt.translateMany(...)``
    factory pattern. Convenient for directly instantiating ``TranslationsCache`` in tests.

    Example:
        translate_many = translate_many_for_locale("es")
        cache = TranslationsCache(locale="es", translate_many=translate_many, ...)
    """

    def make(locale: str) -> Callable[[dict[str, Any]], Awaitable[dict[str, Any]]]:
        async def _translate_many(sources: dict[str, Any]) -> dict[str, Any]:
            result = await fake_gt.translate_many(sources, {"target_locale": locale})
            assert isinstance(result, dict)
            return result

        return _translate_many

    return make


# ---------------------------------------------------------------------------
# Singleton reset — prevents cross-test state leakage.
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _reset_i18n_manager_singleton() -> Generator[None, None, None]:
    """Reset the module-level I18nManager singleton between tests."""
    import gt_i18n.i18n_manager._singleton as mod

    old = mod._manager
    yield
    mod._manager = old

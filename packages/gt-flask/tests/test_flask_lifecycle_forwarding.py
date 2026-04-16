"""Golden-standard test: ``initialize_gt()`` forwards the ``lifecycle`` kwarg.

Sibling to the identically-named test in gt-fastapi. Both frameworks are thin
pass-throughs to ``I18nManager(...)`` and both must accept and forward the
``lifecycle`` kwarg so users can observe cache behavior without bypassing
``initialize_gt``.

This test should FAIL until PR #1207 is ported.
"""

from __future__ import annotations

from collections.abc import Generator
from typing import Any

import pytest
from flask import Flask
from gt_flask import initialize_gt
from gt_i18n.i18n_manager._i18n_manager import I18nManager


@pytest.fixture(autouse=True)
def _reset_singleton() -> Generator[None, None, None]:
    import gt_i18n.i18n_manager._singleton as mod

    old = mod._manager
    yield
    mod._manager = old


class _FakeGT:
    """Minimal GT test double returning an echoing translation."""

    async def translate_many(
        self,
        sources: dict[str, Any],
        options: dict[str, Any] | str,
        timeout: int | None = None,
    ) -> dict[str, Any]:
        if isinstance(options, str):
            options = {"target_locale": options}
        locale = options.get("target_locale", options.get("targetLocale", "?"))
        return {
            h: {"success": True, "translation": f"[{locale}]{entry['source']}", "locale": locale}
            for h, entry in sources.items()
        }


# ---------------------------------------------------------------------------
# test_flask_initialize_gt_forwards_lifecycle_kwarg
#
# Example:
#     events = []
#     manager = initialize_gt(
#         app,
#         default_locale="en", locales=["en", "es"],
#         load_translations=lambda loc: {},
#         lifecycle={"on_translations_cache_miss": lambda **p: events.append(p)},
#     )
#     # After a runtime miss, `events` has one entry.
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_flask_initialize_gt_forwards_lifecycle_kwarg(monkeypatch: pytest.MonkeyPatch) -> None:
    """``initialize_gt`` accepts ``lifecycle`` and wires it through to the I18nManager."""
    gt = _FakeGT()
    monkeypatch.setattr(I18nManager, "get_gt_instance", lambda self: gt)

    events: list[dict[str, Any]] = []

    app = Flask(__name__)
    manager = initialize_gt(
        app,
        default_locale="en",
        locales=["en", "es"],
        load_translations=lambda locale: {},
        eager_loading=False,
        lifecycle={
            "on_translations_cache_miss": lambda *, locale, hash, value: events.append(
                {"locale": locale, "hash": hash, "value": value}
            ),
        },
    )

    manager.set_locale("es")
    await manager.lookup_translation_with_fallback("Hello", _format="STRING")

    assert len(events) == 1, "on_translations_cache_miss should have fired once via the forwarded lifecycle dict"
    assert events[0]["locale"] == "es"
    assert events[0]["value"] == "[es]Hello"

"""Lifecycle callback TypedDict for cache hits / misses.

Mirrors the JS ``LifecycleCallbacks`` type introduced in gt PR #1207. All
callbacks are optional; consumers can observe any subset of events.

Callbacks are invoked with keyword arguments (Pythonic) rather than a single
params object. Example:

    def on_miss(*, locale: str, hash: str, value: str) -> None:
        log.info("runtime fetch for %s/%s", locale, hash)

    manager = I18nManager(
        ...,
        lifecycle={"on_translations_cache_miss": on_miss},
    )
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, TypedDict


class LifecycleCallbacks(TypedDict, total=False):
    """Optional hooks for observing translation cache behavior.

    Keys:
        on_locales_cache_hit: Fires when a locale's translations dict is read
            from the outer LocalesCache. Kwargs: ``locale``, ``value``.
        on_locales_cache_miss: Fires after the user loader completes for a
            locale. Kwargs: ``locale``, ``value``.
        on_translations_cache_hit: Fires when a translation is read from the
            inner TranslationsCache. Kwargs: ``locale``, ``hash``, ``value``.
        on_translations_cache_miss: Fires after a runtime translate fetch
            populates the cache. Kwargs: ``locale``, ``hash``, ``value``.
    """

    on_locales_cache_hit: Callable[..., Any]
    on_locales_cache_miss: Callable[..., Any]
    on_translations_cache_hit: Callable[..., Any]
    on_translations_cache_miss: Callable[..., Any]

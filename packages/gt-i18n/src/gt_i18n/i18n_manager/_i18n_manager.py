"""I18nManager — central orchestrator for i18n operations.

Post gt PR #1207: the manager owns a ``LocalesCache`` (outer) whose entries
each own a ``TranslationsCache`` (inner, hash-keyed, batched). All lookup
traffic flows through this two-level cache. Runtime translate calls go to
``GT.translate_many`` via a ``create_translate_many_factory`` that defers GT
construction to ``self.get_gt_instance()`` so tests can patch it cleanly.
"""

from __future__ import annotations

import asyncio
import warnings
from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING, Any

from generaltranslation import CustomMapping
from generaltranslation._gt import GT
from generaltranslation._settings import LIBRARY_DEFAULT_LOCALE
from generaltranslation.locales import requires_translation

from gt_i18n.i18n_manager._context_var_adapter import ContextVarStorageAdapter
from gt_i18n.i18n_manager._lifecycle import LifecycleCallbacks
from gt_i18n.i18n_manager._locales_cache import LocalesCache
from gt_i18n.i18n_manager._storage_adapter import StorageAdapter
from gt_i18n.i18n_manager._translate_many_factory import (
    DEFAULT_TRANSLATION_TIMEOUT_MS,
    create_translate_many_factory,
)

if TYPE_CHECKING:
    from gt_i18n.i18n_manager._remote_loader import TranslationsLoader


class I18nManager:
    """Central orchestrator for i18n operations."""

    def __init__(
        self,
        *,
        default_locale: str = LIBRARY_DEFAULT_LOCALE,
        locales: list[str] | None = None,
        project_id: str | None = None,
        cache_url: str | None = None,
        custom_mapping: CustomMapping | None = None,
        store_adapter: StorageAdapter | None = None,
        load_translations: TranslationsLoader | None = None,
        cache_expiry_time: int = 60_000,
        version_id: str | None = None,
        lifecycle: LifecycleCallbacks | None = None,
        batch_size: int = 25,
        batch_interval_ms: int = 50,
        max_concurrent_requests: int = 100,
        translation_timeout_ms: int = DEFAULT_TRANSLATION_TIMEOUT_MS,
    ) -> None:
        self._version_id = version_id
        self._default_locale = default_locale
        locales_set: set[str] = {default_locale, *(locales or [])}
        self._locales = list(locales_set)
        self._project_id = project_id
        self._cache_url = cache_url
        self._custom_mapping = custom_mapping

        # Storage
        self._store: StorageAdapter = store_adapter or ContextVarStorageAdapter()

        # Translation loader — user-provided, CDN (if project_id), or no-op.
        if load_translations is not None:
            loader: TranslationsLoader = load_translations
        elif project_id:
            from gt_i18n.i18n_manager._remote_loader import (
                create_remote_translation_loader,
            )

            loader = create_remote_translation_loader(project_id, cache_url or "")
        else:
            loader = lambda locale: {}  # noqa: E731
        self._load_translations: TranslationsLoader = loader

        # Two-level cache hierarchy.
        self._lifecycle: LifecycleCallbacks = lifecycle or {}
        self._locales_cache = LocalesCache(
            load_translations=loader,
            create_translate_many=create_translate_many_factory(
                self.get_gt_instance,
                timeout_ms=translation_timeout_ms,
            ),
            ttl_ms=cache_expiry_time,
            batch_size=batch_size,
            batch_interval_ms=batch_interval_ms,
            max_concurrent_requests=max_concurrent_requests,
            lifecycle=self._lifecycle,
        )

    # -- basic properties --------------------------------------------------

    @property
    def default_locale(self) -> str:
        return self._default_locale

    def get_gt_instance(self) -> GT:
        """Get a new GT instance for the current request."""
        return GT(
            project_id=self._project_id,
            source_locale=self._default_locale,
            target_locale=self.get_locale(),
            locales=self._locales,
            custom_mapping=self._custom_mapping,
        )

    def get_version_id(self) -> str | None:
        return self._version_id

    def get_locales(self) -> list[str]:
        return list(self._locales)

    def get_locale(self) -> str:
        locale = self._store.get_item("locale")
        return locale or self._default_locale

    def set_locale(self, locale: str) -> None:
        self._store.set_item("locale", locale)

    def requires_translation(self, locale: str | None = None) -> bool:
        target = locale or self.get_locale()
        return requires_translation(
            self._default_locale,
            target,
            approved_locales=self._locales or None,
        )

    # -- translation lookup (new API) -------------------------------------

    def lookup_translation(self, message: str, **options: Any) -> str | None:
        """Sync dict-cache lookup. Never fires a network call. Returns None on miss."""
        locale = options.pop("_locale", None) or self.get_locale()
        if not self.requires_translation(locale):
            return None
        tc = self._locales_cache.get(locale)
        if tc is None:
            return None
        return tc.get({"message": message, "options": options})

    async def lookup_translation_with_fallback(self, message: str, **options: Any) -> str | None:
        """Cache-hit sync; on miss, fetch via runtime translate_many."""
        locale = options.pop("_locale", None) or self.get_locale()
        if not self.requires_translation(locale):
            return None
        tc = self._locales_cache.get(locale)
        if tc is None:
            tc = await self._locales_cache.miss(locale)
        return await tc.miss({"message": message, "options": options})

    async def load_translations(self, locale: str | None = None) -> dict[str, str]:
        """Load (or return cached) translations dict for the locale."""
        target = locale or self.get_locale()
        await self._locales_cache.miss(target)
        entry = self._locales_cache._cache.get(target)
        return dict(entry.translations) if entry else {}

    async def get_lookup_translation(
        self,
        locale: str | None = None,
        prefetch: list[dict[str, Any]] | None = None,
    ) -> Callable[[str, dict[str, Any]], str | None]:
        """Prefetch entries for ``locale``, then return a sync lookup callable."""
        target = locale or self.get_locale()
        tc = self._locales_cache.get(target)
        if tc is None:
            tc = await self._locales_cache.miss(target)
        if prefetch:
            await asyncio.gather(*(tc.miss(entry) for entry in prefetch))

        def _lookup(message: str, options: dict[str, Any]) -> str | None:
            return tc.get({"message": message, "options": options})

        return _lookup

    # -- translation lookup (legacy, deprecated) --------------------------

    async def get_translations(self, locale: str | None = None) -> dict[str, str]:
        """DEPRECATED: use ``load_translations`` instead."""
        warnings.warn(
            "I18nManager.get_translations is deprecated; use load_translations instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return await self.load_translations(locale)

    def get_translations_sync(self, locale: str | None = None) -> dict[str, str]:
        """Return cached translations dict (sync, empty if not yet loaded)."""
        target = locale or self.get_locale()
        entry = self._locales_cache._cache.get(target)
        if entry is None:
            return {}
        # Respect TTL — expired entries shouldn't leak stale data.
        import time as _time

        if entry.expires_at < _time.monotonic():
            return {}
        return dict(entry.translations)

    async def load_all_translations(self) -> None:
        """Eagerly load translations for all configured locales concurrently."""
        if self._locales:
            await asyncio.gather(*(self._locales_cache.miss(loc) for loc in self._locales))

    async def get_translation_resolver(
        self,
        locale: str | None = None,
    ) -> Callable[[str, dict[str, Any]], str | None]:
        """DEPRECATED: use ``get_lookup_translation`` instead."""
        warnings.warn(
            "I18nManager.get_translation_resolver is deprecated; use get_lookup_translation instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return await self.get_lookup_translation(locale)

    def resolve_translation_sync(self, message: str, options: dict[str, Any]) -> str | None:
        """DEPRECATED: use ``lookup_translation`` instead."""
        warnings.warn(
            "I18nManager.resolve_translation_sync is deprecated; use lookup_translation instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.lookup_translation(message, **options)

    def get_translation_loader(self) -> Callable[[str], dict[str, str] | Awaitable[dict[str, str]]]:
        """DEPRECATED: pass ``load_translations`` directly to the constructor instead."""
        warnings.warn(
            "I18nManager.get_translation_loader is deprecated; pass load_translations directly.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self._load_translations

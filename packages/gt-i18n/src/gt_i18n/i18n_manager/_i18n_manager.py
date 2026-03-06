"""I18nManager — central orchestrator for i18n operations."""

from __future__ import annotations

from typing import TYPE_CHECKING

from generaltranslation._settings import LIBRARY_DEFAULT_LOCALE
from generaltranslation.locales import requires_translation

from gt_i18n.i18n_manager._context_var_adapter import ContextVarStorageAdapter
from gt_i18n.i18n_manager._storage_adapter import StorageAdapter
from gt_i18n.i18n_manager._translations_manager import TranslationsManager

if TYPE_CHECKING:
    from gt_i18n.i18n_manager._remote_loader import TranslationsLoader


class I18nManager:
    """Central orchestrator for i18n operations.

    Args:
        default_locale: The source/default locale.
        locales: List of target locales the application supports.
        project_id: GT project ID (used for CDN loader).
        cache_url: CDN base URL override.
        store_adapter: Custom storage adapter. Defaults to
            :class:`ContextVarStorageAdapter`.
        load_translations: Custom translation loader. Overrides the
            remote CDN loader when provided.
        cache_expiry_time: Cache expiry in milliseconds.
    """

    def __init__(
        self,
        *,
        default_locale: str = LIBRARY_DEFAULT_LOCALE,
        locales: list[str] | None = None,
        project_id: str | None = None,
        cache_url: str | None = None,
        store_adapter: StorageAdapter | None = None,
        load_translations: TranslationsLoader | None = None,
        cache_expiry_time: int = 60_000,
    ) -> None:
        self._default_locale = default_locale
        self._locales = locales or []
        self._project_id = project_id

        # Storage
        self._store: StorageAdapter = store_adapter or ContextVarStorageAdapter()

        # Translation loading
        if load_translations is not None:
            loader = load_translations
        elif project_id:
            from gt_i18n.i18n_manager._remote_loader import (
                create_remote_translation_loader,
            )

            loader = create_remote_translation_loader(project_id, cache_url or "")
        else:
            loader = lambda locale: {}  # noqa: E731

        self._translations = TranslationsManager(loader, cache_expiry_time=cache_expiry_time)

    @property
    def default_locale(self) -> str:
        return self._default_locale

    def get_locales(self) -> list[str]:
        return list(self._locales)

    def get_locale(self) -> str:
        """Read the current request locale from the storage adapter."""
        locale = self._store.get_item("locale")
        return locale or self._default_locale

    def set_locale(self, locale: str) -> None:
        """Write the current request locale to the storage adapter."""
        self._store.set_item("locale", locale)

    def requires_translation(self, locale: str | None = None) -> bool:
        """Check if the given locale needs translation from the default."""
        target = locale or self.get_locale()
        return requires_translation(
            self._default_locale,
            target,
            approved_locales=self._locales or None,
        )

    async def get_translations(self, locale: str | None = None) -> dict[str, str]:
        """Get translations for a locale (async, loads if needed)."""
        target = locale or self.get_locale()
        return await self._translations.get_translations(target)

    def get_translations_sync(self, locale: str | None = None) -> dict[str, str]:
        """Get cached translations (sync, returns empty if not loaded)."""
        target = locale or self.get_locale()
        return self._translations.get_translations_sync(target)

    async def load_all_translations(self) -> None:
        """Eagerly load translations for all configured locales."""
        if self._locales:
            await self._translations.load_all(self._locales)

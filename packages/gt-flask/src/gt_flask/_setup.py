"""Flask integration: initialize_gt() and locale detection."""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from typing import Any

from generaltranslation import CustomMapping
from generaltranslation._settings import LIBRARY_DEFAULT_LOCALE
from gt_i18n import I18nManager, set_i18n_manager
from gt_i18n.internal import _detect_from_accept_language


def initialize_gt(
    app: Any,
    *,
    default_locale: str = LIBRARY_DEFAULT_LOCALE,
    locales: list[str] | None = None,
    custom_mapping: CustomMapping | None = None,
    project_id: str | None = None,
    cache_url: str | None = None,
    get_locale: Callable[..., str] | None = None,
    load_translations: Callable[[str], dict[str, str]] | None = None,
    eager_loading: bool = True,
) -> I18nManager:
    """Initialize General Translation for a Flask app.

    Args:
        app: The Flask application instance.
        default_locale: Source locale.
        locales: Target locales.
        project_id: GT project ID for CDN loading.
        cache_url: CDN base URL override.
        get_locale: Custom locale detection callback ``(request) -> str``.
        load_translations: Custom translation loader ``(locale) -> dict``.
        eager_loading: Load all translations at startup (default True).
        **kwargs: Additional kwargs passed to I18nManager.

    Returns:
        The configured I18nManager.
    """
    manager = I18nManager(
        default_locale=default_locale,
        locales=locales,
        custom_mapping=custom_mapping,
        project_id=project_id,
        cache_url=cache_url,
        load_translations=load_translations,
    )
    set_i18n_manager(manager)

    if eager_loading and locales:
        asyncio.run(manager.load_all_translations())

    @app.before_request
    def _set_locale() -> None:
        from flask import request

        if get_locale:
            locale = get_locale(request)
        else:
            locale = _detect_from_accept_language(request, manager)
        manager.set_locale(locale)

    return manager

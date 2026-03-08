"""FastAPI integration: initialize_gt() and locale detection."""

from __future__ import annotations

from collections.abc import AsyncGenerator, Callable
from contextlib import asynccontextmanager
from typing import Any

from generaltranslation import CustomMapping
from generaltranslation._settings import LIBRARY_DEFAULT_LOCALE
from gt_i18n import I18nManager, set_i18n_manager
from gt_i18n.internal import GTConfig, _detect_from_accept_language, load_gt_config


def initialize_gt(
    app: Any,
    *,
    default_locale: str | None = None,
    locales: list[str] | None = None,
    custom_mapping: CustomMapping | None = None,
    project_id: str | None = None,
    cache_url: str | None = None,
    get_locale: Callable[..., str] | None = None,
    load_translations: Callable[[str], dict[str, str]] | None = None,
    eager_loading: bool = True,
    config_path: str | None = None,
    load_config: Callable[[str | None], GTConfig] | None = None,
) -> I18nManager:
    """Initialize General Translation for a FastAPI app.

    Args:
        app: The FastAPI application instance.
        default_locale: Source locale.
        locales: Target locales.
        project_id: GT project ID for CDN loading.
        cache_url: CDN base URL override.
        get_locale: Custom locale detection callback ``(request) -> str``.
        load_translations: Custom translation loader ``(locale) -> dict``.
        eager_loading: Load all translations at startup (default True).
        config_path: Path to a ``gt.config.json`` file.
        load_config: Custom config loader replacing the default.

    Returns:
        The configured I18nManager.
    """
    if load_config is not None:
        file_config = load_config(config_path)
    elif config_path is not None:
        file_config = load_gt_config(config_path)
    else:
        file_config = load_gt_config()

    resolved_default_locale = default_locale or file_config.get("default_locale") or LIBRARY_DEFAULT_LOCALE
    resolved_locales = locales if locales is not None else file_config.get("locales")
    resolved_project_id = project_id or file_config.get("project_id")
    resolved_cache_url = cache_url or file_config.get("cache_url")
    resolved_custom_mapping = custom_mapping or file_config.get("custom_mapping")

    manager = I18nManager(
        default_locale=resolved_default_locale,
        locales=resolved_locales,
        custom_mapping=resolved_custom_mapping,
        project_id=resolved_project_id,
        cache_url=resolved_cache_url,
        load_translations=load_translations,
    )
    set_i18n_manager(manager)

    # Wrap existing lifespan if present
    existing_lifespan = getattr(app, "router", app).lifespan_context

    @asynccontextmanager
    async def _gt_lifespan(a: Any) -> AsyncGenerator[Any, None]:
        if eager_loading and locales:
            await manager.load_all_translations()
        async with existing_lifespan(a) as state:
            yield state

    app.router.lifespan_context = _gt_lifespan

    @app.middleware("http")
    async def gt_middleware(request: Any, call_next: Any) -> Any:
        if get_locale:
            locale = get_locale(request)
        else:
            locale = _detect_from_accept_language(request, manager)
        manager.set_locale(locale)
        return await call_next(request)

    return manager

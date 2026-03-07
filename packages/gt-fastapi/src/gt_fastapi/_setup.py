"""FastAPI integration: initialize_gt() and locale detection."""

from __future__ import annotations

from collections.abc import AsyncGenerator, Callable
from contextlib import asynccontextmanager
from typing import Any

from gt_i18n import I18nManager, set_i18n_manager
from gt_i18n.internal import _detect_from_accept_language
from generaltranslation import CustomMapping

def initialize_gt(
    app: Any,
    *,
    default_locale: str = "en",
    locales: list[str] | None = None,
    custom_mapping: CustomMapping | None = None,
    project_id: str | None = None,
    cache_url: str | None = None,
    get_locale: Callable[..., str] | None = None,
    load_translations: Callable[[str], dict[str, str]] | None = None,
    eager_loading: bool = True,
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

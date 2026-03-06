"""FastAPI integration: initialize_gt() and locale detection."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator, Callable

from generaltranslation.locales import determine_locale

from gt_i18n import I18nManager, set_i18n_manager, t  # noqa: F401


def _detect_from_accept_language(
    request: Any, manager: I18nManager
) -> str:
    """Parse Accept-Language header and resolve against configured locales."""
    accept = request.headers.get("accept-language", "")
    if not accept:
        return manager.default_locale

    locales: list[tuple[float, str]] = []
    for part in accept.split(","):
        part = part.strip()
        if not part:
            continue
        if ";q=" in part:
            lang, q = part.split(";q=", 1)
            try:
                quality = float(q.strip())
            except ValueError:
                quality = 0.0
            locales.append((quality, lang.strip()))
        else:
            locales.append((1.0, part))

    locales.sort(key=lambda x: x[0], reverse=True)
    locale_list = [loc for _, loc in locales]

    approved = manager.get_locales()
    if not approved:
        return locale_list[0] if locale_list else manager.default_locale

    result = determine_locale(locale_list, approved)
    return result or manager.default_locale


def initialize_gt(
    app: Any,
    *,
    default_locale: str = "en",
    locales: list[str] | None = None,
    project_id: str | None = None,
    cache_url: str | None = None,
    get_locale: Callable[..., str] | None = None,
    load_translations: Callable[[str], dict[str, str]] | None = None,
    eager_loading: bool = True,
    **kwargs: Any,
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
        project_id=project_id,
        cache_url=cache_url,
        load_translations=load_translations,
        **kwargs,
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

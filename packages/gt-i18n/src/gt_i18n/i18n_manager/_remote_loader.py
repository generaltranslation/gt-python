"""CDN translation loader using httpx."""

from __future__ import annotations

from collections.abc import Awaitable, Callable

import httpx
from generaltranslation._settings import DEFAULT_CACHE_URL

TranslationsLoader = Callable[[str], dict[str, str] | Awaitable[dict[str, str]]]


def create_remote_translation_loader(
    project_id: str,
    cache_url: str | None = None,
    *,
    version_id: str | None = None,
    branch_id: str | None = None,
) -> TranslationsLoader:
    """Create a loader that fetches translations from the CDN.

    Args:
        project_id: The GT project ID.
        cache_url: CDN base URL. Defaults to the General Translation CDN.
        version_id: Pins the translations to one published version.
        branch_id: The General Translation branch the version belongs to.

    Returns:
        An async callable ``(locale) -> dict[str, str]`` that raises when the
        request fails or returns no translations, so the cache keeps its
        previous translations. The CDN answers some server-side failures with
        an empty object, which is why empty counts as a failure here.
    """
    base = f"{cache_url or DEFAULT_CACHE_URL}/{project_id}"
    version = f"/{version_id}" if version_id else ""
    params = {"branchId": branch_id} if branch_id else None

    async def loader(locale: str) -> dict[str, str]:
        url = f"{base}/{locale}{version}"
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, params=params, timeout=10.0)
        resp.raise_for_status()
        data = resp.json()
        if not isinstance(data, dict) or not data:
            raise ValueError(f"No translations in the response from {url}")
        return data

    return loader

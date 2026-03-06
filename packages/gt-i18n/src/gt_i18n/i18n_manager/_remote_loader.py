"""CDN translation loader using httpx."""

from __future__ import annotations

from collections.abc import Awaitable, Callable

import httpx
from generaltranslation._settings import DEFAULT_CACHE_URL

TranslationsLoader = Callable[[str], dict[str, str] | Awaitable[dict[str, str]]]


def create_remote_translation_loader(
    project_id: str,
    cache_url: str = DEFAULT_CACHE_URL,
) -> TranslationsLoader:
    """Create a loader that fetches translations from the CDN.

    Args:
        project_id: The GT project ID.
        cache_url: CDN base URL.

    Returns:
        An async callable ``(locale) -> dict[str, str]``.
    """

    async def loader(locale: str) -> dict[str, str]:
        url = f"{cache_url}/{project_id}/{locale}"
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(url, timeout=10.0)
                if resp.status_code == 200:
                    data = resp.json()
                    if isinstance(data, dict):
                        return data
        except Exception:
            pass
        return {}

    return loader

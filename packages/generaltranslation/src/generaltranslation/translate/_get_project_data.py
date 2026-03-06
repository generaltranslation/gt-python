"""Get project data endpoint."""

from __future__ import annotations

from typing import Any
from urllib.parse import quote

from generaltranslation.translate._request import api_request


async def get_project_data(
    project_id: str,
    options: dict[str, Any],
    config: dict[str, Any],
) -> dict[str, Any]:
    """Get project data for a given project ID."""
    encoded_id = quote(project_id, safe="!'()*-._~")
    endpoint = f"/v2/project/info/{encoded_id}"
    return await api_request(
        config,
        endpoint,
        method="GET",
        timeout=options.get("timeout"),
    )

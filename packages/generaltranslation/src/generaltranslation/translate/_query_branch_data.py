"""Query branch data endpoint."""

from __future__ import annotations

from typing import Any

from generaltranslation.translate._request import api_request


async def query_branch_data(
    query: dict[str, Any],
    config: dict[str, Any],
) -> dict[str, Any]:
    """Query branch information from the API."""
    return await api_request(
        config,
        "/v2/project/branches/info",
        body=query,
    )

"""Create branch endpoint."""

from __future__ import annotations

from typing import Any

from generaltranslation.translate._request import api_request


async def create_branch(
    query: dict[str, Any],
    config: dict[str, Any],
) -> dict[str, Any]:
    """Create a new branch in the API."""
    return await api_request(
        config,
        "/v2/project/branches/create",
        body=query,
    )

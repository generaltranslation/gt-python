"""Query source file endpoint."""

from __future__ import annotations

from typing import Any
from urllib.parse import quote, urlencode

from generaltranslation.translate._request import api_request


async def query_source_file(
    query: dict[str, Any],
    options: dict[str, Any],
    config: dict[str, Any],
) -> dict[str, Any]:
    """Get source file and translation information for a given file ID."""
    file_id = query.get("file_id", query.get("fileId", ""))
    branch_id = query.get("branch_id", query.get("branchId"))
    version_id = query.get("version_id", query.get("versionId"))

    params: dict[str, str] = {}
    if branch_id:
        params["branchId"] = branch_id
    if version_id:
        params["versionId"] = version_id

    qs = urlencode(params) if params else ""
    encoded_file_id = quote(file_id, safe="!'()*-._~")
    endpoint = f"/v2/project/translations/files/status/{encoded_file_id}"
    if qs:
        endpoint = f"{endpoint}?{qs}"

    return await api_request(
        config,
        endpoint,
        method="GET",
        timeout=options.get("timeout"),
    )

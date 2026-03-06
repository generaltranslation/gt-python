"""Generate request headers for API calls."""

from __future__ import annotations

from typing import Any

from generaltranslation._settings import API_VERSION


def generate_request_headers(config: dict[str, Any], *, exclude_content_type: bool = False) -> dict[str, str]:
    headers: dict[str, str] = {}
    if not exclude_content_type:
        headers["Content-Type"] = "application/json"
    headers["x-gt-project-id"] = config.get("project_id", "")

    api_key = config.get("api_key", "")
    if api_key:
        if api_key.startswith("gtx-internal-"):
            headers["x-gt-internal-api-key"] = api_key
        else:
            headers["x-gt-api-key"] = api_key

    headers["gt-api-version"] = API_VERSION
    return headers

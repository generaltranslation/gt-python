"""Setup project endpoint."""

from __future__ import annotations

from typing import Any, Optional

from generaltranslation.translate._request import api_request


async def setup_project(
    files: list[dict[str, Any]],
    config: dict[str, Any],
    options: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """Enqueue files for project setup."""
    options = options or {}
    body: dict[str, Any] = {
        "files": [
            {
                "branchId": f.get("branch_id", f.get("branchId", "")),
                "fileId": f.get("file_id", f.get("fileId", "")),
                "versionId": f.get("version_id", f.get("versionId", "")),
            }
            for f in files
        ],
    }
    if options.get("locales"):
        body["locales"] = options["locales"]
    if options.get("force") is not None:
        body["force"] = options["force"]

    return await api_request(
        config,
        "/v2/project/setup/generate",
        body=body,
        timeout=options.get("timeout_ms"),
    )

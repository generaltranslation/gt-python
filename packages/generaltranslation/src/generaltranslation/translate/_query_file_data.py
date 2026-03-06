"""Query file data endpoint."""

from __future__ import annotations

from typing import Any

from generaltranslation.translate._request import api_request


async def query_file_data(
    data: dict[str, Any],
    options: dict[str, Any],
    config: dict[str, Any],
) -> dict[str, Any]:
    """Query data about one or more source or translation files."""
    body: dict[str, Any] = {}
    if data.get("source_files") or data.get("sourceFiles"):
        source_files = data.get("source_files") or data.get("sourceFiles") or []
        body["sourceFiles"] = [
            {
                "fileId": item.get("file_id", item.get("fileId", "")),
                "versionId": item.get("version_id", item.get("versionId", "")),
                "branchId": item.get("branch_id", item.get("branchId", "")),
            }
            for item in source_files
        ]
    if data.get("translated_files") or data.get("translatedFiles"):
        translated_files = data.get("translated_files") or data.get("translatedFiles") or []
        body["translatedFiles"] = [
            {
                "fileId": item.get("file_id", item.get("fileId", "")),
                "versionId": item.get("version_id", item.get("versionId", "")),
                "branchId": item.get("branch_id", item.get("branchId", "")),
                "locale": item.get("locale", ""),
            }
            for item in translated_files
        ]

    return await api_request(
        config,
        "/v2/project/files/info",
        body=body,
        timeout=options.get("timeout"),
    )

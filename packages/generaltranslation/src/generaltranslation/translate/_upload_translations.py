"""Upload translations endpoint."""

from __future__ import annotations

import base64
from typing import Any

from generaltranslation.translate._batch import process_batches
from generaltranslation.translate._request import api_request


async def upload_translations(
    files: list[dict[str, Any]],
    options: dict[str, Any],
    config: dict[str, Any],
) -> dict[str, Any]:
    """Upload translations to the API in batches."""

    async def _process_batch(batch: list[dict[str, Any]]) -> list[Any]:
        body = {
            "data": [
                {
                    "source": {
                        "content": base64.b64encode(
                            item["source"]["content"].encode()
                        ).decode(),
                        "fileName": item["source"].get(
                            "file_name", item["source"].get("fileName", "")
                        ),
                        "fileFormat": item["source"].get(
                            "file_format", item["source"].get("fileFormat", "")
                        ),
                        "locale": item["source"].get("locale", ""),
                        "dataFormat": item["source"].get(
                            "data_format", item["source"].get("dataFormat")
                        ),
                        "formatMetadata": item["source"].get(
                            "format_metadata", item["source"].get("formatMetadata")
                        ),
                        "fileId": item["source"].get(
                            "file_id", item["source"].get("fileId")
                        ),
                        "versionId": item["source"].get(
                            "version_id", item["source"].get("versionId")
                        ),
                        "branchId": item["source"].get(
                            "branch_id", item["source"].get("branchId")
                        ),
                    },
                    "translations": [
                        {
                            "content": base64.b64encode(t["content"].encode()).decode(),
                            "fileName": t.get("file_name", t.get("fileName", "")),
                            "fileFormat": t.get("file_format", t.get("fileFormat", "")),
                            "locale": t.get("locale", ""),
                            "dataFormat": t.get("data_format", t.get("dataFormat")),
                            "fileId": t.get("file_id", t.get("fileId")),
                            "versionId": t.get("version_id", t.get("versionId")),
                            "branchId": t.get("branch_id", t.get("branchId")),
                        }
                        for t in item.get("translations", [])
                    ],
                }
                for item in batch
            ],
            "sourceLocale": options.get(
                "source_locale", options.get("sourceLocale", "")
            ),
        }
        result = await api_request(
            config,
            "/v2/project/files/upload-translations",
            body=body,
            timeout=options.get("timeout"),
        )
        return result.get("uploadedFiles", [])

    return await process_batches(files, _process_batch, batch_size=100)

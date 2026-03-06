"""Download multiple translation files in batches."""

from __future__ import annotations

import base64
from typing import Any

from generaltranslation.translate._batch import process_batches
from generaltranslation.translate._request import api_request


async def download_file_batch(
    requests: list[dict[str, Any]],
    options: dict[str, Any],
    config: dict[str, Any],
) -> dict[str, Any]:
    """Download multiple translation files in batches."""

    async def _process_batch(batch: list[dict[str, Any]]) -> list[Any]:
        result = await api_request(
            config,
            "/v2/project/files/download",
            body=batch,
            timeout=options.get("timeout"),
        )
        files = []
        for f in result.get("files", []):
            decoded = {**f}
            decoded["data"] = base64.b64decode(f["data"]).decode("utf-8")
            files.append(decoded)
        return files

    return await process_batches(requests, _process_batch, batch_size=100)

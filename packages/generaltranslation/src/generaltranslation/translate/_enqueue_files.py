"""Enqueue files for translation."""

from __future__ import annotations

from typing import Any

from generaltranslation.translate._batch import process_batches
from generaltranslation.translate._request import api_request


async def enqueue_files(
    files: list[dict[str, Any]],
    options: dict[str, Any],
    config: dict[str, Any],
) -> dict[str, Any]:
    """Enqueue files for translation in batches."""

    async def _process_batch(batch: list[dict[str, Any]]) -> list[Any]:
        body: dict[str, Any] = {
            "files": [
                {
                    "branchId": f.get("branch_id", f.get("branchId", "")),
                    "fileId": f.get("file_id", f.get("fileId", "")),
                    "versionId": f.get("version_id", f.get("versionId", "")),
                    "fileName": f.get("file_name", f.get("fileName", "")),
                }
                for f in batch
            ],
            "targetLocales": options.get("target_locales", options.get("targetLocales", [])),
            "sourceLocale": options.get("source_locale", options.get("sourceLocale", "")),
            "publish": options.get("publish"),
            "requireApproval": options.get("require_approval", options.get("requireApproval")),
            "modelProvider": options.get("model_provider", options.get("modelProvider")),
            "force": options.get("force"),
        }
        body = {k: v for k, v in body.items() if v is not None}
        result = await api_request(
            config,
            "/v2/project/translations/enqueue",
            body=body,
            timeout=options.get("timeout"),
        )
        return list(result.get("jobData", {}).items())

    result = await process_batches(files, _process_batch, batch_size=100)
    jobs = dict(result["data"])
    target_locales = options.get("target_locales", options.get("targetLocales", []))
    return {
        "jobData": jobs,
        "locales": target_locales,
        "message": f"Successfully enqueued {result['count']} file translation jobs in {result['batch_count']} batch(es)",
    }

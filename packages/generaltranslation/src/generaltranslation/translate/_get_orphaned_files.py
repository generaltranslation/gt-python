"""Get orphaned files endpoint."""

from __future__ import annotations

import asyncio
from typing import Any

from generaltranslation.translate._batch import create_batches
from generaltranslation.translate._request import api_request


async def get_orphaned_files(
    branch_id: str,
    file_ids: list[str],
    options: dict[str, Any],
    config: dict[str, Any],
) -> dict[str, Any]:
    """Get orphaned files for a branch.

    Files that exist on the branch but whose fileIds are not in the provided list.
    """

    async def _make_request(batch_file_ids: list[str]) -> dict[str, Any]:
        return await api_request(
            config,
            "/v2/project/files/orphaned",
            body={"branchId": branch_id, "fileIds": batch_file_ids},
            timeout=options.get("timeout"),
        )

    if not file_ids:
        return await _make_request([])

    batches = create_batches(file_ids, 100)
    batch_results = await asyncio.gather(*(_make_request(batch) for batch in batches))

    if len(batch_results) == 1:
        return batch_results[0]

    # Find intersection of orphaned files across all batches
    orphaned_map: dict[str, dict[str, Any]] = {}
    for orphan in batch_results[0].get("orphanedFiles", []):
        orphaned_map[orphan["fileId"]] = orphan

    for i in range(1, len(batch_results)):
        batch_orphan_ids = {f["fileId"] for f in batch_results[i].get("orphanedFiles", [])}
        for file_id in list(orphaned_map.keys()):
            if file_id not in batch_orphan_ids:
                del orphaned_map[file_id]

    return {"orphanedFiles": list(orphaned_map.values())}

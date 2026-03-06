"""Process file moves endpoint."""

from __future__ import annotations

from typing import Any

from generaltranslation.translate._batch import process_batches
from generaltranslation.translate._request import api_request


async def process_file_moves(
    moves: list[dict[str, Any]],
    options: dict[str, Any],
    config: dict[str, Any],
) -> dict[str, Any]:
    """Process file moves by cloning source files and translations."""
    if not moves:
        return {
            "results": [],
            "summary": {"total": 0, "succeeded": 0, "failed": 0},
        }

    async def _process_batch(batch: list[dict[str, Any]]) -> list[Any]:
        result = await api_request(
            config,
            "/v2/project/files/moves",
            body={"branchId": options.get("branch_id", options.get("branchId")), "moves": batch},
            timeout=options.get("timeout"),
        )
        return result.get("results", [])

    batch_result = await process_batches(moves, _process_batch, batch_size=100)

    succeeded = sum(1 for r in batch_result["data"] if r.get("success"))
    failed = sum(1 for r in batch_result["data"] if not r.get("success"))

    return {
        "results": batch_result["data"],
        "summary": {
            "total": len(moves),
            "succeeded": succeeded,
            "failed": failed,
        },
    }

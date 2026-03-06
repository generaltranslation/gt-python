"""Submit user edit diffs endpoint."""

from __future__ import annotations

from typing import Any

from generaltranslation.translate._batch import process_batches
from generaltranslation.translate._request import api_request


async def submit_user_edit_diffs(
    payload: dict[str, Any],
    config: dict[str, Any],
    options: dict[str, Any] | None = None,
) -> dict[str, bool]:
    """Submit user edit diffs so the service can learn/persist user-intended rules."""
    options = options or {}
    diffs = payload.get("diffs", [])

    async def _process_batch(batch: list[Any]) -> list[Any]:
        await api_request(
            config,
            "/v2/project/files/diffs",
            body={"diffs": batch},
            timeout=options.get("timeout"),
        )
        return [{"success": True}]

    await process_batches(diffs, _process_batch, batch_size=100)
    return {"success": True}

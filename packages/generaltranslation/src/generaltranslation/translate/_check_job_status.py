"""Check job status endpoint."""

from __future__ import annotations

from typing import Any

from generaltranslation.translate._request import api_request


async def check_job_status(
    job_ids: list[str],
    config: dict[str, Any],
    timeout_ms: int | None = None,
) -> list[dict[str, Any]]:
    """Query job statuses for a project."""
    return await api_request(
        config,
        "/v2/project/jobs/info",
        body={"jobIds": job_ids},
        timeout=timeout_ms,
    )

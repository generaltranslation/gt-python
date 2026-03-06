"""Core API request function with retry logic."""

from __future__ import annotations

import asyncio
import json
from typing import Any, Literal

import httpx

from generaltranslation._settings import DEFAULT_BASE_URL, DEFAULT_TIMEOUT
from generaltranslation.errors import (
    ApiError,
    api_error_message,
    translation_request_failed_error,
    translation_timeout_error,
)
from generaltranslation.translate._headers import generate_request_headers

MAX_RETRIES = 3
INITIAL_DELAY_MS = 500

RetryPolicy = Literal["exponential", "linear", "none"]


def _get_retry_delay(policy: RetryPolicy, attempt: int) -> float:
    """Return delay in seconds for the given retry policy and attempt."""
    if policy == "linear":
        return (INITIAL_DELAY_MS * (attempt + 1)) / 1000.0
    elif policy == "exponential":
        return (INITIAL_DELAY_MS * (2**attempt)) / 1000.0
    return 0


async def api_request(
    config: dict[str, Any],
    endpoint: str,
    *,
    body: Any = None,
    timeout: int | None = None,
    method: str = "POST",
    retry_policy: RetryPolicy = "exponential",
) -> Any:
    """Make an API request with automatic retry for 5XX errors.

    Parameters
    ----------
    config : dict
        Must contain ``project_id``; optionally ``base_url`` and ``api_key``.
    endpoint : str
        API endpoint path, e.g. ``/v2/project/jobs/info``.
    body : Any, optional
        JSON-serialisable request body.
    timeout : int, optional
        Timeout in milliseconds.  Falls back to ``DEFAULT_TIMEOUT``.
    method : str
        HTTP method (``"GET"`` or ``"POST"``).
    retry_policy : str
        ``"exponential"``, ``"linear"``, or ``"none"``.

    Returns
    -------
    Any
        Parsed JSON response.

    Raises
    ------
    ApiError
        On 4XX responses.
    Exception
        On network failures after retries are exhausted.
    """
    timeout_ms = timeout if timeout is not None else DEFAULT_TIMEOUT
    timeout_s = timeout_ms / 1000.0
    url = f"{config.get('base_url') or DEFAULT_BASE_URL}{endpoint}"
    max_retries = 0 if retry_policy == "none" else MAX_RETRIES
    headers = generate_request_headers(config)

    async with httpx.AsyncClient(timeout=timeout_s) as client:
        for attempt in range(max_retries + 1):
            try:
                if method == "GET":
                    response = await client.get(url, headers=headers)
                else:
                    response = await client.post(
                        url,
                        headers=headers,
                        content=json.dumps(body) if body is not None else None,
                    )
            except httpx.TimeoutException:
                if attempt < max_retries:
                    await asyncio.sleep(_get_retry_delay(retry_policy, attempt))
                    continue
                raise Exception(translation_timeout_error(timeout_ms))
            except Exception as exc:
                if attempt < max_retries:
                    await asyncio.sleep(_get_retry_delay(retry_policy, attempt))
                    continue
                raise Exception(translation_request_failed_error(str(exc))) from exc

            # Retry on 5XX server errors
            if response.status_code >= 500 and attempt < max_retries:
                await asyncio.sleep(_get_retry_delay(retry_policy, attempt))
                continue

            # Validate response
            if response.status_code >= 400:
                error_msg = "Unknown error"
                try:
                    text = response.text
                    try:
                        error_json = json.loads(text)
                        error_msg = error_json.get("error", text or "Unknown error")
                    except (json.JSONDecodeError, TypeError):
                        error_msg = text or "Unknown error"
                except Exception:
                    pass
                error_message = api_error_message(
                    response.status_code, response.reason_phrase or "", error_msg
                )
                raise ApiError(error_message, response.status_code, error_msg)

            return response.json()

        raise Exception("Max retries exceeded")

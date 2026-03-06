"""Translate and translate_many functions."""

from __future__ import annotations

from typing import Any

from generaltranslation._id import hash_source
from generaltranslation._settings import DEFAULT_RUNTIME_API_URL
from generaltranslation.translate._request import api_request


async def translate_many(
    requests: list[Any] | dict[str, Any],
    global_metadata: dict[str, Any],
    config: dict[str, Any],
    timeout: int | None = None,
) -> list[dict[str, Any]] | dict[str, dict[str, Any]]:
    """Translate multiple entries in a single API request.

    Parameters
    ----------
    requests : list or dict
        If a list, each entry is a string or ``{"source": ..., "metadata": ...}``.
        If a dict, keys are hashes and values are entries.
    global_metadata : dict
        Must contain ``target_locale`` and ``source_locale``.
    config : dict
        Translation request config.
    timeout : int, optional
        Timeout in ms.

    Returns
    -------
    list or dict
        Array of results if input was list, dict if input was dict.
    """
    is_array = isinstance(requests, list)

    hash_order: list[str] | None = [] if is_array else None
    requests_object: dict[str, dict[str, Any]] = {}

    if is_array:
        entries: list[tuple[str | None, Any]] = [(None, r) for r in requests]
    else:
        assert isinstance(requests, dict)
        entries = list(requests.items())

    for key, request in entries:
        if isinstance(request, str):
            normalized: dict[str, Any] = {"source": request}
        else:
            normalized = request

        source = normalized.get("source")
        metadata = normalized.get("metadata") or {}

        if key is not None:
            entry_hash = key
        elif metadata.get("hash"):
            entry_hash = metadata["hash"]
        else:
            entry_hash = hash_source(
                source,
                data_format=metadata.get("dataFormat", metadata.get("data_format", "STRING")),
                context=metadata.get("context"),
                id=metadata.get("id"),
                max_chars=metadata.get("maxChars", metadata.get("max_chars")),
            )

        if hash_order is not None:
            hash_order.append(entry_hash)

        requests_object[entry_hash] = {
            "source": source,
            "metadata": metadata or None,
        }

    # Build request body using camelCase keys to match JS API
    body = {
        "requests": requests_object,
        "targetLocale": global_metadata.get("target_locale", global_metadata.get("targetLocale", "")),
        "sourceLocale": global_metadata.get("source_locale", global_metadata.get("sourceLocale", "")),
        "metadata": global_metadata,
    }

    # Use runtime API URL
    request_config = {
        **config,
        "base_url": config.get("base_url") or DEFAULT_RUNTIME_API_URL,
    }

    response = await api_request(
        request_config,
        "/v2/translate",
        body=body,
        timeout=timeout,
        retry_policy="none",
    )

    if hash_order is not None:
        return [
            response.get(h, {"success": False, "error": "No translation returned", "code": 500}) for h in hash_order
        ]

    return response

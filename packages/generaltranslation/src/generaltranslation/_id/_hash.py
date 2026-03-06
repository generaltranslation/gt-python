import hashlib
import json
from collections.abc import Callable
from typing import Any


def hash_string(s: str) -> str:
    """SHA256 hash, first 16 hex characters."""
    return hashlib.sha256(s.encode()).hexdigest()[:16]


def hash_source(
    source: Any,
    *,
    context: str | None = None,
    id: str | None = None,
    max_chars: int | None = None,
    data_format: str = "STRING",
    hash_function: Callable[[str], str] | None = None,
) -> str:
    """Hash source content with metadata. Only ICU/STRING path (no JSX)."""
    if hash_function is None:
        hash_function = hash_string

    sanitized_data: dict[str, Any] = {"dataFormat": data_format}
    # For non-JSX, source is used as-is (string)
    sanitized_data["source"] = source

    if id:
        sanitized_data["id"] = id
    if context:
        sanitized_data["context"] = context
    if max_chars is not None:
        sanitized_data["maxChars"] = abs(max_chars)

    stringified = json.dumps(sanitized_data, sort_keys=True, separators=(",", ":"))
    return hash_function(stringified)


def hash_template(
    template: dict[str, str],
    hash_function: Callable[[str], str] | None = None,
) -> str:
    """Hash a template dict."""
    if hash_function is None:
        hash_function = hash_string
    stringified = json.dumps(template, sort_keys=True, separators=(",", ":"))
    return hash_function(stringified)

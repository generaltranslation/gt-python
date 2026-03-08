"""Load configuration from a gt.config.json file."""

from __future__ import annotations

import json
from typing import TypedDict

from generaltranslation import CustomMapping

DEFAULT_GT_CONFIG_PATH = "gt.config.json"

_KEY_MAP: dict[str, str] = {
    "defaultLocale": "default_locale",
    "locales": "locales",
    "projectId": "project_id",
    "cacheUrl": "cache_url",
    "runtimeUrl": "runtime_url",
    "customMapping": "custom_mapping",
}


class GTConfig(TypedDict, total=False):
    default_locale: str
    locales: list[str]
    project_id: str
    cache_url: str
    runtime_url: str
    custom_mapping: CustomMapping


def load_gt_config(config_path: str | None = None) -> GTConfig:
    """Read a ``gt.config.json`` file and return the relevant config values.

    Args:
        config_path: Explicit path to the config file.  When *None*, the
            default ``gt.config.json`` (relative to CWD) is tried; if it does
            not exist an empty config is returned.

    Raises:
        FileNotFoundError: If *config_path* was explicitly provided but the
            file does not exist.
        ValueError: If the file contains invalid JSON or the top-level value
            is not an object.
    """
    path = config_path if config_path is not None else DEFAULT_GT_CONFIG_PATH
    explicit = config_path is not None

    try:
        with open(path, encoding="utf-8") as f:
            raw = f.read()
    except FileNotFoundError:
        if explicit:
            raise
        return GTConfig()

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in {path}: {exc}") from exc

    if not isinstance(data, dict):
        raise ValueError(f"Expected a JSON object in {path}, got {type(data).__name__}")

    config = GTConfig()
    for json_key, py_key in _KEY_MAP.items():
        if json_key in data:
            config[py_key] = data[json_key]  # type: ignore[literal-required]

    return config

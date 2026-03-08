"""Tests for gt_i18n.internal._load_gt_config."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from gt_i18n.internal._load_gt_config import load_gt_config


def _write_json(tmp_path: Path, data: Any, filename: str = "gt.config.json") -> str:
    path = tmp_path / filename
    path.write_text(json.dumps(data), encoding="utf-8")
    return str(path)


class TestLoadGTConfig:
    def test_all_fields(self, tmp_path: Path) -> None:
        path = _write_json(
            tmp_path,
            {
                "defaultLocale": "en-US",
                "locales": ["fr", "de"],
                "projectId": "proj-123",
                "cacheUrl": "https://cache.example.com",
                "runtimeUrl": "https://runtime.example.com",
                "customMapping": {"en-US": "English"},
            },
        )
        config = load_gt_config(path)
        assert config["default_locale"] == "en-US"
        assert config["locales"] == ["fr", "de"]
        assert config["project_id"] == "proj-123"
        assert config["cache_url"] == "https://cache.example.com"
        assert config["runtime_url"] == "https://runtime.example.com"
        assert config["custom_mapping"] == {"en-US": "English"}

    def test_custom_mapping(self, tmp_path: Path) -> None:
        path = _write_json(
            tmp_path,
            {
                "customMapping": {
                    "en-US": {"name": "English", "nativeName": "English"},
                    "fr": "French",
                },
            },
        )
        config = load_gt_config(path)
        assert config["custom_mapping"] == {
            "en-US": {"name": "English", "nativeName": "English"},
            "fr": "French",
        }

    def test_explicit_path_missing_raises(self, tmp_path: Path) -> None:
        missing = str(tmp_path / "does_not_exist.json")
        with pytest.raises(FileNotFoundError):
            load_gt_config(missing)

    def test_no_path_default_missing_returns_empty(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.chdir(tmp_path)
        config = load_gt_config()
        assert config == {}

    def test_invalid_json_raises(self, tmp_path: Path) -> None:
        path = tmp_path / "bad.json"
        path.write_text("{not valid json", encoding="utf-8")
        with pytest.raises(ValueError, match="Invalid JSON"):
            load_gt_config(str(path))

    def test_non_object_json_raises(self, tmp_path: Path) -> None:
        path = _write_json(tmp_path, [1, 2, 3], filename="array.json")
        with pytest.raises(ValueError, match="Expected a JSON object"):
            load_gt_config(path)

    def test_unknown_keys_ignored(self, tmp_path: Path) -> None:
        path = _write_json(
            tmp_path,
            {
                "defaultLocale": "en",
                "unknownKey": "should be ignored",
                "anotherUnknown": 42,
            },
        )
        config = load_gt_config(path)
        assert config == {"default_locale": "en"}
        assert "unknownKey" not in config
        assert "anotherUnknown" not in config

    def test_partial_config(self, tmp_path: Path) -> None:
        path = _write_json(
            tmp_path,
            {
                "projectId": "my-project",
                "locales": ["es"],
            },
        )
        config = load_gt_config(path)
        assert config == {
            "project_id": "my-project",
            "locales": ["es"],
        }
        assert "default_locale" not in config

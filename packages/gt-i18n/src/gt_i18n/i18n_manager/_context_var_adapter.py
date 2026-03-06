"""ContextVar-based storage adapter.

Uses Python's ``contextvars.ContextVar`` which works for both threaded
(Flask) and async (FastAPI) contexts. Each request automatically gets
its own context.
"""

from __future__ import annotations

import contextvars

from gt_i18n.i18n_manager._storage_adapter import StorageAdapter

_locale_var: contextvars.ContextVar[str] = contextvars.ContextVar("gt_locale")


class ContextVarStorageAdapter(StorageAdapter):
    """Default storage adapter using ``contextvars.ContextVar``."""

    def get_item(self, key: str) -> str | None:
        if key == "locale":
            return _locale_var.get(None)
        return None

    def set_item(self, key: str, value: str) -> None:
        if key == "locale":
            _locale_var.set(value)

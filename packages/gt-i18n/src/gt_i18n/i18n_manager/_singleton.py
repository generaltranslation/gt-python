"""Module-level singleton for the I18nManager."""

from __future__ import annotations

from gt_i18n.i18n_manager._i18n_manager import I18nManager

_manager: I18nManager | None = None


def get_i18n_manager() -> I18nManager:
    """Return the global I18nManager instance.

    Raises:
        RuntimeError: If ``set_i18n_manager`` has not been called yet.
    """
    if _manager is None:
        raise RuntimeError(
            "I18nManager not initialized. Call initialize_gt() first."
        )
    return _manager


def set_i18n_manager(manager: I18nManager) -> None:
    """Set the global I18nManager instance."""
    global _manager
    _manager = manager

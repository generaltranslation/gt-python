"""I18nManager class, singleton operations, and storage adapters."""

from gt_i18n.i18n_manager._context_var_adapter import ContextVarStorageAdapter
from gt_i18n.i18n_manager._i18n_manager import I18nManager
from gt_i18n.i18n_manager._remote_loader import TranslationsLoader
from gt_i18n.i18n_manager._singleton import get_i18n_manager, set_i18n_manager
from gt_i18n.i18n_manager._storage_adapter import StorageAdapter

__all__ = [
    "ContextVarStorageAdapter",
    "I18nManager",
    "StorageAdapter",
    "TranslationsLoader",
    "get_i18n_manager",
    "set_i18n_manager",
]

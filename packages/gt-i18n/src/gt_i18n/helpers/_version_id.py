from gt_i18n.i18n_manager._singleton import get_i18n_manager


def get_version_id() -> str | None:
    """Get the version ID for the current source, if set."""
    manager = get_i18n_manager()
    return manager.get_version_id()

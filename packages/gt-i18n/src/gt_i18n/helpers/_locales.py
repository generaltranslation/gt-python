from gt_i18n.i18n_manager._singleton import get_i18n_manager

def get_locale() -> str:
    """Get the current locale from the I18nManager."""
    manager = get_i18n_manager()
    return manager.get_locale()

def get_locales() -> list[str]:
    """Get the locales from the I18nManager."""
    manager = get_i18n_manager()
    return manager.get_locales()

def get_default_locale() -> str:
    """Get the default locale from the I18nManager."""
    manager = get_i18n_manager()
    return manager.default_locale
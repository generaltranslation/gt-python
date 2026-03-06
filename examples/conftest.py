"""Shared fixtures for example tests."""

import pytest


@pytest.fixture(autouse=True)
def _reset_singleton():
    """Save and restore the global I18nManager singleton between tests."""
    import gt_i18n.i18n_manager._singleton as mod

    old = mod._manager
    yield
    mod._manager = old

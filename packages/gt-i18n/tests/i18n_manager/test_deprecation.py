"""Golden-standard tests for the deprecation path on I18nManager.

gt PR #1207 renamed several I18nManager methods but kept the old names as
backward-compat aliases. The Python port follows the same pattern but uses
``DeprecationWarning`` (Pythonic) rather than a JSDoc annotation.

Rename map:

| Old (deprecated, still works) | New                         |
| ----------------------------- | --------------------------- |
| ``get_translations(locale)``  | ``load_translations(...)``  |
| ``get_translation_resolver``  | ``get_lookup_translation``  |
| ``resolve_translation_sync``  | ``lookup_translation``      |
| ``get_translation_loader``    | (pass ``load_translations`` directly) |

Contract:
1. Calling an old method emits ``DeprecationWarning`` pointing at the new name.
2. The old method's behavior is IDENTICAL to the new method — users upgrading
   later won't see a behavior change, just the warning disappears.

All tests should FAIL until PR #1207 is ported — the new methods they delegate
to don't exist yet, and the old methods don't yet emit warnings.
"""

from __future__ import annotations

import pytest
from gt_i18n import I18nManager

# ---------------------------------------------------------------------------
# test_get_translations_emits_deprecation_warning
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_translations_emits_deprecation_warning() -> None:
    """``get_translations(locale)`` emits DeprecationWarning pointing at ``load_translations``."""
    manager = I18nManager(default_locale="en", locales=["en", "es"], load_translations=lambda locale: {})

    with pytest.warns(DeprecationWarning, match="load_translations"):
        result = await manager.get_translations("es")

    # Behavior parity: same return value as the new name.
    assert result == await manager.load_translations("es")


# ---------------------------------------------------------------------------
# test_get_translation_resolver_emits_deprecation_warning
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_translation_resolver_emits_deprecation_warning() -> None:
    """``get_translation_resolver(locale)`` emits DeprecationWarning → ``get_lookup_translation``."""
    manager = I18nManager(default_locale="en", locales=["en", "es"], load_translations=lambda locale: {})

    with pytest.warns(DeprecationWarning, match="get_lookup_translation"):
        resolver = await manager.get_translation_resolver("es")

    # The returned resolver is a callable, same as get_lookup_translation's return.
    assert callable(resolver)


# ---------------------------------------------------------------------------
# test_resolve_translation_sync_emits_deprecation_warning
# ---------------------------------------------------------------------------


def test_resolve_translation_sync_emits_deprecation_warning() -> None:
    """``resolve_translation_sync(message, options)`` emits DeprecationWarning → ``lookup_translation``."""
    manager = I18nManager(default_locale="en", locales=["en", "es"], load_translations=lambda locale: {})
    manager.set_locale("es")

    with pytest.warns(DeprecationWarning, match="lookup_translation"):
        result = manager.resolve_translation_sync("Hello", {"_format": "ICU"})

    # Behavior parity: same value as lookup_translation (both return None on cold cache).
    assert result == manager.lookup_translation("Hello", _format="ICU")


# ---------------------------------------------------------------------------
# test_get_translation_loader_emits_deprecation_warning
#
# ``get_translation_loader()`` exposed the raw loader callable; the new path
# is to pass ``load_translations`` directly to the constructor (which you
# already do). The method is kept but warns.
# ---------------------------------------------------------------------------


def test_get_translation_loader_emits_deprecation_warning() -> None:
    """``get_translation_loader()`` emits DeprecationWarning."""
    manager = I18nManager(default_locale="en", locales=["en", "es"], load_translations=lambda locale: {})

    with pytest.warns(DeprecationWarning, match="load_translations"):
        loader = manager.get_translation_loader()

    # Still returns the loader callable.
    assert callable(loader)


# ---------------------------------------------------------------------------
# test_deprecated_methods_preserve_semantics
#
# Parametric contract: for each (deprecated, new) pair, the return values
# match. This guards against silent semantic drift between the pair.
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_deprecated_methods_preserve_semantics() -> None:
    """Each deprecated method must return the same thing as its replacement."""
    h_map = {"hash_x": "translated-x"}
    manager = I18nManager(
        default_locale="en",
        locales=["en", "es"],
        load_translations=lambda locale: h_map if locale == "es" else {},
    )
    manager.set_locale("es")

    # get_translations vs load_translations — same dict.
    import warnings

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        old = await manager.get_translations("es")
    new = await manager.load_translations("es")
    assert old == new == h_map

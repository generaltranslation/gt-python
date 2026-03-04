"""Low-level locale utilities built on top of Babel's CLDR data."""

from generaltranslation.locales.utils._minimize import minimize_locale

__all__ = [
    "minimize_locale",
]

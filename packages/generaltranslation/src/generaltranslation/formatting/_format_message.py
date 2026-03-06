"""ICU MessageFormat formatting.

Delegates to ``generaltranslation-intl-messageformat`` for parsing and
locale-aware interpolation (plural, select, selectordinal).
"""

from __future__ import annotations

from generaltranslation_intl_messageformat import IntlMessageFormat

from generaltranslation.formatting._helpers import _resolve_babel_locale


def format_message(
    message: str,
    locales: str | list[str] | None = None,
    variables: dict | None = None,
) -> str:
    """Format an ICU MessageFormat string.

    Args:
        message: The ICU message pattern (e.g.
            ``"{count, plural, one {# item} other {# items}}"``).
        locales: BCP 47 locale tag(s) for plural rule selection.
            Defaults to ``"en"``.
        variables: Variable values to substitute.

    Returns:
        The formatted message string.
    """
    locale = _resolve_babel_locale(locales)
    mf = IntlMessageFormat(message, str(locale))
    return mf.format(variables)

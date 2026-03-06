"""Currency formatting using Babel.

Ports ``_formatCurrency`` from the JS core library.
"""

from __future__ import annotations

from babel.numbers import format_currency as babel_format_currency

from generaltranslation.formatting._helpers import _resolve_babel_locale


# Map JS currencyDisplay values to Babel format_type
_DISPLAY_MAP = {
    "symbol": None,  # Babel default
    "narrowSymbol": None,  # Babel doesn't distinguish; use default
    "name": "name",
}


def format_currency(
    value: int | float,
    currency: str = "USD",
    locales: str | list[str] | None = None,
    options: dict | None = None,
) -> str:
    """Format a currency value according to the given locale and options.

    Args:
        value: The currency amount.
        currency: ISO 4217 currency code (e.g. ``"USD"``, ``"EUR"``).
        locales: BCP 47 locale tag(s). Defaults to ``"en"``.
        options: Formatting options (snake_case).

            - ``currency_display``: ``"symbol"`` (default), ``"name"``,
              ``"code"``, ``"narrowSymbol"``.
            - ``currency_sign``: ``"standard"`` (default), ``"accounting"``.

    Returns:
        The formatted currency string.
    """
    if options is None:
        options = {}

    locale = _resolve_babel_locale(locales)

    currency_display = options.get("currency_display", "symbol")
    currency_sign = options.get("currency_sign", "standard")

    # Determine Babel format_type
    format_type = _DISPLAY_MAP.get(currency_display)

    # Accounting format for negative values
    if currency_sign == "accounting":
        format_type = "accounting"

    # "code" display: format with symbol then replace symbol with currency code
    if currency_display == "code":
        formatted = babel_format_currency(
            number=value,
            currency=currency.upper(),
            locale=locale,
            format_type="standard",
        )
        # Get the currency symbol to replace it with the code
        from babel.numbers import get_currency_symbol

        symbol = get_currency_symbol(currency.upper(), locale=locale)
        return formatted.replace(symbol, currency.upper())

    kwargs: dict = {
        "number": value,
        "currency": currency.upper(),
        "locale": locale,
    }
    if format_type is not None:
        kwargs["format_type"] = format_type

    return babel_format_currency(**kwargs)

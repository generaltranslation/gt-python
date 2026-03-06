"""Flag emoji lookup for BCP 47 locales.

Ports ``getLocaleEmoji.ts`` from the JS core library.
Maps region codes to Unicode flag emoji sequences, with hard-coded
exceptions for languages that do not map cleanly to a single country.
"""

from __future__ import annotations

from babel import Locale
from babel.core import get_global

from generaltranslation.locales._types import CustomMapping

# ---------------------------------------------------------------------------
# Default / fallback emoji
# ---------------------------------------------------------------------------

EUROPE_AFRICA_GLOBE = "\U0001f30d"  # 🌍
ASIA_AUSTRALIA_GLOBE = "\U0001f30f"  # 🌏
DEFAULT_EMOJI = EUROPE_AFRICA_GLOBE

# ---------------------------------------------------------------------------
# Language -> emoji exceptions
# ---------------------------------------------------------------------------

EMOJI_EXCEPTIONS: dict[str, str] = {
    "ca": EUROPE_AFRICA_GLOBE,
    "eu": EUROPE_AFRICA_GLOBE,
    "ku": EUROPE_AFRICA_GLOBE,
    "bo": ASIA_AUSTRALIA_GLOBE,
    "ug": ASIA_AUSTRALIA_GLOBE,
    "gd": ("\U0001f3f4\U000e0067\U000e0062\U000e0073\U000e0063\U000e0074\U000e007f"),
    "cy": ("\U0001f3f4\U000e0067\U000e0062\U000e0077\U000e006c\U000e0073\U000e007f"),
    "gv": "\U0001f1ee\U0001f1f2",
    "grc": "\U0001f3fa",
}

# ---------------------------------------------------------------------------
# Region code -> flag emoji (ISO 3166-1 alpha-2 + UN M.49 "419")
# ---------------------------------------------------------------------------

EMOJIS: dict[str, str] = {
    "AF": "\U0001f1e6\U0001f1eb",
    "AX": "\U0001f1e6\U0001f1fd",
    "AL": "\U0001f1e6\U0001f1f1",
    "DZ": "\U0001f1e9\U0001f1ff",
    "AS": "\U0001f1e6\U0001f1f8",
    "AD": "\U0001f1e6\U0001f1e9",
    "AO": "\U0001f1e6\U0001f1f4",
    "AI": "\U0001f1e6\U0001f1ee",
    "AQ": "\U0001f1e6\U0001f1f6",
    "AG": "\U0001f1e6\U0001f1ec",
    "AR": "\U0001f1e6\U0001f1f7",
    "AM": "\U0001f1e6\U0001f1f2",
    "AW": "\U0001f1e6\U0001f1fc",
    "AU": "\U0001f1e6\U0001f1fa",
    "AT": "\U0001f1e6\U0001f1f9",
    "AZ": "\U0001f1e6\U0001f1ff",
    "BS": "\U0001f1e7\U0001f1f8",
    "BH": "\U0001f1e7\U0001f1ed",
    "BD": "\U0001f1e7\U0001f1e9",
    "BB": "\U0001f1e7\U0001f1e7",
    "BY": "\U0001f1e7\U0001f1fe",
    "BE": "\U0001f1e7\U0001f1ea",
    "BZ": "\U0001f1e7\U0001f1ff",
    "BJ": "\U0001f1e7\U0001f1ef",
    "BM": "\U0001f1e7\U0001f1f2",
    "BT": "\U0001f1e7\U0001f1f9",
    "BO": "\U0001f1e7\U0001f1f4",
    "BQ": "\U0001f1e7\U0001f1f6",
    "BA": "\U0001f1e7\U0001f1e6",
    "BW": "\U0001f1e7\U0001f1fc",
    "BV": "\U0001f1e7\U0001f1fb",
    "BR": "\U0001f1e7\U0001f1f7",
    "IO": "\U0001f1ee\U0001f1f4",
    "BN": "\U0001f1e7\U0001f1f3",
    "BG": "\U0001f1e7\U0001f1ec",
    "BF": "\U0001f1e7\U0001f1eb",
    "BI": "\U0001f1e7\U0001f1ee",
    "CV": "\U0001f1e8\U0001f1fb",
    "KH": "\U0001f1f0\U0001f1ed",
    "CM": "\U0001f1e8\U0001f1f2",
    "CA": "\U0001f1e8\U0001f1e6",
    "KY": "\U0001f1f0\U0001f1fe",
    "CF": "\U0001f1e8\U0001f1eb",
    "TD": "\U0001f1f9\U0001f1e9",
    "CL": "\U0001f1e8\U0001f1f1",
    "CN": "\U0001f1e8\U0001f1f3",
    "CX": "\U0001f1e8\U0001f1fd",
    "CC": "\U0001f1e8\U0001f1e8",
    "CO": "\U0001f1e8\U0001f1f4",
    "KM": "\U0001f1f0\U0001f1f2",
    "CD": "\U0001f1e8\U0001f1e9",
    "CG": "\U0001f1e8\U0001f1ec",
    "CK": "\U0001f1e8\U0001f1f0",
    "CR": "\U0001f1e8\U0001f1f7",
    "CI": "\U0001f1e8\U0001f1ee",
    "HR": "\U0001f1ed\U0001f1f7",
    "CU": "\U0001f1e8\U0001f1fa",
    "CW": "\U0001f1e8\U0001f1fc",
    "CY": "\U0001f1e8\U0001f1fe",
    "CZ": "\U0001f1e8\U0001f1ff",
    "DK": "\U0001f1e9\U0001f1f0",
    "DJ": "\U0001f1e9\U0001f1ef",
    "DM": "\U0001f1e9\U0001f1f2",
    "DO": "\U0001f1e9\U0001f1f4",
    "EC": "\U0001f1ea\U0001f1e8",
    "EG": "\U0001f1ea\U0001f1ec",
    "SV": "\U0001f1f8\U0001f1fb",
    "GQ": "\U0001f1ec\U0001f1f6",
    "ER": "\U0001f1ea\U0001f1f7",
    "EE": "\U0001f1ea\U0001f1ea",
    "SZ": "\U0001f1f8\U0001f1ff",
    "ET": "\U0001f1ea\U0001f1f9",
    "FK": "\U0001f1eb\U0001f1f0",
    "FO": "\U0001f1eb\U0001f1f4",
    "FJ": "\U0001f1eb\U0001f1ef",
    "FI": "\U0001f1eb\U0001f1ee",
    "FR": "\U0001f1eb\U0001f1f7",
    "GF": "\U0001f1ec\U0001f1eb",
    "PF": "\U0001f1f5\U0001f1eb",
    "TF": "\U0001f1f9\U0001f1eb",
    "GA": "\U0001f1ec\U0001f1e6",
    "GM": "\U0001f1ec\U0001f1f2",
    "GE": "\U0001f1ec\U0001f1ea",
    "DE": "\U0001f1e9\U0001f1ea",
    "GH": "\U0001f1ec\U0001f1ed",
    "GI": "\U0001f1ec\U0001f1ee",
    "GR": "\U0001f1ec\U0001f1f7",
    "GL": "\U0001f1ec\U0001f1f1",
    "GD": "\U0001f1ec\U0001f1e9",
    "GP": "\U0001f1ec\U0001f1f5",
    "GU": "\U0001f1ec\U0001f1fa",
    "GT": "\U0001f1ec\U0001f1f9",
    "GG": "\U0001f1ec\U0001f1ec",
    "GN": "\U0001f1ec\U0001f1f3",
    "GW": "\U0001f1ec\U0001f1fc",
    "GY": "\U0001f1ec\U0001f1fe",
    "HT": "\U0001f1ed\U0001f1f9",
    "HM": "\U0001f1ed\U0001f1f2",
    "VA": "\U0001f1fb\U0001f1e6",
    "HN": "\U0001f1ed\U0001f1f3",
    "HK": "\U0001f1ed\U0001f1f0",
    "HU": "\U0001f1ed\U0001f1fa",
    "IS": "\U0001f1ee\U0001f1f8",
    "IN": "\U0001f1ee\U0001f1f3",
    "ID": "\U0001f1ee\U0001f1e9",
    "IR": "\U0001f1ee\U0001f1f7",
    "IQ": "\U0001f1ee\U0001f1f6",
    "IE": "\U0001f1ee\U0001f1ea",
    "IM": "\U0001f1ee\U0001f1f2",
    "IL": "\U0001f1ee\U0001f1f1",
    "IT": "\U0001f1ee\U0001f1f9",
    "JM": "\U0001f1ef\U0001f1f2",
    "JP": "\U0001f1ef\U0001f1f5",
    "JE": "\U0001f1ef\U0001f1ea",
    "JO": "\U0001f1ef\U0001f1f4",
    "KZ": "\U0001f1f0\U0001f1ff",
    "KE": "\U0001f1f0\U0001f1ea",
    "KI": "\U0001f1f0\U0001f1ee",
    "KP": "\U0001f1f0\U0001f1f5",
    "KR": "\U0001f1f0\U0001f1f7",
    "KW": "\U0001f1f0\U0001f1fc",
    "KG": "\U0001f1f0\U0001f1ec",
    "LA": "\U0001f1f1\U0001f1e6",
    "LV": "\U0001f1f1\U0001f1fb",
    "LB": "\U0001f1f1\U0001f1e7",
    "LS": "\U0001f1f1\U0001f1f8",
    "LR": "\U0001f1f1\U0001f1f7",
    "LY": "\U0001f1f1\U0001f1fe",
    "LI": "\U0001f1f1\U0001f1ee",
    "LT": "\U0001f1f1\U0001f1f9",
    "LU": "\U0001f1f1\U0001f1fa",
    "MO": "\U0001f1f2\U0001f1f4",
    "MG": "\U0001f1f2\U0001f1ec",
    "MW": "\U0001f1f2\U0001f1fc",
    "MY": "\U0001f1f2\U0001f1fe",
    "MV": "\U0001f1f2\U0001f1fb",
    "ML": "\U0001f1f2\U0001f1f1",
    "MT": "\U0001f1f2\U0001f1f9",
    "MH": "\U0001f1f2\U0001f1ed",
    "MQ": "\U0001f1f2\U0001f1f6",
    "MR": "\U0001f1f2\U0001f1f7",
    "MU": "\U0001f1f2\U0001f1fa",
    "YT": "\U0001f1fe\U0001f1f9",
    "MX": "\U0001f1f2\U0001f1fd",
    "FM": "\U0001f1eb\U0001f1f2",
    "MD": "\U0001f1f2\U0001f1e9",
    "MC": "\U0001f1f2\U0001f1e8",
    "MN": "\U0001f1f2\U0001f1f3",
    "ME": "\U0001f1f2\U0001f1ea",
    "MS": "\U0001f1f2\U0001f1f8",
    "MA": "\U0001f1f2\U0001f1e6",
    "MZ": "\U0001f1f2\U0001f1ff",
    "MM": "\U0001f1f2\U0001f1f2",
    "NA": "\U0001f1f3\U0001f1e6",
    "NR": "\U0001f1f3\U0001f1f7",
    "NP": "\U0001f1f3\U0001f1f5",
    "NL": "\U0001f1f3\U0001f1f1",
    "NC": "\U0001f1f3\U0001f1e8",
    "NZ": "\U0001f1f3\U0001f1ff",
    "NI": "\U0001f1f3\U0001f1ee",
    "NE": "\U0001f1f3\U0001f1ea",
    "NG": "\U0001f1f3\U0001f1ec",
    "NU": "\U0001f1f3\U0001f1fa",
    "NF": "\U0001f1f3\U0001f1eb",
    "MK": "\U0001f1f2\U0001f1f0",
    "MP": "\U0001f1f2\U0001f1f5",
    "NO": "\U0001f1f3\U0001f1f4",
    "OM": "\U0001f1f4\U0001f1f2",
    "PK": "\U0001f1f5\U0001f1f0",
    "PW": "\U0001f1f5\U0001f1fc",
    "PS": "\U0001f1f5\U0001f1f8",
    "PA": "\U0001f1f5\U0001f1e6",
    "PG": "\U0001f1f5\U0001f1ec",
    "PY": "\U0001f1f5\U0001f1fe",
    "PE": "\U0001f1f5\U0001f1ea",
    "PH": "\U0001f1f5\U0001f1ed",
    "PN": "\U0001f1f5\U0001f1f3",
    "PL": "\U0001f1f5\U0001f1f1",
    "PT": "\U0001f1f5\U0001f1f9",
    "PR": "\U0001f1f5\U0001f1f7",
    "QA": "\U0001f1f6\U0001f1e6",
    "RE": "\U0001f1f7\U0001f1ea",
    "RO": "\U0001f1f7\U0001f1f4",
    "RU": "\U0001f1f7\U0001f1fa",
    "RW": "\U0001f1f7\U0001f1fc",
    "BL": "\U0001f1e7\U0001f1f1",
    "SH": "\U0001f1f8\U0001f1ed",
    "KN": "\U0001f1f0\U0001f1f3",
    "LC": "\U0001f1f1\U0001f1e8",
    "MF": "\U0001f1f2\U0001f1eb",
    "PM": "\U0001f1f5\U0001f1f2",
    "VC": "\U0001f1fb\U0001f1e8",
    "WS": "\U0001f1fc\U0001f1f8",
    "SM": "\U0001f1f8\U0001f1f2",
    "ST": "\U0001f1f8\U0001f1f9",
    "SA": "\U0001f1f8\U0001f1e6",
    "SN": "\U0001f1f8\U0001f1f3",
    "RS": "\U0001f1f7\U0001f1f8",
    "SC": "\U0001f1f8\U0001f1e8",
    "SL": "\U0001f1f8\U0001f1f1",
    "SG": "\U0001f1f8\U0001f1ec",
    "SX": "\U0001f1f8\U0001f1fd",
    "SK": "\U0001f1f8\U0001f1f0",
    "SI": "\U0001f1f8\U0001f1ee",
    "SB": "\U0001f1f8\U0001f1e7",
    "SO": "\U0001f1f8\U0001f1f4",
    "ZA": "\U0001f1ff\U0001f1e6",
    "GS": "\U0001f1ec\U0001f1f8",
    "SS": "\U0001f1f8\U0001f1f8",
    "ES": "\U0001f1ea\U0001f1f8",
    "LK": "\U0001f1f1\U0001f1f0",
    "SD": "\U0001f1f8\U0001f1e9",
    "SR": "\U0001f1f8\U0001f1f7",
    "SJ": "\U0001f1f8\U0001f1ef",
    "SE": "\U0001f1f8\U0001f1ea",
    "CH": "\U0001f1e8\U0001f1ed",
    "SY": "\U0001f1f8\U0001f1fe",
    "TW": "\U0001f1f9\U0001f1fc",
    "TJ": "\U0001f1f9\U0001f1ef",
    "TZ": "\U0001f1f9\U0001f1ff",
    "TH": "\U0001f1f9\U0001f1ed",
    "TL": "\U0001f1f9\U0001f1f1",
    "TG": "\U0001f1f9\U0001f1ec",
    "TK": "\U0001f1f9\U0001f1f0",
    "TO": "\U0001f1f9\U0001f1f4",
    "TT": "\U0001f1f9\U0001f1f9",
    "TN": "\U0001f1f9\U0001f1f3",
    "TR": "\U0001f1f9\U0001f1f7",
    "TM": "\U0001f1f9\U0001f1f2",
    "TC": "\U0001f1f9\U0001f1e8",
    "TV": "\U0001f1f9\U0001f1fb",
    "UG": "\U0001f1fa\U0001f1ec",
    "UA": "\U0001f1fa\U0001f1e6",
    "AE": "\U0001f1e6\U0001f1ea",
    "GB": "\U0001f1ec\U0001f1e7",
    "US": "\U0001f1fa\U0001f1f8",
    "UM": "\U0001f1fa\U0001f1f2",
    "UY": "\U0001f1fa\U0001f1fe",
    "UZ": "\U0001f1fa\U0001f1ff",
    "VU": "\U0001f1fb\U0001f1fa",
    "VE": "\U0001f1fb\U0001f1ea",
    "VN": "\U0001f1fb\U0001f1f3",
    "VG": "\U0001f1fb\U0001f1ec",
    "VI": "\U0001f1fb\U0001f1ee",
    "WF": "\U0001f1fc\U0001f1eb",
    "EH": "\U0001f1ea\U0001f1ed",
    "YE": "\U0001f1fe\U0001f1ea",
    "ZM": "\U0001f1ff\U0001f1f2",
    "ZW": "\U0001f1ff\U0001f1fc",
    "EU": "\U0001f1ea\U0001f1fa",
    "419": "\U0001f30e",  # 🌎 Latin America
}

# CLDR likely subtags for territory inference
_likely_subtags: dict[str, str] = get_global("likely_subtags")


def get_locale_emoji(
    locale: str,
    custom_mapping: CustomMapping | None = None,
) -> str:
    """Return a flag emoji for the given BCP 47 *locale*."""
    from generaltranslation.locales._custom_locale_mapping import (
        get_custom_property,
        should_use_canonical_locale,
    )
    from generaltranslation.locales._is_valid_locale import standardize_locale

    # Check custom mapping for emoji override
    if custom_mapping is not None:
        custom_emoji = get_custom_property(custom_mapping, locale, "emoji")
        if custom_emoji:
            return custom_emoji

        if should_use_canonical_locale(locale, custom_mapping):
            entry = custom_mapping[locale]
            if isinstance(entry, dict):
                canonical = entry["code"]
                custom_emoji = get_custom_property(custom_mapping, canonical, "emoji")
                if custom_emoji:
                    return custom_emoji

        std = standardize_locale(locale)
        if std != locale:
            custom_emoji = get_custom_property(custom_mapping, std, "emoji")
            if custom_emoji:
                return custom_emoji

    # Try to parse with Babel
    try:
        parsed = Locale.parse(locale, sep="-")
        language = parsed.language
        territory = parsed.territory
        script = parsed.script
    except Exception:
        # Can't parse - check exceptions for raw language code
        lang = locale.split("-")[0].lower()
        if lang in EMOJI_EXCEPTIONS:
            return EMOJI_EXCEPTIONS[lang]
        return DEFAULT_EMOJI

    # Check explicit region
    if territory:
        emoji = EMOJIS.get(territory)
        if emoji:
            return emoji

    # Check language exceptions BEFORE maximize (these override inferred regions)
    if language in EMOJI_EXCEPTIONS:
        return EMOJI_EXCEPTIONS[language]

    # Maximize using likely subtags to infer region
    candidates = []
    if script:
        candidates.append(f"{language}_{script}")
    candidates.append(language)

    for candidate in candidates:
        if candidate in _likely_subtags:
            parts = _likely_subtags[candidate].split("_")
            if len(parts) >= 3:
                inferred_territory = parts[2]
                emoji = EMOJIS.get(inferred_territory)
                if emoji:
                    return emoji
            break

    return DEFAULT_EMOJI

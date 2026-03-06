"""Retrieve comprehensive metadata for a BCP 47 locale.

Ports ``getLocaleProperties.ts`` from the JS core library.
Uses ``babel`` for parsing, maximisation/minimisation, and display
name resolution instead of the browser ``Intl`` APIs.
"""

from __future__ import annotations

from babel import Locale
from babel.core import get_global

from generaltranslation.locales._types import CustomMapping, LocaleProperties

_likely_subtags: dict[str, str] = dict(get_global("likely_subtags"))


def _create_custom_locale_properties(
    locale_variants: list[str],
    custom_mapping: CustomMapping | None = None,
) -> dict[str, str] | None:
    """Merge custom property overrides from the mapping."""
    if custom_mapping is None:
        return None

    result: dict[str, str] = {}
    for variant in reversed(locale_variants):
        entry = custom_mapping.get(variant)
        if entry is not None:
            if isinstance(entry, str):
                result["name"] = entry
            elif isinstance(entry, dict):
                result.update(entry)

    return result if result else None


def _apply_cjk_formatting(text: str, display_lang: str) -> str:
    """Apply CJK-specific formatting to display names."""
    if display_lang == "zh":
        text = text.replace(" (", "\uff08").replace(")", "\uff09")
        text = text.replace(", ", "\uff0c")
    elif display_lang == "ja":
        text = text.replace(", ", "\u3001")
    return text


def _get_compound_name(
    locale_tag: str,
    display_locale: Locale,
    parsed: Locale,
) -> str:
    """Get compound CLDR name (e.g. 'Austrian German') if available,
    otherwise fall back to get_display_name."""
    underscore_tag = parsed.language
    if parsed.script:
        underscore_tag += f"_{parsed.script}"
    if parsed.territory:
        underscore_tag += f"_{parsed.territory}"

    compound = display_locale.languages.get(underscore_tag)
    if compound:
        return compound

    name = parsed.get_display_name(str(display_locale))
    if name:
        name = _apply_cjk_formatting(name, display_locale.language)
        return name
    return locale_tag


def _build_component_name(
    language: str,
    script: str | None,
    territory: str | None,
    display_locale: Locale,
) -> str:
    """Build 'Language (Script, Territory)' name with locale-specific formatting."""
    lang_name = display_locale.languages.get(language, language)
    details = []
    if script:
        details.append(display_locale.scripts.get(script, script))
    if territory:
        details.append(display_locale.territories.get(territory, territory))

    if not details:
        return lang_name

    joined = ", ".join(details)
    result = f"{lang_name} ({joined})"

    # Apply locale-specific formatting for CJK
    display_lang = display_locale.language
    if display_lang == "zh":
        # Chinese: fullwidth brackets and comma
        fw_comma = "\uff0c"
        result = f"{lang_name}\uff08{fw_comma.join(details)}\uff09"
    elif display_lang == "ja":
        # Japanese: ASCII parens, ideographic comma
        jp_comma = "\u3001"
        result = f"{lang_name} ({jp_comma.join(details)})"

    return result


def get_locale_properties(
    locale: str,
    default_locale: str | None = "en",
    custom_mapping: CustomMapping | None = None,
) -> LocaleProperties:
    """Return a :class:`LocaleProperties` for *locale*."""
    from generaltranslation.locales._custom_locale_mapping import (
        should_use_canonical_locale,
    )
    from generaltranslation.locales._get_locale_emoji import get_locale_emoji
    from generaltranslation.locales._is_valid_locale import standardize_locale
    from generaltranslation.locales.utils import minimize_locale

    original_locale = locale

    # Resolve canonical if needed
    canonical_code = locale
    if custom_mapping is not None and should_use_canonical_locale(locale, custom_mapping):
        entry = custom_mapping[locale]
        if isinstance(entry, dict) and "code" in entry:
            canonical_code = entry["code"]

    std_locale = standardize_locale(canonical_code)

    try:
        parsed = Locale.parse(std_locale, sep="-")
    except Exception:
        return LocaleProperties(
            code=original_locale,
            name=original_locale,
            native_name=original_locale,
        )

    # Get display locale
    try:
        display_locale = Locale.parse(default_locale, sep="-")
    except Exception:
        display_locale = Locale("en")

    # Components from parsed
    language_code = parsed.language
    input_region = parsed.territory or ""
    input_script = parsed.script or ""

    # Maximize using likely subtags
    max_script = input_script
    max_territory = input_region

    candidates = []
    if input_script and input_region:
        candidates.append(f"{language_code}_{input_script}_{input_region}")
    if input_script:
        candidates.append(f"{language_code}_{input_script}")
    if input_region:
        candidates.append(f"{language_code}_{input_region}")
    candidates.append(language_code)

    for candidate in candidates:
        if candidate in _likely_subtags:
            parts = _likely_subtags[candidate].split("_")
            if not max_script and len(parts) > 1:
                max_script = parts[1]
            if not max_territory and len(parts) > 2:
                max_territory = parts[2]
            break

    # Fill remaining from base language
    if not max_script or not max_territory:
        if language_code in _likely_subtags:
            parts = _likely_subtags[language_code].split("_")
            if not max_script and len(parts) > 1:
                max_script = parts[1]
            if not max_territory and len(parts) > 2:
                max_territory = parts[2]

    # Build maximized/minimized codes
    maximized_parts = [language_code]
    if max_script:
        maximized_parts.append(max_script)
    if max_territory:
        maximized_parts.append(max_territory)
    maximized_code = "-".join(maximized_parts)

    minimized_code = minimize_locale(std_locale)

    # Parse minimized for display name lookup
    try:
        minimized_parsed = Locale.parse(minimized_code, sep="-")
    except Exception:
        minimized_parsed = parsed

    # Use maximized region/script as defaults for properties
    region_code = input_region or max_territory
    script_code = input_script or max_script

    # --- Display names in default_locale ---
    name = _get_compound_name(std_locale, display_locale, parsed)
    language_name = display_locale.languages.get(language_code, language_code)
    region_name = display_locale.territories.get(region_code, "") if region_code else ""
    script_name = display_locale.scripts.get(script_code, "") if script_code else ""

    # Maximized name: always use component form
    maximized_name = _build_component_name(language_code, max_script, max_territory, display_locale)

    # Minimized name: use compound lookup
    minimized_name = _get_compound_name(minimized_code, display_locale, minimized_parsed)

    # --- Native display names ---
    # Include script in native locale for correct display (e.g. sr-Latn vs sr-Cyrl)
    native_locale_id = language_code
    if parsed.script:
        native_locale_id += f"_{parsed.script}"
    try:
        native_locale = Locale.parse(native_locale_id)
    except Exception:
        try:
            native_locale = Locale.parse(language_code)
        except Exception:
            native_locale = parsed

    native_name = _get_compound_name(std_locale, native_locale, parsed)
    native_language_name = native_locale.languages.get(language_code, language_code)
    native_region_name = native_locale.territories.get(region_code, "") if region_code else ""
    native_script_name = native_locale.scripts.get(script_code, "") if script_code else ""
    native_maximized_name = _build_component_name(language_code, max_script, max_territory, native_locale)
    native_minimized_name = _get_compound_name(minimized_code, native_locale, minimized_parsed)

    # Name with region code
    if parsed.territory:
        name_with_region_code = f"{language_name} ({parsed.territory})"
        native_name_with_region_code = f"{native_language_name} ({parsed.territory})"
    else:
        name_with_region_code = language_name
        native_name_with_region_code = native_language_name

    emoji = get_locale_emoji(std_locale, custom_mapping)

    props = LocaleProperties(
        code=original_locale,
        name=name,
        native_name=native_name,
        language_code=language_code,
        language_name=language_name,
        native_language_name=native_language_name,
        name_with_region_code=name_with_region_code,
        native_name_with_region_code=native_name_with_region_code,
        region_code=region_code,
        region_name=region_name,
        native_region_name=native_region_name,
        script_code=script_code,
        script_name=script_name,
        native_script_name=native_script_name,
        maximized_code=maximized_code,
        maximized_name=maximized_name,
        native_maximized_name=native_maximized_name,
        minimized_code=minimized_code,
        minimized_name=minimized_name,
        native_minimized_name=native_minimized_name,
        emoji=emoji,
    )

    # Apply custom overrides
    if custom_mapping is not None:
        locale_variants = [original_locale, std_locale, language_code]
        custom_props = _create_custom_locale_properties(locale_variants, custom_mapping)
        if custom_props:
            key_map = {
                "name": "name",
                "nativeName": "native_name",
                "emoji": "emoji",
                "languageCode": "language_code",
                "languageName": "language_name",
                "regionCode": "region_code",
                "regionName": "region_name",
                "scriptCode": "script_code",
                "scriptName": "script_name",
            }
            for custom_key, value in custom_props.items():
                field = key_map.get(custom_key, custom_key)
                if hasattr(props, field) and field != "code":
                    setattr(props, field, value)

    return props

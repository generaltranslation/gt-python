"""Language-level locale comparison.

Ports ``isSameLanguage.ts`` from the JS core library.
Compares only the language subtag, ignoring region and script.
"""

from __future__ import annotations

from babel import Locale


def is_same_language(*locales: str | list[str]) -> bool:
    """Return ``True`` if all given locales share the same base language.

    Extracts the language component from each BCP 47 tag (ignoring
    region and script) and checks that they are all identical.

    Accepts individual strings or lists of strings (which are flattened).

    Args:
        *locales: Two or more BCP 47 locale tags (or lists thereof).

    Returns:
        ``True`` if every locale has the same language code,
        ``False`` otherwise (including on parse errors).

    Examples:
        >>> is_same_language("en-US", "en-GB")
        True
        >>> is_same_language("en-US", "fr-FR")
        False
        >>> is_same_language("zh-Hans", "zh-Hant")
        True
    """
    # Flatten args
    flat: list[str] = []
    for arg in locales:
        if isinstance(arg, list):
            flat.extend(arg)
        else:
            flat.append(arg)

    if len(flat) < 2:
        return False

    try:
        languages: list[str] = []
        for loc in flat:
            parsed = Locale.parse(loc, sep="-")
            languages.append(parsed.language)
        return len(set(languages)) == 1
    except Exception:
        return False

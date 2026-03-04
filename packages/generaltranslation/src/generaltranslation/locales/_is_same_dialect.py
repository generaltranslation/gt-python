"""Dialect-level locale comparison.

Ports ``isSameDialect.ts`` from the JS core library.
Two locales are the "same dialect" when their language matches and
neither has a region or script that conflicts with the other.
"""

from __future__ import annotations

from babel import Locale


def is_same_dialect(*locales: str | list[str]) -> bool:
    """Return ``True`` if all given locales are the same dialect.

    Two locales are considered the same dialect when:

    - Their language codes are identical.
    - If both specify a region, the regions match.
    - If both specify a script, the scripts match.

    An unspecified (empty) region or script is treated as compatible
    with any value, so ``"en-US"`` and ``"en"`` are the same dialect,
    but ``"en-US"`` and ``"en-GB"`` are not.

    All pairwise combinations are checked (not just consecutive pairs).

    Args:
        *locales: Two or more BCP 47 locale tags (or lists thereof).

    Returns:
        ``True`` if every pair of locales is the same dialect,
        ``False`` otherwise (including on parse errors).

    Examples:
        >>> is_same_dialect("en-US", "en")
        True
        >>> is_same_dialect("en-US", "en-GB")
        False
        >>> is_same_dialect("zh-Hans", "zh-Hant")
        False
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
        from generaltranslation.locales._is_valid_locale import standardize_locale

        parsed_list = []
        for loc in flat:
            std = standardize_locale(loc)
            parsed = Locale.parse(std, sep="-")
            parsed_list.append(parsed)

        # Check all pairs
        for i in range(len(parsed_list)):
            for j in range(i + 1, len(parsed_list)):
                a = parsed_list[i]
                b = parsed_list[j]

                if a.language != b.language:
                    return False

                if a.territory and b.territory and a.territory != b.territory:
                    return False

                if a.script and b.script and a.script != b.script:
                    return False

        return True
    except Exception:
        return False

from typing import Any

from gt_i18n.i18n_manager._i18n_manager import I18nManager


def _detect_from_accept_language(request: Any, manager: I18nManager) -> str:
    """Default, Parse Accept-Language header and resolve against configured locales."""
    accept = request.headers.get("Accept-Language", "")
    if not accept:
        return manager.default_locale

    # Parse Accept-Language: e.g. "en-US,en;q=0.9,es;q=0.8"
    locales: list[tuple[float, str]] = []
    for part in accept.split(","):
        part = part.strip()
        if not part:
            continue
        if ";q=" in part:
            lang, q = part.split(";q=", 1)
            try:
                quality = float(q.strip())
            except ValueError:
                quality = 0.0
            locales.append((quality, lang.strip()))
        else:
            locales.append((1.0, part))

    # Sort by quality descending
    locales.sort(key=lambda x: x[0], reverse=True)
    locale_list = [loc for _, loc in locales]

    # Determine the best matching locale
    gt = manager.get_gt_instance()
    result = gt.determine_locale(locale_list)
    return result or manager.default_locale

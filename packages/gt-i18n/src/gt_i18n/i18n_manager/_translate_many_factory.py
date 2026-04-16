"""Factory that binds a ``GT`` instance to a per-locale ``translate_many`` callable.

Mirrors the JS ``createTranslateMany(gtInstance, timeout)`` → ``(locale) => (sources) => gt.translateMany(...)``
pattern from gt PR #1207. The deferred ``gt_factory`` (called each invocation rather
than frozen) is what lets tests monkey-patch ``I18nManager.get_gt_instance`` and
still have the cache route through the fake GT.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from generaltranslation._gt import GT

DEFAULT_TRANSLATION_TIMEOUT_MS = 12_000


def create_translate_many_factory(
    gt_factory: Callable[[], GT],
    timeout_ms: int = DEFAULT_TRANSLATION_TIMEOUT_MS,
) -> Callable[[str], Callable[[dict[str, Any]], Awaitable[dict[str, Any]]]]:
    """Build a locale-binding factory for runtime ``translate_many`` calls.

    Example:
        translate_many = create_translate_many_factory(manager.get_gt_instance)
        es_call = translate_many("es")
        response = await es_call({"<hash>": {"source": "Hello", "metadata": {...}}})

    Args:
        gt_factory: Zero-arg callable returning a GT instance. Evaluated each
            call so patched GT instances (e.g. in tests) are respected.
        timeout_ms: Per-request timeout in milliseconds. Defaults to 12s.

    Returns:
        A callable that, given a target locale, returns an async
        ``(sources_dict) -> response_dict`` function.
    """

    def for_locale(locale: str) -> Callable[[dict[str, Any]], Awaitable[dict[str, Any]]]:
        async def _call(sources: dict[str, Any]) -> dict[str, Any]:
            gt = gt_factory()
            result = await gt.translate_many(sources, {"target_locale": locale}, timeout_ms)
            assert isinstance(result, dict), "translate_many must return a dict when given a dict of sources"
            return result

        return _call

    return for_locale

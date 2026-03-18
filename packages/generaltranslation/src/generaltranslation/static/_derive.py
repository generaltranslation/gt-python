from __future__ import annotations

import warnings


def derive(content: object) -> object:
    """Mark *content* as derivable (statically analyzable).

    This is an identity function used as a marker for the CLI tool's
    static analysis.
    """
    return content


def declare_static(content: object) -> object:
    """Mark *content* as derivable (statically analyzable).

    .. deprecated::
        Use :func:`derive` instead.
    """
    warnings.warn(
        "declare_static() is deprecated, use derive() instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    return derive(content)

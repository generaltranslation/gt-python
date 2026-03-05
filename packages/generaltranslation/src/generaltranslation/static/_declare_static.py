from __future__ import annotations


def declare_static(content):
    """Mark *content* as statically analyzable.

    This is an identity function used as a marker for static analysis.
    """
    return content

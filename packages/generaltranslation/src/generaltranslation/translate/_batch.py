"""Batch utilities for splitting and processing items."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from typing import Any, TypeVar

T = TypeVar("T")
U = TypeVar("U")


def create_batches(items: list[T], batch_size: int = 100) -> list[list[T]]:
    """Split *items* into batches of at most *batch_size*."""
    batches: list[list[T]] = []
    for i in range(0, len(items), batch_size):
        batches.append(items[i : i + batch_size])
    return batches


async def process_batches(
    items: list[Any],
    processor: Callable[[list[Any]], Awaitable[list[Any]]],
    *,
    batch_size: int = 100,
    parallel: bool = True,
) -> dict[str, Any]:
    """Process *items* in batches using *processor*.

    Returns a dict with keys ``data``, ``count``, ``batch_count``.
    """
    if not items:
        return {"data": [], "count": 0, "batch_count": 0}

    batches = create_batches(items, batch_size)
    all_items: list[Any] = []

    if parallel:
        results = await asyncio.gather(*(processor(batch) for batch in batches))
        for result in results:
            if result:
                all_items.extend(result)
    else:
        for batch in batches:
            result = await processor(batch)
            if result:
                all_items.extend(result)

    return {"data": all_items, "count": len(all_items), "batch_count": len(batches)}

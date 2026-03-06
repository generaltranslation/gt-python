"""Abstract base class for locale storage adapters."""

from __future__ import annotations

from abc import ABC, abstractmethod


class StorageAdapter(ABC):
    """Abstract storage adapter for per-request locale state."""

    @abstractmethod
    def get_item(self, key: str) -> str | None:
        """Retrieve a stored value by key."""
        ...

    @abstractmethod
    def set_item(self, key: str, value: str) -> None:
        """Store a value by key."""
        ...

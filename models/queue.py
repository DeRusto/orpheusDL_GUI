"""Download queue management for Orpheus-dl GUI Wrapper.

This module handles the queue of items to be downloaded,
including adding, removing, and tracking queued items.
"""

from typing import List, Set, Optional
from core.types import QueueItem


class DownloadQueue:
    """Manages the download queue and tracks queued items."""

    def __init__(self):
        """Initialize an empty download queue."""
        self._queue: List[QueueItem] = []
        self._queued_ids: Set[str] = set()

    def add_item(self, result: any, media_type: any) -> bool:
        """Add an item to the download queue.

        Args:
            result: Search result object with result_id attribute.
            media_type: Download type enum value.

        Returns:
            True if item was added, False if already in queue.
        """
        result_id = getattr(result, 'result_id', None)
        if result_id is None:
            return False

        # Check if already queued
        if result_id in self._queued_ids:
            return False

        # Add to queue
        self._queue.append((result, media_type))
        self._queued_ids.add(result_id)
        return True

    def remove_item(self, index: int) -> Optional[QueueItem]:
        """Remove an item from the queue by index.

        Args:
            index: Index of the item to remove.

        Returns:
            The removed item tuple, or None if index is invalid.
        """
        if 0 <= index < len(self._queue):
            removed_item = self._queue.pop(index)
            result_id = removed_item[0].result_id
            if result_id in self._queued_ids:
                self._queued_ids.remove(result_id)
            return removed_item
        return None

    def is_queued(self, result_id: str) -> bool:
        """Check if a result ID is already in the queue.

        Args:
            result_id: ID to check.

        Returns:
            True if the ID is queued, False otherwise.
        """
        return result_id in self._queued_ids

    def clear(self) -> None:
        """Remove all items from the queue."""
        self._queue.clear()
        self._queued_ids.clear()

    def get_items(self) -> List[QueueItem]:
        """Get all items in the queue.

        Returns:
            List of queue item tuples.
        """
        return self._queue.copy()

    def get_queued_ids(self) -> Set[str]:
        """Get set of all queued IDs.

        Returns:
            Set of result IDs that are queued.
        """
        return self._queued_ids.copy()

    def __len__(self) -> int:
        """Get the number of items in the queue.

        Returns:
            Number of items in queue.
        """
        return len(self._queue)

    def __iter__(self):
        """Iterate over queue items.

        Yields:
            Queue item tuples.
        """
        return iter(self._queue)

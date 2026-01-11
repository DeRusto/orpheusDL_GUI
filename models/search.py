"""Search result management for Orpheus-dl GUI Wrapper.

This module handles search results, including formatting
for display and managing result storage.
"""

from typing import List, Optional, Any
from core.types import SearchResultTuple


class SearchResultFormatter:
    """Formats search results for display in the UI."""

    @staticmethod
    def format_track(result: Any, index: int, is_queued: bool = False) -> str:
        """Format a track search result for display.

        Args:
            result: Track search result object.
            index: Display index (1-based).
            is_queued: Whether the result is already queued.

        Returns:
            Formatted display string.
        """
        title = getattr(result, "name", "Unknown Title")
        artists = getattr(result, "artists", None)

        # Format artists
        if isinstance(artists, list) and artists:
            artists_str = ", ".join(artists)
        else:
            artists_str = "Unknown Artist"

        year = getattr(result, "year", "Unknown Year")
        duration = getattr(result, "duration", 0)
        minutes = duration // 60
        seconds = duration % 60
        duration_str = f"{minutes}:{seconds:02}"

        explicit = getattr(result, "explicit", False)
        explicit_str = "Explicit" if explicit else ""

        additional = getattr(result, "additional", None)
        additional_str = " ".join(additional) if (isinstance(additional, list) and additional) else ""

        details = f" - {artists_str} (Year: {year}, Duration: {duration_str})"
        if explicit_str:
            details += f" [{explicit_str}]"
        if additional_str:
            details += f" [{additional_str}]"

        display_text = f"{index}. {title}{details} (ID: {getattr(result, 'result_id', 'N/A')})"

        if is_queued:
            display_text += " (Queued)"

        return display_text

    @staticmethod
    def format_album(result: Any, index: int, is_queued: bool = False) -> str:
        """Format an album search result for display.

        Args:
            result: Album search result object.
            index: Display index (1-based).
            is_queued: Whether the result is already queued.

        Returns:
            Formatted display string.
        """
        title = getattr(result, "name", "Unknown Album")
        artists = getattr(result, "artists", None)

        if isinstance(artists, list) and artists:
            artists_str = ", ".join(artists)
        else:
            artists_str = "Unknown Artist"

        year = getattr(result, "year", "Unknown Year")
        additional = getattr(result, "additional", None)
        additional_str = " ".join(additional) if (isinstance(additional, list) and additional) else ""

        details = f" - {artists_str} (Year: {year})"
        if additional_str:
            details += f" [{additional_str}]"

        display_text = f"{index}. {title}{details} (ID: {getattr(result, 'result_id', 'N/A')})"

        if is_queued:
            display_text += " (Queued)"

        return display_text

    @staticmethod
    def format_artist(result: Any, index: int, is_queued: bool = False) -> str:
        """Format an artist search result for display.

        Args:
            result: Artist search result object.
            index: Display index (1-based).
            is_queued: Whether the result is already queued.

        Returns:
            Formatted display string.
        """
        title = getattr(result, "name", "Unknown Artist")
        display_text = f"{index}. {title} (ID: {getattr(result, 'result_id', 'N/A')})"

        if is_queued:
            display_text += " (Queued)"

        return display_text

    @staticmethod
    def format_generic(result: Any, index: int, is_queued: bool = False) -> str:
        """Format a generic search result for display.

        Args:
            result: Generic search result object.
            index: Display index (1-based).
            is_queued: Whether the result is already queued.

        Returns:
            Formatted display string.
        """
        title = getattr(result, "name", "Unknown")
        display_text = f"{index}. {title} (ID: {getattr(result, 'result_id', 'N/A')})"

        if is_queued:
            display_text += " (Queued)"

        return display_text

    @staticmethod
    def format_result(result: Any, search_type: str, index: int, is_queued: bool = False) -> str:
        """Format a search result based on its type.

        Args:
            result: Search result object.
            search_type: Type of search ("track", "album", "artist", etc.).
            index: Display index (1-based).
            is_queued: Whether the result is already queued.

        Returns:
            Formatted display string.
        """
        if search_type == "track":
            return SearchResultFormatter.format_track(result, index, is_queued)
        elif search_type == "album":
            return SearchResultFormatter.format_album(result, index, is_queued)
        elif search_type == "artist":
            return SearchResultFormatter.format_artist(result, index, is_queued)
        else:
            return SearchResultFormatter.format_generic(result, index, is_queued)


class SearchResultManager:
    """Manages search results and their display."""

    def __init__(self):
        """Initialize an empty search result manager."""
        self._results: List[SearchResultTuple] = []
        self._search_type: str = ""

    def set_results(self, results: List[Any], media_type: Any, search_type: str) -> None:
        """Set the current search results.

        Args:
            results: List of search result objects.
            media_type: Media type enum value.
            search_type: Type of search as string ("track", "album", etc.).
        """
        self._results = [(result, media_type) for result in results]
        self._search_type = search_type

    def get_result(self, index: int) -> Optional[SearchResultTuple]:
        """Get a specific result by index.

        Args:
            index: Index of the result (0-based).

        Returns:
            Result tuple, or None if index is invalid.
        """
        if 0 <= index < len(self._results):
            return self._results[index]
        return None

    def get_all_results(self) -> List[SearchResultTuple]:
        """Get all search results.

        Returns:
            List of result tuples.
        """
        return self._results.copy()

    def clear(self) -> None:
        """Clear all search results."""
        self._results.clear()
        self._search_type = ""

    def get_search_type(self) -> str:
        """Get the current search type.

        Returns:
            Search type string.
        """
        return self._search_type

    def __len__(self) -> int:
        """Get the number of results.

        Returns:
            Number of results.
        """
        return len(self._results)

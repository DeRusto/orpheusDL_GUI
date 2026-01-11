"""Type definitions for Orpheus-dl GUI Wrapper.

This module contains type aliases and dataclasses used throughout the application.
"""

from typing import Tuple, Any, Dict, Optional
from dataclasses import dataclass

# Type aliases for clarity
SearchResultTuple = Tuple[Any, Any]  # (SearchResult, DownloadTypeEnum)
QueueItem = Tuple[Any, Any]  # Same as SearchResultTuple


@dataclass
class SearchQuery:
    """Represents a search query with module, type, and query string."""

    module_name: str
    search_type: str
    query: str


@dataclass
class DownloadConfig:
    """Configuration for download operations."""

    download_path: str
    module_name: str
    third_party_modules: Dict[Any, str]
    sdm: str

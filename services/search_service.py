"""Search service for Orpheus-dl GUI Wrapper.

This module provides search orchestration between the Orpheus API
and the UI layer.
"""

from typing import List, Any, Callable
from core.types import SearchQuery, SearchResultTuple
from core.orpheus_client import OrpheusClient


class SearchService:
    """Orchestrates search operations using the Orpheus API."""

    def __init__(self, orpheus_client: OrpheusClient):
        """Initialize the search service.

        Args:
            orpheus_client: OrpheusClient instance for API access.
        """
        self.orpheus_client = orpheus_client
        self.orpheus = orpheus_client.get_orpheus_instance()

    def search(self, query: SearchQuery, limit: int = 20) -> List[SearchResultTuple]:
        """Perform a search using the specified module.

        Args:
            query: SearchQuery with module_name, search_type, and query string.
            limit: Maximum number of results to return.

        Returns:
            List of (result, media_type) tuples.

        Raises:
            Exception: If module loading or search fails.
        """
        # Load the module
        module = self.orpheus.load_module(query.module_name)

        # Get the query type enum
        query_type = self.orpheus_client.DownloadTypeEnum[query.search_type]

        # Perform the search
        results = module.search(query_type, query.query, limit=limit)

        # Return as tuples
        if results:
            return [(result, query_type) for result in results]
        else:
            return []

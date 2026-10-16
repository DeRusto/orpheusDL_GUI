"""Download service for Orpheus-dl GUI Wrapper.

This module handles batch downloads with threading
and provides callbacks for UI updates.
"""

import os
import threading
import queue
from typing import List, Callable, Dict, Any
from core.types import QueueItem, DownloadConfig
from core.orpheus_client import OrpheusClient


class DownloadService:
    """Handles batch download operations with threading."""

    def __init__(self, orpheus_client: OrpheusClient, log_callback: Callable[[str], None] = None):
        """Initialize the download service.

        Args:
            orpheus_client: OrpheusClient instance for API access.
            log_callback: Optional callback function for logging messages.
        """
        self.orpheus_client = orpheus_client
        self.orpheus = orpheus_client.get_orpheus_instance()
        self.log_callback = log_callback
        self.is_downloading = False
        self.log_queue = queue.Queue()

    def get_log_queue(self) -> queue.Queue:
        """Get the queue containing log messages.

        Returns:
            queue.Queue: The log queue.
        """
        return self.log_queue

    def _log(self, message: str) -> None:
        """Log a message to the queue and optional callback.

        Args:
            message: The message to log.
        """
        self.log_queue.put(message)
        if self.log_callback:
            self.log_callback(message)

    def download_batch(
        self,
        queue_items: List[QueueItem],
        config: DownloadConfig,
        completion_callback: Callable[[], None] = None
    ) -> bool:
        """Start batch download in background thread.

        Args:
            queue_items: List of (result, media_type) tuples to download.
            config: Download configuration.
            completion_callback: Optional callback to run when complete.

        Returns:
            bool: True if download started, False if already in progress.
        """
        if self.is_downloading:
            self._log("Download already in progress.\n")
            return False

        self.is_downloading = True
        self._log("Starting batch download...\n")

        # Start download in background thread
        thread = threading.Thread(
            target=self._download_worker,
            args=(queue_items, config, completion_callback),
            daemon=True
        )
        thread.start()
        return True

    def _download_worker(
        self,
        queue_items: List[QueueItem],
        config: DownloadConfig,
        completion_callback: Callable[[], None] = None
    ) -> None:
        """Worker thread for batch downloads.

        Args:
            queue_items: List of (result, media_type) tuples to download.
            config: Download configuration.
            completion_callback: Optional callback to run when complete.
        """
        try:
            # Ensure download directory exists
            if not os.path.isdir(config.download_path):
                os.makedirs(config.download_path, exist_ok=True)

            # Get core download function
            orpheus_core_download = self.orpheus_client.get_core_download_function()

            # Process each queue item
            for result, media_type in queue_items:
                media_id = result.result_id
                result_name = getattr(result, 'name', 'Unknown')

                # Create media identification
                media_ident = self.orpheus_client.MediaIdentification(
                    media_type=media_type,
                    media_id=media_id
                )

                media_to_download = {config.module_name: [media_ident]}

                self._log(f"Downloading: {result_name} (ID: {media_id})\n")

                try:
                    orpheus_core_download(
                        self.orpheus,
                        media_to_download,
                        config.third_party_modules,
                        config.sdm,
                        config.download_path
                    )
                    self._log(f"Download complete for {result_name} (ID: {media_id}).\n")
                except Exception as e:
                    self._log(f"Error downloading {result_name}: {e}\n")

            self._log("Batch processing complete.\n")

        except Exception as e:
            self._log(f"Fatal error during batch download: {e}\n")

        finally:
            self.is_downloading = False
            if completion_callback:
                completion_callback()

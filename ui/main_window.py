"""Main window for Orpheus-dl GUI Wrapper.

This module contains the main application window that coordinates
all tabs and services.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import os
import queue
import threading

from config.manager import ConfigManager
from core.orpheus_client import OrpheusClient
from core.types import DownloadConfig
from models.queue import DownloadQueue
from models.search import SearchResultManager, SearchResultFormatter
from services.download_service import DownloadService
from services.command_runner import CommandRunner
from ui.tabs.search_tab import SearchTab
from ui.tabs.batch_tab import BatchTab
from ui.tabs.manual_tab import ManualTab
from ui.tabs.settings_tab import SettingsTab


class OrpheusGUI(tk.Tk):
    """Main application window for Orpheus-dl GUI Wrapper."""

    def __init__(self):
        """Initialize the main window."""
        super().__init__()
        self.title("Orpheus-dl GUI Wrapper (API Mode)")
        self.geometry("900x750")

        # Get base directory
        self.base_dir = os.path.dirname(os.path.dirname(__file__))

        # Initialize services and models
        try:
            self._initialize_services()
        except Exception as e:
            messagebox.showerror("Initialization Error", f"Could not initialize Orpheus: {e}")
            self.destroy()
            return

        # Create notebook for tabs
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # Create tabs
        self._create_tabs()

    def _initialize_services(self) -> None:
        """Initialize all services, clients, and models."""
        # Configuration manager
        self.config_manager = ConfigManager(self.base_dir)

        # Orpheus client
        self.orpheus_client = OrpheusClient(self.base_dir)
        self.orpheus = self.orpheus_client.get_orpheus_instance()

        # Models
        self.search_result_manager = SearchResultManager()
        self.download_queue = DownloadQueue()

        # Services
        # Pass None for log_callback as we will use queue-based polling
        self.download_service = DownloadService(
            self.orpheus_client,
            log_callback=None
        )

        self.command_runner = CommandRunner(self._log_manual_output)

        # Store type references for convenience
        self.DownloadTypeEnum = self.orpheus_client.DownloadTypeEnum
        self.MediaIdentification = self.orpheus_client.MediaIdentification
        self.ModuleModes = self.orpheus_client.ModuleModes

    def _create_tabs(self) -> None:
        """Create all UI tabs."""
        # Search tab
        self.search_tab = SearchTab(
            self.notebook,
            self.config_manager,
            self.search_result_manager,
            self.download_queue,
            self._handle_search,
            self._handle_add_to_queue
        )

        # Batch tab
        self.batch_tab = BatchTab(
            self.notebook,
            self.download_queue,
            self._handle_remove_from_queue,
            self._handle_batch_download,
            self._handle_clear_queue
        )

        # Manual tab
        self.manual_tab = ManualTab(
            self.notebook,
            self.command_runner
        )

        # Settings tab
        self.settings_tab = SettingsTab(
            self.notebook,
            self.config_manager,
            self.orpheus_client
        )

    # Search tab callbacks
    def _handle_search(self, module_name: str, search_type: str, query: str) -> None:
        """Handle search request from search tab.

        Args:
            module_name: Name of the module to search with.
            search_type: Type of search ("track", "album", "artist").
            query: Search query string.
        """
        # Clear previous results
        self.search_result_manager.clear()
        self.search_tab.clear_output()
        self.search_tab.append_output("Searching...\n")

        # Start search in a separate thread
        thread = threading.Thread(
            target=self._perform_search_thread,
            args=(module_name, search_type, query),
            daemon=True
        )
        thread.start()

    def _perform_search_thread(self, module_name: str, search_type: str, query: str) -> None:
        """Perform search in a background thread."""
        try:
            # Load module and perform search
            module = self.orpheus.load_module(module_name)
            query_type = self.DownloadTypeEnum[search_type]
            results = module.search(query_type, query, limit=20)

            # Schedule success callback
            self.after(0, self._on_search_complete, results, query_type, search_type, None)

        except Exception as e:
            # Schedule error callback
            self.after(0, self._on_search_complete, None, None, None, e)

    def _on_search_complete(self, results, query_type, search_type, error) -> None:
        """Handle completion of the search.

        Args:
            results: Search results list.
            query_type: Type of query used.
            search_type: String representation of search type.
            error: Exception if one occurred, else None.
        """
        if error:
            messagebox.showerror("Search Error", f"An error occurred during search:\n{error}")
            return

        if not results:
            self.search_tab.append_output("No results found.\n")
            return

        # Store results
        self.search_result_manager.set_results(results, query_type, search_type)

        # Display results
        for i, (result, _) in enumerate(self.search_result_manager.get_all_results(), start=1):
            result_id = getattr(result, 'result_id', None)
            is_queued = self.download_queue.is_queued(result_id) if result_id else False
            display_text = SearchResultFormatter.format_result(result, search_type, i, is_queued)
            self.search_tab.append_output(display_text + "\n")

        # Update the results listbox
        self.search_tab.refresh_results_display()

    def _handle_add_to_queue(self, index: int) -> None:
        """Handle adding an item to the queue.

        Args:
            index: Index of the result to add.
        """
        result_tuple = self.search_result_manager.get_result(index)
        if result_tuple is None:
            messagebox.showerror("Selection Error", "Invalid result selected.")
            return

        selected_result, media_type = result_tuple

        # Try to add to queue
        if not self.download_queue.add_item(selected_result, media_type):
            messagebox.showinfo("Already Queued", "This item is already in the queue.")
            return

        # Update queue listbox
        display_text = f"{index+1}. {selected_result.name} (ID: {selected_result.result_id})"
        self.batch_tab.get_queue_listbox().insert(tk.END, display_text)

        # Refresh search results to show queued indicator
        self.search_tab.refresh_results_display()

    # Batch tab callbacks
    def _handle_remove_from_queue(self, index: int) -> None:
        """Handle removing an item from the queue.

        Args:
            index: Index of the item to remove.
        """
        removed_item = self.download_queue.remove_item(index)
        if removed_item is not None:
            self.batch_tab.get_queue_listbox().delete(index)
            # Refresh search results to remove queued indicator
            self.search_tab.refresh_results_display()

    def _handle_batch_download(self) -> None:
        """Handle starting the batch download."""
        if len(self.download_queue) == 0:
            return

        # Get download configuration
        module_name = self.search_tab.get_module_name()
        third_party_modules = self.settings_tab.get_third_party_modules(module_name)

        download_config = DownloadConfig(
            download_path="./downloads",
            module_name=module_name,
            third_party_modules=third_party_modules,
            sdm=module_name
        )

        # Disable button during download
        self.batch_tab.get_download_button().config(state=tk.DISABLED)

        # Start download
        if self.download_service.download_batch(
            self.download_queue.get_items(),
            download_config,
            self._on_download_complete
        ):
            # Start monitoring logs only if download started
            self._monitor_download_logs()

    def _monitor_download_logs(self) -> None:
        """Poll the download service's log queue and update the text widget."""
        log_queue = self.download_service.get_log_queue()

        try:
            while True:
                msg = log_queue.get_nowait()
                self._log_download_output(msg)
        except queue.Empty:
            pass

        # Continue polling if still downloading or queue might have new items
        if self.download_service.is_downloading or not log_queue.empty():
            self.after(100, self._monitor_download_logs)

    def _handle_clear_queue(self) -> None:
        """Handle clearing the download queue."""
        self.download_queue.clear()
        self.batch_tab.get_queue_listbox().delete(0, tk.END)
        self.search_tab.refresh_results_display()

    def _on_download_complete(self) -> None:
        """Callback when batch download completes."""
        # Re-enable button
        self.batch_tab.get_download_button().config(state=tk.NORMAL)

        # Clear queue
        self.download_queue.clear()
        self.batch_tab.get_queue_listbox().delete(0, tk.END)

        # Refresh search results
        self.search_tab.refresh_results_display()

    # Logging callbacks
    def _log_download_output(self, text: str) -> None:
        """Log text to the batch download output.

        Args:
            text: Text to log.
        """
        self.batch_tab.append_log(text)

    def _log_manual_output(self, text: str) -> None:
        """Log text to the manual command output.

        Args:
            text: Text to log.
        """
        self.manual_tab.append_output(text)

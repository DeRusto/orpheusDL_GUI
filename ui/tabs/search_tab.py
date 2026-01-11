"""Search tab for Orpheus-dl GUI Wrapper."""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
from typing import Callable
from config.manager import ConfigManager
from models.search import SearchResultManager, SearchResultFormatter
from models.queue import DownloadQueue


class SearchTab:
    """Tab for searching and selecting items."""

    def __init__(
        self,
        parent: ttk.Notebook,
        config_manager: ConfigManager,
        search_result_manager: SearchResultManager,
        download_queue: DownloadQueue,
        search_callback: Callable,
        add_to_queue_callback: Callable
    ):
        """Initialize the search tab.

        Args:
            parent: Parent notebook widget.
            config_manager: ConfigManager instance.
            search_result_manager: SearchResultManager instance.
            download_queue: DownloadQueue instance.
            search_callback: Callback function to perform search.
            add_to_queue_callback: Callback function to add items to queue.
        """
        self.parent = parent
        self.config_manager = config_manager
        self.search_result_manager = search_result_manager
        self.download_queue = download_queue
        self.search_callback = search_callback
        self.add_to_queue_callback = add_to_queue_callback

        # Create tab frame
        self.frame = ttk.Frame(parent)
        parent.add(self.frame, text="Search & Select")

        # Create widgets
        self._create_widgets()

    def _create_widgets(self) -> None:
        """Create the UI widgets for this tab."""
        # Search parameters
        search_params = ttk.LabelFrame(self.frame, text="Search Parameters")
        search_params.pack(fill=tk.X, padx=10, pady=10)

        ttk.Label(search_params, text="Module:").grid(
            row=0, column=0, padx=5, pady=5, sticky=tk.E
        )

        installed_modules = self.config_manager.load_installed_modules()
        self.module_combo = ttk.Combobox(
            search_params,
            values=installed_modules,
            state="readonly",
            width=15
        )
        self.module_combo.grid(row=0, column=1, padx=5, pady=5)

        default_module = self.config_manager.load_default_module()
        if default_module and default_module in installed_modules:
            self.module_combo.set(default_module)
        elif installed_modules:
            self.module_combo.set(installed_modules[0])
        else:
            self.module_combo.set("")

        ttk.Label(search_params, text="Search Type:").grid(
            row=0, column=2, padx=5, pady=5, sticky=tk.E
        )

        self.search_type = tk.StringVar(value="track")
        search_type_menu = ttk.OptionMenu(
            search_params,
            self.search_type,
            "track",
            "track",
            "album",
            "artist"
        )
        search_type_menu.grid(row=0, column=3, padx=5, pady=5)

        ttk.Label(search_params, text="Query:").grid(
            row=0, column=4, padx=5, pady=5, sticky=tk.E
        )

        self.query_entry = ttk.Entry(search_params, width=30)
        self.query_entry.grid(row=0, column=5, padx=5, pady=5)

        self.search_button = ttk.Button(
            search_params,
            text="Search",
            command=self._on_search_clicked
        )
        self.search_button.grid(row=0, column=6, padx=5, pady=5)

        # Bind Enter key to search
        self.query_entry.bind("<Return>", lambda event: self._on_search_clicked())

        # Search results
        results_frame = ttk.LabelFrame(self.frame, text="Search Results")
        results_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.results_listbox = tk.Listbox(results_frame, selectmode=tk.SINGLE)
        self.results_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(5, 0), pady=5)

        scrollbar = ttk.Scrollbar(
            results_frame,
            orient=tk.VERTICAL,
            command=self.results_listbox.yview
        )
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, padx=5, pady=5)
        self.results_listbox.config(yscrollcommand=scrollbar.set)

        # Bind double-click to add to queue
        self.results_listbox.bind("<Double-Button-1>", lambda event: self._on_add_to_queue_clicked())

        # Add to batch button
        self.add_to_batch_button = ttk.Button(
            self.frame,
            text="Add Selected to Batch",
            command=self._on_add_to_queue_clicked
        )
        self.add_to_batch_button.pack(pady=5)

        # Search output log
        self.search_output = scrolledtext.ScrolledText(self.frame, height=8)
        self.search_output.pack(fill=tk.BOTH, padx=10, pady=5)

    def _on_search_clicked(self) -> None:
        """Handle search button click."""
        module_name = self.module_combo.get().strip()
        search_type = self.search_type.get().strip()
        query = self.query_entry.get().strip()

        if not (module_name and search_type and query):
            messagebox.showerror("Input Error", "Please fill in module, search type, and query.")
            return

        # Call the search callback
        self.search_callback(module_name, search_type, query)

    def _on_add_to_queue_clicked(self) -> None:
        """Handle add to queue button click."""
        selection = self.results_listbox.curselection()
        if not selection:
            messagebox.showerror("Selection Error", "No result selected.")
            return

        index = selection[0]
        self.add_to_queue_callback(index)

    def refresh_results_display(self) -> None:
        """Refresh the search results display with queued indicators."""
        self.results_listbox.delete(0, tk.END)
        search_type = self.search_result_manager.get_search_type()

        for i, (result, _) in enumerate(self.search_result_manager.get_all_results(), start=1):
            result_id = getattr(result, 'result_id', None)
            is_queued = self.download_queue.is_queued(result_id) if result_id else False
            display_text = SearchResultFormatter.format_result(result, search_type, i, is_queued)
            self.results_listbox.insert(tk.END, display_text)

    def get_module_name(self) -> str:
        """Get the currently selected module name.

        Returns:
            Module name string.
        """
        return self.module_combo.get().strip()

    def get_search_type(self) -> str:
        """Get the currently selected search type.

        Returns:
            Search type string.
        """
        return self.search_type.get().strip()

    def append_output(self, text: str) -> None:
        """Append text to the search output area.

        Args:
            text: Text to append.
        """
        self.search_output.insert(tk.END, text)
        self.search_output.see(tk.END)

    def clear_output(self) -> None:
        """Clear the search output area."""
        self.search_output.delete(1.0, tk.END)

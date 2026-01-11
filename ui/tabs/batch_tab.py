"""Batch queue tab for Orpheus-dl GUI Wrapper."""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
from typing import Callable
from models.queue import DownloadQueue


class BatchTab:
    """Tab for managing the download queue."""

    def __init__(
        self,
        parent: ttk.Notebook,
        download_queue: DownloadQueue,
        remove_callback: Callable,
        download_callback: Callable,
        clear_callback: Callable
    ):
        """Initialize the batch queue tab.

        Args:
            parent: Parent notebook widget.
            download_queue: DownloadQueue instance.
            remove_callback: Callback for removing selected item.
            download_callback: Callback for starting batch download.
            clear_callback: Callback for clearing the queue.
        """
        self.parent = parent
        self.download_queue = download_queue
        self.remove_callback = remove_callback
        self.download_callback = download_callback
        self.clear_callback = clear_callback

        # Create tab frame
        self.frame = ttk.Frame(parent)
        parent.add(self.frame, text="Batch Queue")

        # Create widgets
        self._create_widgets()

    def _create_widgets(self) -> None:
        """Create the UI widgets for this tab."""
        # Queue display
        queue_frame = ttk.LabelFrame(self.frame, text="Download Queue")
        queue_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.queue_listbox = tk.Listbox(queue_frame)
        self.queue_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(5, 0), pady=5)

        queue_scroll = ttk.Scrollbar(
            queue_frame,
            orient=tk.VERTICAL,
            command=self.queue_listbox.yview
        )
        queue_scroll.pack(side=tk.RIGHT, fill=tk.Y, padx=5, pady=5)
        self.queue_listbox.config(yscrollcommand=queue_scroll.set)

        # Bind Delete key to remove
        self.queue_listbox.bind("<Delete>", lambda event: self._on_remove_clicked())

        # Buttons
        btn_frame = ttk.Frame(self.frame)
        btn_frame.pack(fill=tk.X, padx=10, pady=5)

        self.remove_queue_button = ttk.Button(
            btn_frame,
            text="Remove Selected",
            command=self._on_remove_clicked
        )
        self.remove_queue_button.pack(side=tk.LEFT, padx=5)

        self.download_batch_button = ttk.Button(
            btn_frame,
            text="Download Batch",
            command=self._on_download_clicked
        )
        self.download_batch_button.pack(side=tk.LEFT, padx=5)

        self.clear_queue_button = ttk.Button(
            btn_frame,
            text="Clear Queue",
            command=self._on_clear_clicked
        )
        self.clear_queue_button.pack(side=tk.LEFT, padx=5)

        # Batch log
        self.batch_log = scrolledtext.ScrolledText(self.frame, height=10)
        self.batch_log.pack(fill=tk.BOTH, padx=10, pady=5)

    def _on_remove_clicked(self) -> None:
        """Handle remove button click."""
        selection = self.queue_listbox.curselection()
        if not selection:
            messagebox.showerror("Selection Error", "No item selected in the queue.")
            return

        index = selection[0]
        self.remove_callback(index)

    def _on_download_clicked(self) -> None:
        """Handle download button click."""
        if len(self.download_queue) == 0:
            messagebox.showinfo("Queue Empty", "No items in the batch queue to download.")
            return

        self.download_callback()

    def _on_clear_clicked(self) -> None:
        """Handle clear button click."""
        self.clear_callback()

    def append_log(self, text: str) -> None:
        """Append text to the batch log.

        Args:
            text: Text to append.
        """
        self.batch_log.insert(tk.END, text)
        self.batch_log.see(tk.END)

    def get_queue_listbox(self) -> tk.Listbox:
        """Get the queue listbox widget.

        Returns:
            The queue listbox widget.
        """
        return self.queue_listbox

    def get_download_button(self) -> ttk.Button:
        """Get the download button widget.

        Returns:
            The download button widget.
        """
        return self.download_batch_button

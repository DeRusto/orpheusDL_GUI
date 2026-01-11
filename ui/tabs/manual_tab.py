"""Manual command builder tab for Orpheus-dl GUI Wrapper."""

import tkinter as tk
from tkinter import ttk, scrolledtext
import queue as queue_module
from services.command_runner import CommandRunner


class ManualTab:
    """Tab for building and running manual Orpheus commands."""

    def __init__(self, parent: ttk.Notebook, command_runner: CommandRunner):
        """Initialize the manual command tab.

        Args:
            parent: Parent notebook widget.
            command_runner: CommandRunner service instance.
        """
        self.parent = parent
        self.command_runner = command_runner

        # Create tab frame
        self.frame = ttk.Frame(parent)
        parent.add(self.frame, text="Manual Command Builder")

        # Create widgets
        self._create_widgets()

    def _create_widgets(self) -> None:
        """Create the UI widgets for this tab."""
        ttk.Label(
            self.frame,
            text="Command (e.g. py orpheus.py download qobuz track 52151405):"
        ).pack(anchor=tk.W, padx=10, pady=5)

        self.manual_cmd_entry = ttk.Entry(self.frame, width=80)
        self.manual_cmd_entry.pack(padx=10, pady=5)

        self.manual_run_button = ttk.Button(
            self.frame,
            text="Run Command",
            command=self._on_run_clicked
        )
        self.manual_run_button.pack(padx=10, pady=5)

        self.manual_output = scrolledtext.ScrolledText(self.frame, height=10)
        self.manual_output.pack(fill=tk.BOTH, padx=10, pady=5)

    def _on_run_clicked(self) -> None:
        """Handle run button click."""
        from tkinter import messagebox

        cmd_text = self.manual_cmd_entry.get().strip()
        if not cmd_text:
            messagebox.showerror("Input Error", "Please enter a command.")
            return

        cmd = cmd_text.split()
        self.command_runner.run_command(cmd)

        # Start polling for output
        self._update_output()

    def _update_output(self) -> None:
        """Poll the command runner's output queue and update the text widget."""
        output_queue = self.command_runner.get_output_queue()

        try:
            while True:
                line = output_queue.get_nowait()
                self.manual_output.insert(tk.END, line)
                self.manual_output.see(tk.END)
        except queue_module.Empty:
            # Schedule next poll
            self.frame.after(100, self._update_output)

    def append_output(self, text: str) -> None:
        """Append text to the output area.

        Args:
            text: Text to append.
        """
        self.manual_output.insert(tk.END, text)
        self.manual_output.see(tk.END)

"""Command runner service for Orpheus-dl GUI Wrapper.

This module handles subprocess execution for manual commands
with output streaming.
"""

import subprocess
import threading
import queue
from typing import List, Callable


class CommandRunner:
    """Executes commands via subprocess with output streaming."""

    def __init__(self, output_callback: Callable[[str], None]):
        """Initialize the command runner.

        Args:
            output_callback: Callback function for command output.
        """
        self.output_callback = output_callback
        self.output_queue: queue.Queue = queue.Queue()

    def run_command(self, cmd: List[str]) -> None:
        """Run a command in a background thread.

        Args:
            cmd: Command and arguments as list of strings.
        """
        self.output_callback(f"Running: {' '.join(cmd)}\n")

        # Start subprocess in background thread
        thread = threading.Thread(
            target=self._run_subprocess,
            args=(cmd, self.output_queue),
            daemon=True
        )
        thread.start()

    def _run_subprocess(self, cmd: List[str], output_queue: queue.Queue) -> None:
        """Worker thread for running subprocess.

        Args:
            cmd: Command and arguments as list of strings.
            output_queue: Queue for output lines.
        """
        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True
            )

            # Stream output lines
            if process.stdout:
                for line in process.stdout:
                    output_queue.put(line)

            process.stdout.close() if process.stdout else None
            process.wait()

            output_queue.put("\nCommand complete.\n")

        except Exception as e:
            output_queue.put(f"Error: {e}\n")

    def get_output_queue(self) -> queue.Queue:
        """Get the output queue for polling.

        Returns:
            Queue containing output lines.
        """
        return self.output_queue

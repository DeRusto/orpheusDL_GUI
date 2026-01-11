#!/usr/bin/env python3
# orpheus_gui.py
#
# Copyright (c) 2025 DeRusto
#
# This file is part of Orpheus-dl GUI Wrapper.
#
# Licensed under the MIT License. See the LICENSE file in the project root for license information.

"""Main entry point for Orpheus-dl GUI Wrapper.

This is a graphical user interface for Orpheus-dl that makes queuing up multiple
downloads and browsing for tracks, albums, and playlists easier and more intuitive.
"""

from ui.main_window import OrpheusGUI


def main() -> None:
    """Launch the Orpheus-dl GUI application."""
    app = OrpheusGUI()
    app.mainloop()


if __name__ == "__main__":
    main()

# Orpheus-dl GUI Wrapper

A graphical user interface for [Orpheus-dl](https://github.com/OrfiTeam/OrpheusDL) that makes queuing up multiple downloads and browsing for tracks, albums, and playlists easier and more intuitive. This project leverages the Orpheus-dl Python API to provide a modern, user-friendly front end while preserving the rich CLI output during downloads.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.


## Features

- **Search & Browse:**  
  Perform searches by track, album, or artist. Results are displayed in a list with detailed metadata (e.g. track/album name, artist, version/edition, and media ID).

- **Queue Management:**  
  Easily add search results to a download queue using double-click or via an "Add to Queue" button. Visual indicators ("(Queued)") mark items that have already been added.  

- **Batch Download:**  
  Process the entire queue at once. The CLI output is displayed in an integrated terminal area during downloads, providing real-time feedback and progress details.

- **Queue Editing:**  
  Remove items from the queue using the Delete key or a "Remove Selected" button. The search results list automatically refreshes to remove the "(Queued)" indicator for items that have been removed from the queue.

- **Settings Panel:**  
  Configure default modules for covers, lyrics, and credits. Drop-down menus allow you to choose a separate module for each (or select "Default" to use the main module). Additional settings (e.g. download path, quality) are read from the configuration file.

- **Keyboard Shortcuts:**  
  - Press **Enter** in the search field to initiate a search.
  - Double-click search results to add them to the queue.
  - Press **Delete** in the queue list to remove selected items.
  
## Configuration
Main Module:
The main service is selected via a drop-down in the Search tab.

Third-Party Modules:
The default configuration for covers, lyrics, and credits can be set in your settings file (e.g., config/settings.json) under the "global": { "module_defaults": { ... } } section.
The GUI also provides drop-downs in the Settings tab to override these defaults.

## Installation

### Quick Setup

1. **Clone or download** this repository
2. **Copy the entire directory** (or its contents) to the root of your Orpheus-dl installation
3. Your directory structure should look like this:
   ```
   OrpheusDL/                    # Your Orpheus-dl root directory
   ├── orpheus.py                # Orpheus-dl main file
   ├── orpheus/                  # Orpheus-dl core folder
   ├── modules/                  # Orpheus-dl modules
   ├── orpheus_gui.py            # GUI entry point (from this repo)
   ├── core/                     # GUI core components (from this repo)
   ├── models/                   # GUI data models (from this repo)
   ├── config/                   # GUI configuration (from this repo)
   ├── services/                 # GUI services (from this repo)
   └── ui/                       # GUI interface (from this repo)
   ```
4. Run the GUI with: `python orpheus_gui.py`

### What Gets Created

When you run the GUI for the first time, it will automatically create:
- `default_module.txt` - stores your default module selection
- `config/settings.json` - Orpheus-dl configuration (if it doesn't exist)

**Note:** The GUI reads from the same `config/settings.json` that Orpheus-dl uses, so your existing settings are preserved.

## Requirements

- **Orpheus-dl:**  
  Your application relies on Orpheus-dl being installed. Make sure you have a working Orpheus-dl installation (including the `orpheus.py` file and the accompanying `orpheus/` folder). You can clone or download Orpheus-dl from its [GitHub repository](https://github.com/OrfiTeam/OrpheusDL).

- **Python:**
  The application requires Python 3.7 or later.
  (Tkinter is used for the GUI and is typically included with standard Python distributions.)

## Project Structure

This application uses a modular architecture for better maintainability:

- **`orpheus_gui.py`** - Main entry point (run this file)
- **`core/`** - Orpheus API integration and type definitions
- **`models/`** - Queue management and search result handling
- **`config/`** - Configuration file management
- **`services/`** - Download orchestration and command execution
- **`ui/`** - User interface components and tab layouts

The original single-file version is preserved as `orpheus_gui_legacy.py` if needed for reference.

## Upgrading from Previous Version

If you were using the old single-file version:

1. The new version is **fully compatible** - no configuration changes needed
2. Your existing `default_module.txt` and `config/settings.json` will work as-is
3. Simply replace `orpheus_gui.py` with the new directory structure
4. The functionality is identical, just better organized

## Troubleshooting

### "ModuleNotFoundError" or "ImportError"

**Problem:** You get errors like `ModuleNotFoundError: No module named 'core'` or `ImportError: cannot import name 'OrpheusGUI'`

**Solution:** Make sure you copied **all directories** (`core/`, `models/`, `config/`, `services/`, `ui/`) to your Orpheus-dl root directory, not just `orpheus_gui.py`.

### "Could not initialize Orpheus" error

**Problem:** The application shows an initialization error on startup.

**Solution:** Verify that:
- You're running the GUI from the Orpheus-dl root directory
- The `orpheus.py` file exists in the same directory
- The `orpheus/` folder exists and contains `core.py`

### GUI doesn't start or crashes immediately

**Problem:** The window doesn't appear or closes right away.

**Solution:**
- Make sure Python 3.7+ is installed: `python --version`
- Verify Tkinter is available: `python -m tkinter` (should open a test window)
- Check for error messages in the terminal/console

### Need the old version?

The legacy single-file version is available as `orpheus_gui_legacy.py` if you need it.

## Credits
Orpheus-dl: The underlying CLI tool and Python API by OrfiTeam/OrpheusDL
Tkinter: For providing the GUI framework.
Thanks to everyone who contributed ideas and feedback!
  
  


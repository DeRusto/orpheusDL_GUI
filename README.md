# Orpheus-dl GUI Wrapper

A graphical user interface for [Orpheus-dl](https://github.com/OrfiTeam/OrpheusDL) that makes queuing up multiple downloads and browsing for tracks, albums, and playlists easier and more intuitive. This project leverages the Orpheus-dl Python API to provide a modern, user-friendly front end while preserving the rich CLI output during downloads.

## License

This project is licensed under the MIT License - see the [LICENSE] file for details.


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

	Place the `orpheus_gui.py` file in the root directory of your Orpheus-dl installation. When you run it, it will load settings from the configuration file (e.g. `config/settings.json`) and create its own text file for the default module if needed.

## Requirements

- **Orpheus-dl:**  
  Your application relies on Orpheus-dl being installed. Make sure you have a working Orpheus-dl installation (including the `orpheus.py` file and the accompanying `orpheus/` folder). You can clone or download Orpheus-dl from its [GitHub repository](https://github.com/OrfiTeam/OrpheusDL).

- **Python:**  
  The application requires Python 3.7 or later.  
  (Tkinter is used for the GUI and is typically included with standard Python distributions.)
  
  
## Credits
Orpheus-dl: The underlying CLI tool and Python API by OrfiTeam/OrpheusDL
Tkinter: For providing the GUI framework.
Thanks to everyone who contributed ideas and feedback!
  
  


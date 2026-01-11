# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

Orpheus-dl GUI Wrapper is a Tkinter-based graphical interface for the Orpheus-dl music downloading CLI tool. The application follows a modular architecture with clear separation of concerns between UI, business logic, and data access layers.

## Prerequisites

This GUI wrapper expects to be placed in the **root directory of an existing Orpheus-dl installation**. The application dynamically imports:
- `orpheus.py` from the repository root
- `orpheus/core.py` for core download functionality
- Modules from `modules/` or `orpheus/modules/` directories

Without these dependencies, the application will fail to initialize.

## Running the Application

```bash
# Main entry point (27 lines, imports from ui/main_window.py)
python orpheus_gui.py
```

No build process, tests, or linting configuration exists in this repository.

## Architecture

The application has been refactored from a 527-line monolithic file into a modular structure:

### Directory Structure

```
orpheusDL_GUI/
├── orpheus_gui.py              # Entry point (~27 lines)
├── orpheus_gui_legacy.py       # Backup of original monolithic version
├── core/                       # Core Orpheus API integration
│   ├── __init__.py
│   ├── orpheus_client.py       # OrpheusClient - wraps Orpheus API
│   └── types.py                # Type definitions and dataclasses
├── models/                     # Data models and business logic
│   ├── __init__.py
│   ├── queue.py                # DownloadQueue - queue management
│   └── search.py               # SearchResultManager, SearchResultFormatter
├── config/                     # Configuration management
│   ├── __init__.py
│   └── manager.py              # ConfigManager - file I/O
├── services/                   # Service layer (orchestration)
│   ├── __init__.py
│   ├── search_service.py       # SearchService (not currently used)
│   ├── download_service.py     # DownloadService - threaded downloads
│   └── command_runner.py       # CommandRunner - subprocess execution
└── ui/                         # User interface components
    ├── __init__.py
    ├── main_window.py          # OrpheusGUI - main application window
    └── tabs/                   # Tab components
        ├── __init__.py
        ├── search_tab.py       # SearchTab - search interface
        ├── batch_tab.py        # BatchTab - queue management
        ├── manual_tab.py       # ManualTab - manual commands
        └── settings_tab.py     # SettingsTab - configuration
```

### Component Responsibilities

#### Entry Point
- **orpheus_gui.py**: Minimal launcher that imports `OrpheusGUI` from `ui.main_window` and starts the application.

#### Core Layer
- **OrpheusClient** (`core/orpheus_client.py`): Encapsulates dynamic module loading of `orpheus.py` and `orpheus/core.py`. Provides clean API for accessing Orpheus functionality and type definitions (`Orpheus`, `DownloadTypeEnum`, `MediaIdentification`, `ModuleModes`).
- **Types** (`core/types.py`): Type aliases (`SearchResultTuple`, `QueueItem`) and dataclasses (`SearchQuery`, `DownloadConfig`).

#### Models Layer
- **DownloadQueue** (`models/queue.py`): Manages download queue with duplicate prevention via `queued_ids` set. Methods: `add_item()`, `remove_item()`, `is_queued()`, `clear()`, `get_items()`.
- **SearchResultManager** (`models/search.py`): Stores and manages search results. Methods: `set_results()`, `get_result()`, `get_all_results()`, `clear()`.
- **SearchResultFormatter** (`models/search.py`): Static methods for formatting search results by type (track, album, artist, generic).

#### Configuration Layer
- **ConfigManager** (`config/manager.py`): Handles all file I/O for configuration. Methods: `load_installed_modules()`, `load_default_module()`, `save_default_module()`, `load_settings_json()`, `save_settings_json()`.

#### Services Layer
- **DownloadService** (`services/download_service.py`): Orchestrates batch downloads in background threads with callbacks for UI updates.
- **CommandRunner** (`services/command_runner.py`): Executes subprocess commands with output streaming via queue.
- **SearchService** (`services/search_service.py`): Service for search orchestration (created but not currently integrated).

#### UI Layer
- **OrpheusGUI** (`ui/main_window.py`): Main application window. Initializes all services and models, creates tabs, provides callback methods that connect tab actions to business logic.
- **SearchTab** (`ui/tabs/search_tab.py`): Search interface with module selection, search type, query input, and results display.
- **BatchTab** (`ui/tabs/batch_tab.py`): Queue management with download, remove, and clear buttons, plus batch log output.
- **ManualTab** (`ui/tabs/manual_tab.py`): Manual command builder with subprocess execution.
- **SettingsTab** (`ui/tabs/settings_tab.py`): Configuration editor and module defaults.

### Key Data Flow Patterns

#### Search Flow
1. User enters search in `SearchTab`
2. `SearchTab` calls `_handle_search()` callback in `OrpheusGUI`
3. `OrpheusGUI` uses `OrpheusClient` to load module and perform search
4. Results stored in `SearchResultManager`
5. `SearchResultFormatter` formats results for display
6. `SearchTab.refresh_results_display()` updates UI with "(Queued)" indicators

#### Queue Management Flow
1. User double-clicks result or clicks "Add to Batch"
2. `SearchTab` calls `_handle_add_to_queue()` callback
3. `DownloadQueue.add_item()` adds item (fails if duplicate)
4. `SearchTab.refresh_results_display()` updates to show "(Queued)"
5. Item appears in `BatchTab` queue listbox

#### Download Flow
1. User clicks "Download Batch" in `BatchTab`
2. `BatchTab` calls `_handle_batch_download()` callback
3. `OrpheusGUI` creates `DownloadConfig` from settings
4. `DownloadService.download_batch()` starts background thread
5. Progress logged via `_log_download_output()` callback to `BatchTab`
6. On completion, `_on_download_complete()` clears queue and re-enables button

### Callback Pattern
The main window (`OrpheusGUI`) provides callback methods that tabs invoke for actions:
- `_handle_search(module_name, search_type, query)` - Perform search
- `_handle_add_to_queue(index)` - Add result to queue
- `_handle_remove_from_queue(index)` - Remove from queue
- `_handle_batch_download()` - Start batch download
- `_handle_clear_queue()` - Clear download queue
- `_log_download_output(text)` - Log to batch tab
- `_log_manual_output(text)` - Log to manual tab

### Threading
- **Download operations**: Run in daemon threads via `DownloadService`
- **Manual commands**: Run in daemon threads via `CommandRunner`
- **UI updates from threads**: Use callbacks that are called from worker threads; Tkinter widgets are updated directly (considered safe for simple text insertions)

### Configuration Files
- `default_module.txt`: Stores user's default module selection (created at runtime in repo root)
- `config/settings.json`: Orpheus-dl configuration (read/written by Settings tab)

## Important Notes for Development

### Dynamic Module Loading
The `OrpheusClient` uses `importlib.util` to dynamically load:
- `orpheus.py` as "orpheus_entry"
- `orpheus/core.py` as "orpheus_core"

This approach avoids namespace conflicts. The loading logic in `OrpheusClient._load_orpheus_api()` and `OrpheusClient._load_orpheus_core()` must preserve exact import behavior.

### Queue State Management
`DownloadQueue` maintains two data structures:
- `_queue`: List of `(result, media_type)` tuples
- `_queued_ids`: Set of `result_id` strings for O(1) duplicate checking

When adding/removing items, both structures must stay synchronized.

### Type Hints
All modules use type hints extensively:
- Function signatures have parameter and return types
- Instance variables are typed in `__init__`
- Generic types use `List[T]`, `Dict[K, V]`, `Optional[T]`
- Callbacks use `Callable[[args], return_type]`

### Error Handling
- Initialization errors trigger error messagebox and destroy window
- Search/download errors displayed in respective output widgets
- File I/O errors logged to console and return False/empty values

### Testing
No automated tests exist. Manual testing workflow:
1. Application starts without errors
2. Module dropdown populates
3. Search returns results with proper formatting
4. Add to queue works, shows "(Queued)" indicator
5. Remove from queue works, removes "(Queued)"
6. Batch download completes successfully with log output
7. Settings save and load correctly
8. Manual commands execute and stream output

## Module Dependencies

```
orpheus_gui.py
  └─> ui.main_window.OrpheusGUI
       ├─> config.manager.ConfigManager
       ├─> core.orpheus_client.OrpheusClient
       │    └─> core.types
       ├─> models.queue.DownloadQueue
       │    └─> core.types
       ├─> models.search.SearchResultManager, SearchResultFormatter
       │    └─> core.types
       ├─> services.download_service.DownloadService
       │    └─> core.orpheus_client, core.types
       ├─> services.command_runner.CommandRunner
       └─> ui.tabs.*
            └─> (models, config, services as needed)
```

## Legacy Version

The original monolithic implementation is preserved as `orpheus_gui_legacy.py` (527 lines). The refactored version maintains identical functionality while providing better maintainability, testability, and extensibility.

## Windows-Specific Considerations

This repository is currently on Windows (`win32` platform). File paths use `os.path.join()` for cross-platform compatibility, but manual command execution (subprocess) may behave differently on Unix systems.

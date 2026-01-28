"""Configuration management for Orpheus-dl GUI Wrapper.

This module handles loading and saving configuration files,
including module discovery and settings management.
"""

import os
import json
from typing import List, Optional, Dict


class ConfigManager:
    """Manages configuration files and module discovery."""

    def __init__(self, base_dir: Optional[str] = None):
        """Initialize the configuration manager.

        Args:
            base_dir: Base directory for configuration files.
                     If None, uses the directory of the calling script.
        """
        self.base_dir = base_dir if base_dir is not None else os.path.dirname(__file__)

    def load_installed_modules(self) -> List[str]:
        """
        Get the names of installed Orpheus-dl modules from the modules directory.
        
        Searches for a "modules" directory under the configured base directory (falling back to "orpheus/modules") and returns the names of subdirectories found, excluding "__pycache__" and "example".
        
        Returns:
            List[str]: Module directory names found; empty list if no modules directory exists.
        """
        modules_dir = os.path.join(self.base_dir, "modules")
        if not os.path.isdir(modules_dir):
            modules_dir = os.path.join(self.base_dir, "orpheus", "modules")

        if os.path.isdir(modules_dir):
            with os.scandir(modules_dir) as entries:
                modules = [
                    entry.name for entry in entries
                    if entry.is_dir() and entry.name not in ("__pycache__", "example")
                ]
            return modules
        else:
            return []

    def load_default_module(self) -> Optional[str]:
        """Load the default module name from configuration file.

        Returns:
            Module name if found, None otherwise.
        """
        config_path = os.path.join(self.base_dir, "default_module.txt")
        if os.path.exists(config_path):
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    return f.read().strip()
            except Exception as e:
                print(f"Error reading default module file: {e}")
                return None
        return None

    def save_default_module(self, module_name: str) -> bool:
        """Save the default module name to configuration file.

        Args:
            module_name: Name of the module to set as default.

        Returns:
            True if successful, False otherwise.
        """
        config_path = os.path.join(self.base_dir, "default_module.txt")
        try:
            with open(config_path, "w", encoding="utf-8") as f:
                f.write(module_name.strip())
            return True
        except Exception as e:
            print(f"Error saving default module: {e}")
            return False

    def load_settings_json(self) -> str:
        """Load the contents of the settings.json configuration file.

        Returns:
            JSON string contents of the file, or "{}" if file doesn't exist,
            or error message string if an error occurs.
        """
        config_path = os.path.join(self.base_dir, "config", "settings.json")
        if os.path.exists(config_path):
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    return f.read()
            except Exception as e:
                return f"Error reading config file: {e}"
        else:
            return "{}"

    def save_settings_json(self, contents: str) -> bool:
        """Save contents to the settings.json configuration file.

        Args:
            contents: JSON string to save to the file.

        Returns:
            True if successful, False otherwise.
        """
        config_dir = os.path.join(self.base_dir, "config")
        if not os.path.isdir(config_dir):
            os.makedirs(config_dir, exist_ok=True)

        config_path = os.path.join(config_dir, "settings.json")
        try:
            # Validate JSON before saving
            json.loads(contents)
            with open(config_path, "w", encoding="utf-8") as f:
                f.write(contents)
            return True
        except json.JSONDecodeError as e:
            print(f"Invalid JSON format: {e}")
            return False
        except Exception as e:
            print(f"Error saving config file: {e}")
            return False

    def get_module_defaults(self, settings: Dict) -> Dict[str, str]:
        """Extract module defaults from settings dictionary.

        Args:
            settings: Orpheus settings dictionary.

        Returns:
            Dictionary of module defaults (covers, lyrics, credits).
        """
        try:
            return settings.get('global', {}).get('module_defaults', {})
        except (AttributeError, TypeError):
            return {}
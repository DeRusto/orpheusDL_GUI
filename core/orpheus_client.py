"""Orpheus API client wrapper.

This module handles dynamic loading of the Orpheus-dl API
and provides a clean interface to its functionality.
"""

import os
import importlib.util
from typing import Any, Callable, Optional


class OrpheusClient:
    """Wrapper for Orpheus-dl API with dynamic module loading."""

    def __init__(self, base_dir: Optional[str] = None):
        """Initialize the Orpheus client.

        Args:
            base_dir: Base directory where orpheus.py is located.
                     If None, uses the directory of the calling script.

        Raises:
            ImportError: If orpheus.py or orpheus/core.py cannot be loaded.
            AttributeError: If required symbols are not found in modules.
        """
        self.base_dir = base_dir if base_dir is not None else os.path.dirname(__file__)

        # Load main Orpheus API
        self._load_orpheus_api()

        # Load core download function
        self._load_orpheus_core()

        # Initialize Orpheus instance
        self.orpheus_instance: Optional[Any] = None

    def _load_orpheus_api(self) -> None:
        """Load the main API from orpheus.py.

        Raises:
            ImportError: If orpheus.py cannot be loaded.
            AttributeError: If required symbols are not found.
        """
        orpheus_path = os.path.join(self.base_dir, "orpheus.py")
        spec = importlib.util.spec_from_file_location("orpheus_entry", orpheus_path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Cannot load orpheus.py from {orpheus_path}")

        orpheus_entry = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(orpheus_entry)

        # Extract required symbols
        self.Orpheus = orpheus_entry.Orpheus
        self.DownloadTypeEnum = orpheus_entry.DownloadTypeEnum
        self.MediaIdentification = orpheus_entry.MediaIdentification
        self.ModuleModes = orpheus_entry.ModuleModes

    def _load_orpheus_core(self) -> None:
        """Load the core download function from orpheus/core.py.

        Raises:
            ImportError: If orpheus/core.py cannot be loaded.
            AttributeError: If orpheus_core_download is not found.
        """
        core_path = os.path.join(self.base_dir, "orpheus", "core.py")
        spec_core = importlib.util.spec_from_file_location("orpheus_core", core_path)
        if spec_core is None or spec_core.loader is None:
            raise ImportError(f"Cannot load orpheus/core.py from {core_path}")

        orpheus_core = importlib.util.module_from_spec(spec_core)
        spec_core.loader.exec_module(orpheus_core)

        self.orpheus_core_download = orpheus_core.orpheus_core_download

    def get_orpheus_instance(self, create_if_missing: bool = True) -> Any:
        """Get or create the Orpheus instance.

        Args:
            create_if_missing: If True, creates instance if it doesn't exist.

        Returns:
            Orpheus instance.

        Raises:
            Exception: If instance cannot be created.
        """
        if self.orpheus_instance is None and create_if_missing:
            self.orpheus_instance = self.Orpheus(False)
        return self.orpheus_instance

    def load_module(self, module_name: str) -> Any:
        """Load a specific Orpheus module.

        Args:
            module_name: Name of the module to load.

        Returns:
            Loaded module object.

        Raises:
            Exception: If module cannot be loaded.
        """
        orpheus = self.get_orpheus_instance()
        return orpheus.load_module(module_name)

    def get_core_download_function(self) -> Callable:
        """Get the core download function.

        Returns:
            The orpheus_core_download function.
        """
        return self.orpheus_core_download

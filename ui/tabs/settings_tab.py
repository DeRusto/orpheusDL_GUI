"""Settings tab for Orpheus-dl GUI Wrapper."""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
from typing import Dict, Any
from config.manager import ConfigManager
from core.orpheus_client import OrpheusClient


class SettingsTab:
    """Tab for managing application settings."""

    def __init__(
        self,
        parent: ttk.Notebook,
        config_manager: ConfigManager,
        orpheus_client: OrpheusClient
    ):
        """Initialize the settings tab.

        Args:
            parent: Parent notebook widget.
            config_manager: ConfigManager instance.
            orpheus_client: OrpheusClient instance.
        """
        self.parent = parent
        self.config_manager = config_manager
        self.orpheus_client = orpheus_client
        self.orpheus = orpheus_client.get_orpheus_instance()

        # Create tab frame
        self.frame = ttk.Frame(parent)
        parent.add(self.frame, text="Settings")

        # Create widgets
        self._create_widgets()

    def _create_widgets(self) -> None:
        """Create the UI widgets for this tab."""
        # Configuration file editor
        config_frame = ttk.LabelFrame(
            self.frame,
            text="OrpheusDL Configuration (config/settings.json)"
        )
        config_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.config_text = scrolledtext.ScrolledText(config_frame, height=15)
        self.config_text.pack(fill=tk.BOTH, padx=5, pady=5)
        config_contents = self.config_manager.load_settings_json()
        self.config_text.insert(tk.END, config_contents)

        self.save_config_button = ttk.Button(
            config_frame,
            text="Save Config",
            command=self._on_save_config_clicked
        )
        self.save_config_button.pack(pady=5)

        # Default module selection
        default_frame = ttk.LabelFrame(self.frame, text="Default Module Setting")
        default_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Label(default_frame, text="Select Default Module:").grid(
            row=0, column=0, padx=5, pady=5, sticky=tk.E
        )

        installed_modules = self.config_manager.load_installed_modules()
        self.default_module_combo = ttk.Combobox(
            default_frame,
            values=installed_modules,
            state="readonly",
            width=15
        )
        self.default_module_combo.grid(row=0, column=1, padx=5, pady=5)

        current_default = self.config_manager.load_default_module()
        if current_default and current_default in installed_modules:
            self.default_module_combo.set(current_default)
        elif installed_modules:
            self.default_module_combo.set(installed_modules[0])
        else:
            self.default_module_combo.set("")

        # Third-party modules settings
        third_party_frame = ttk.LabelFrame(
            self.frame,
            text="Third‑Party Modules Settings"
        )
        third_party_frame.pack(fill=tk.X, padx=10, pady=10)

        # Get available modules
        available_modules = self.config_manager.load_installed_modules()
        available_modules.insert(0, "default")

        ttk.Label(third_party_frame, text="Covers Module:").grid(
            row=0, column=0, padx=5, pady=5, sticky=tk.E
        )
        self.covers_module_combo = ttk.Combobox(
            third_party_frame,
            values=available_modules,
            state="readonly",
            width=15
        )
        self.covers_module_combo.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(third_party_frame, text="Lyrics Module:").grid(
            row=1, column=0, padx=5, pady=5, sticky=tk.E
        )
        self.lyrics_module_combo = ttk.Combobox(
            third_party_frame,
            values=available_modules,
            state="readonly",
            width=15
        )
        self.lyrics_module_combo.grid(row=1, column=1, padx=5, pady=5)

        ttk.Label(third_party_frame, text="Credits Module:").grid(
            row=2, column=0, padx=5, pady=5, sticky=tk.E
        )
        self.credits_module_combo = ttk.Combobox(
            third_party_frame,
            values=available_modules,
            state="readonly",
            width=15
        )
        self.credits_module_combo.grid(row=2, column=1, padx=5, pady=5)

        # Read defaults from configuration
        module_defaults = self.orpheus.settings['global']['module_defaults']

        self.covers_module_combo.set(module_defaults.get("covers", "default"))
        self.lyrics_module_combo.set(module_defaults.get("lyrics", "default"))
        self.credits_module_combo.set(module_defaults.get("credits", "default"))

        self.save_default_button = ttk.Button(
            default_frame,
            text="Save Default Module",
            command=self._on_save_default_module_clicked
        )
        self.save_default_button.grid(row=0, column=2, padx=5, pady=5)

    def _on_save_config_clicked(self) -> None:
        """Handle save config button click."""
        new_config = self.config_text.get(1.0, tk.END)
        if self.config_manager.save_settings_json(new_config):
            messagebox.showinfo("Config Saved", "Configuration saved successfully.")
        else:
            messagebox.showerror("Error", "Failed to save configuration.")

    def _on_save_default_module_clicked(self) -> None:
        """Handle save default module button click."""
        new_default = self.default_module_combo.get().strip()
        if new_default:
            if self.config_manager.save_default_module(new_default):
                messagebox.showinfo(
                    "Default Module Saved",
                    f"Default module set to '{new_default}'."
                )
            else:
                messagebox.showerror("Error", "Failed to save default module.")
        else:
            messagebox.showerror("Input Error", "Please select a default module.")

    def get_third_party_modules(self, main_module: str) -> Dict[Any, str]:
        """Get third-party module configuration.

        Args:
            main_module: Main module name to use as default.

        Returns:
            Dictionary mapping ModuleModes to module names.
        """
        covers = self.covers_module_combo.get().strip()
        lyrics = self.lyrics_module_combo.get().strip()
        credits = self.credits_module_combo.get().strip()

        ModuleModes = self.orpheus_client.ModuleModes

        return {
            ModuleModes.covers: covers if covers != "default" else main_module,
            ModuleModes.lyrics: lyrics if lyrics != "default" else main_module,
            ModuleModes.credits: credits if credits != "default" else main_module
        }

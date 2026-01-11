# orpheus_gui.py
#
# Copyright (c) 2025 DeRusto
#
# This file is part of Orpheus-dl GUI Wrapper.
#
# Licensed under the MIT License. See the LICENSE file in the project root for license information.

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, simpledialog
import threading
import queue
import os
import re
import json
import importlib.util

# Import configuration manager, Orpheus client, and models
from config.manager import ConfigManager
from core.orpheus_client import OrpheusClient
from models.queue import DownloadQueue
from models.search import SearchResultManager, SearchResultFormatter

# --- GUI Application using the Orpheus API ---
class OrpheusGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Orpheus-dl GUI Wrapper (API Mode)")
        self.geometry("900x750")

        # Initialize configuration manager
        self.config_manager = ConfigManager(os.path.dirname(__file__))

        # Initialize Orpheus client
        try:
            self.orpheus_client = OrpheusClient(os.path.dirname(__file__))
            self.orpheus = self.orpheus_client.get_orpheus_instance()
        except Exception as e:
            messagebox.showerror("Initialization Error", f"Could not initialize Orpheus: {e}")
            self.destroy()
            return

        # Get references to Orpheus types
        self.DownloadTypeEnum = self.orpheus_client.DownloadTypeEnum
        self.MediaIdentification = self.orpheus_client.MediaIdentification
        self.ModuleModes = self.orpheus_client.ModuleModes

        #Initialize third party modules dictionary
        self.third_party_modules = {
        self.ModuleModes.covers: '',
        self.ModuleModes.lyrics: '',
        self.ModuleModes.credits: ''}

        # Initialize models
        self.search_result_manager = SearchResultManager()
        self.download_queue = DownloadQueue()

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        self.create_search_tab()
        self.create_batch_tab()
        self.create_manual_tab()
        self.create_settings_tab()

    def create_search_tab(self):
        self.search_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.search_tab, text="Search & Select")

        search_params = ttk.LabelFrame(self.search_tab, text="Search Parameters")
        search_params.pack(fill=tk.X, padx=10, pady=10)

        ttk.Label(search_params, text="Module:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.E)
        installed_modules = self.config_manager.load_installed_modules()
        self.module_combo = ttk.Combobox(search_params, values=installed_modules, state="readonly", width=15)
        self.module_combo.grid(row=0, column=1, padx=5, pady=5)
        default_module = self.config_manager.load_default_module()
        if default_module and default_module in installed_modules:
            self.module_combo.set(default_module)
        elif installed_modules:
            self.module_combo.set(installed_modules[0])
        else:
            self.module_combo.set("")

        ttk.Label(search_params, text="Search Type:").grid(row=0, column=2, padx=5, pady=5, sticky=tk.E)
        self.search_type = tk.StringVar(value="track")
        search_type_menu = ttk.OptionMenu(search_params, self.search_type, "track", "track", "album", "artist")
        search_type_menu.grid(row=0, column=3, padx=5, pady=5)

        ttk.Label(search_params, text="Query:").grid(row=0, column=4, padx=5, pady=5, sticky=tk.E)
        self.query_entry = ttk.Entry(search_params, width=30)
        self.query_entry.grid(row=0, column=5, padx=5, pady=5)

        self.search_button = ttk.Button(search_params, text="Search", command=self.do_search)
        self.search_button.grid(row=0, column=6, padx=5, pady=5)
        self.query_entry.bind("<Return>", lambda event: self.do_search())


        results_frame = ttk.LabelFrame(self.search_tab, text="Search Results")
        results_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        self.results_listbox = tk.Listbox(results_frame, selectmode=tk.SINGLE)
        self.results_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(5,0), pady=5)
        scrollbar = ttk.Scrollbar(results_frame, orient=tk.VERTICAL, command=self.results_listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, padx=5, pady=5)
        self.results_listbox.config(yscrollcommand=scrollbar.set)
        self.results_listbox.bind("<Double-Button-1>", lambda event: self.add_selected_to_batch())

        self.add_to_batch_button = ttk.Button(self.search_tab, text="Add Selected to Batch", command=self.add_selected_to_batch)
        self.add_to_batch_button.pack(pady=5)

        self.search_output = scrolledtext.ScrolledText(self.search_tab, height=8)
        self.search_output.pack(fill=tk.BOTH, padx=10, pady=5)

    def create_batch_tab(self):
        self.batch_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.batch_tab, text="Batch Queue")

        queue_frame = ttk.LabelFrame(self.batch_tab, text="Download Queue")
        queue_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.queue_listbox = tk.Listbox(queue_frame)
        self.queue_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(5,0), pady=5)
        queue_scroll = ttk.Scrollbar(queue_frame, orient=tk.VERTICAL, command=self.queue_listbox.yview)
        queue_scroll.pack(side=tk.RIGHT, fill=tk.Y, padx=5, pady=5)
        self.queue_listbox.config(yscrollcommand=queue_scroll.set)
        self.queue_listbox.bind("<Delete>", lambda event: self.remove_selected_from_queue())

        btn_frame = ttk.Frame(self.batch_tab)
        btn_frame.pack(fill=tk.X, padx=10, pady=5)
        self.remove_queue_button = ttk.Button(btn_frame, text="Remove Selected", command=self.remove_selected_from_queue)
        self.remove_queue_button.pack(side=tk.LEFT, padx=5)
        self.download_batch_button = ttk.Button(btn_frame, text="Download Batch", command=self.download_batch)
        self.download_batch_button.pack(side=tk.LEFT, padx=5)
        self.clear_queue_button = ttk.Button(btn_frame, text="Clear Queue", command=self.clear_batch_queue)
        self.clear_queue_button.pack(side=tk.LEFT, padx=5)

        self.batch_log = scrolledtext.ScrolledText(self.batch_tab, height=10)
        self.batch_log.pack(fill=tk.BOTH, padx=10, pady=5)

    def create_manual_tab(self):
        self.manual_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.manual_tab, text="Manual Command Builder")

        ttk.Label(self.manual_tab, text="Command (e.g. py orpheus.py download qobuz track 52151405):").pack(anchor=tk.W, padx=10, pady=5)
        self.manual_cmd_entry = ttk.Entry(self.manual_tab, width=80)
        self.manual_cmd_entry.pack(padx=10, pady=5)
        self.manual_run_button = ttk.Button(self.manual_tab, text="Run Command", command=self.run_manual_command)
        self.manual_run_button.pack(padx=10, pady=5)

        self.manual_output = scrolledtext.ScrolledText(self.manual_tab, height=10)
        self.manual_output.pack(fill=tk.BOTH, padx=10, pady=5)

    def create_settings_tab(self):
        self.settings_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.settings_tab, text="Settings")

        config_frame = ttk.LabelFrame(self.settings_tab, text="OrpheusDL Configuration (config/settings.json)")
        config_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.config_text = scrolledtext.ScrolledText(config_frame, height=15)
        self.config_text.pack(fill=tk.BOTH, padx=5, pady=5)
        config_contents = self.config_manager.load_settings_json()
        self.config_text.insert(tk.END, config_contents)

        self.save_config_button = ttk.Button(config_frame, text="Save Config", command=self.save_config)
        self.save_config_button.pack(pady=5)

        default_frame = ttk.LabelFrame(self.settings_tab, text="Default Module Setting")
        default_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Label(default_frame, text="Select Default Module:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.E)
        installed_modules = self.config_manager.load_installed_modules()
        self.default_module_combo = ttk.Combobox(default_frame, values=installed_modules, state="readonly", width=15)
        self.default_module_combo.grid(row=0, column=1, padx=5, pady=5)
        current_default = self.config_manager.load_default_module()
        if current_default and current_default in installed_modules:
            self.default_module_combo.set(current_default)
        elif installed_modules:
            self.default_module_combo.set(installed_modules[0])
        else:
            self.default_module_combo.set("")

        third_party_frame = ttk.LabelFrame(self.settings_tab, text="Third‑Party Modules Settings")
        third_party_frame.pack(fill=tk.X, padx=10, pady=10)

        # Get the list of available modules.
        available_modules = self.config_manager.load_installed_modules()  # This returns a list like ["tidal", "deezer", ...]
        # Add "Default" to the top.
        available_modules.insert(0, "default")

        ttk.Label(third_party_frame, text="Covers Module:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.E)
        self.covers_module_combo = ttk.Combobox(third_party_frame, values=available_modules, state="readonly", width=15)
        self.covers_module_combo.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(third_party_frame, text="Lyrics Module:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.E)
        self.lyrics_module_combo = ttk.Combobox(third_party_frame, values=available_modules, state="readonly", width=15)
        self.lyrics_module_combo.grid(row=1, column=1, padx=5, pady=5)

        ttk.Label(third_party_frame, text="Credits Module:").grid(row=2, column=0, padx=5, pady=5, sticky=tk.E)
        self.credits_module_combo = ttk.Combobox(third_party_frame, values=available_modules, state="readonly", width=15)
        self.credits_module_combo.grid(row=2, column=1, padx=5, pady=5)
        
        # Read defaults from configuration:
        module_defaults = self.orpheus.settings['global']['module_defaults']

        # Set each combo box. If the config value is missing, default to "Default".
        self.covers_module_combo.set(module_defaults.get("covers", "default"))
        self.lyrics_module_combo.set(module_defaults.get("lyrics", "default"))
        self.credits_module_combo.set(module_defaults.get("credits", "default"))


        self.save_default_button = ttk.Button(default_frame, text="Save Default Module", command=self.save_default_module_setting)
        self.save_default_button.grid(row=0, column=2, padx=5, pady=5)

    def save_config(self):
        new_config = self.config_text.get(1.0, tk.END)
        if self.config_manager.save_settings_json(new_config):
            messagebox.showinfo("Config Saved", "Configuration saved successfully.")
        else:
            messagebox.showerror("Error", "Failed to save configuration.")

    def save_default_module_setting(self):
        new_default = self.default_module_combo.get().strip()
        if new_default:
            if self.config_manager.save_default_module(new_default):
                messagebox.showinfo("Default Module Saved", f"Default module set to '{new_default}'.")
            else:
                messagebox.showerror("Error", "Failed to save default module.")
        else:
            messagebox.showerror("Input Error", "Please select a default module.")
            
    def update_third_party_modules(self):
        # Get the main module name
        main_module = self.module_combo.get().strip()  # e.g., "tidal"
    
        # For each third-party module option, if "Default" is selected, use the main module.
        covers = self.covers_module_combo.get().strip()
        lyrics = self.lyrics_module_combo.get().strip()
        credits = self.credits_module_combo.get().strip()
    
        self.third_party_modules = {
            ModuleModes.covers: covers if covers != "default" else main_module,
            ModuleModes.lyrics: lyrics if lyrics != "default" else main_module,
            ModuleModes.credits: credits if credits != "default" else main_module
        }


    # --- API-based Search ---
    def do_search(self):
        self.results_listbox.delete(0, tk.END)
        self.search_output.delete(1.0, tk.END)
        self.search_result_manager.clear()

        module_name = self.module_combo.get().strip()
        search_type_str = self.search_type.get().strip()
        query = self.query_entry.get().strip()

        if not (module_name and search_type_str and query):
            messagebox.showerror("Input Error", "Please fill in module, search type, and query.")
            return

        try:
            module = self.orpheus.load_module(module_name)
            query_type = self.DownloadTypeEnum[search_type_str]
            results = module.search(query_type, query, limit=20)
            if not results:
                self.search_output.insert(tk.END, "No results found.\n")
                return

            # Store results using SearchResultManager
            self.search_result_manager.set_results(results, query_type, search_type_str)

            # Display results using SearchResultFormatter
            for i, (result, _) in enumerate(self.search_result_manager.get_all_results(), start=1):
                result_id = getattr(result, 'result_id', None)
                is_queued = self.download_queue.is_queued(result_id) if result_id else False
                display_text = SearchResultFormatter.format_result(result, search_type_str, i, is_queued)
                self.results_listbox.insert(tk.END, display_text)
                self.search_output.insert(tk.END, display_text + "\n")
        except Exception as e:
            messagebox.showerror("Search Error", f"An error occurred during search:\n{e}")

    def add_selected_to_batch(self):
        selection = self.results_listbox.curselection()
        if not selection:
            messagebox.showerror("Selection Error", "No result selected.")
            return
        index = selection[0]
        # Retrieve the tuple (result, media_type)
        result_tuple = self.search_result_manager.get_result(index)
        if result_tuple is None:
            messagebox.showerror("Selection Error", "Invalid result selected.")
            return

        selected_result, media_type = result_tuple

        # Try to add to queue
        if not self.download_queue.add_item(selected_result, media_type):
            messagebox.showinfo("Already Queued", "This item is already in the queue.")
            return

        # Create a display string for the queue listbox:
        display_text = f"{index+1}. {selected_result.name} (ID: {selected_result.result_id})"

        # Now, update the queue listbox so the user can see it:
        self.queue_listbox.insert(tk.END, display_text)
        self.refresh_search_listbox()
            
    def remove_selected_from_queue(self):
        selection = self.queue_listbox.curselection()
        if not selection:
            messagebox.showerror("Selection Error", "No item selected in the queue.")
            return
        index = selection[0]
        removed_item = self.download_queue.remove_item(index)
        if removed_item is not None:
            self.queue_listbox.delete(index)
            # Refresh the search results listbox to update any queued indicators.
            self.refresh_search_listbox()

    def refresh_search_listbox(self):
        self.results_listbox.delete(0, tk.END)
        search_type = self.search_result_manager.get_search_type()
        for i, (result, _) in enumerate(self.search_result_manager.get_all_results(), start=1):
            result_id = getattr(result, 'result_id', None)
            is_queued = self.download_queue.is_queued(result_id) if result_id else False
            display_text = SearchResultFormatter.format_result(result, search_type, i, is_queued)
            self.results_listbox.insert(tk.END, display_text)

    def clear_batch_queue(self):
        self.download_queue.clear()
        self.queue_listbox.delete(0, tk.END)
        self.refresh_search_listbox()

    # --- API-based Batch Download ---
    def download_batch(self):
        if len(self.download_queue) == 0:
            messagebox.showinfo("Queue Empty", "No items in the batch queue to download.")
            return
        self.batch_log.insert(tk.END, "Starting batch download...\n")
        self.download_batch_button.config(state=tk.DISABLED)
        threading.Thread(target=self.process_batch_queue, daemon=True).start()

    def process_batch_queue(self):
        download_path = "./downloads"
        module_name = self.module_combo.get().strip()
        self.update_third_party_modules()

        if not os.path.isdir(download_path):
            os.makedirs(download_path, exist_ok=True)
        # Set sdm to 'default' as required by core.py for non-playlists.
        sdm = module_name

        try:
            query_type = self.DownloadTypeEnum[self.search_type.get().strip()]
        except Exception as e:
            self.append_batch_log(f"Error determining media type: {e}\n")
            self.download_batch_button.config(state=tk.NORMAL)
            return

        for result, media_type in self.download_queue:
            # Use the media type stored with the result
            media_id = result.result_id  # or use an alternate attribute if needed
            module_name = self.module_combo.get().strip()
            media_ident = self.MediaIdentification(media_type=media_type, media_id=media_id)
            media_to_download = {module_name: [media_ident]}
            self.append_batch_log(f"Downloading: {result.name} (ID: {media_id})\n")
            try:
                orpheus_core_download = self.orpheus_client.get_core_download_function()
                orpheus_core_download(self.orpheus, media_to_download, self.third_party_modules, sdm, download_path)
                self.append_batch_log(f"Download complete for {result.name} (ID: {media_id}).\n")
            except Exception as e:
                self.append_batch_log(f"Error downloading {result.name}: {e}\n")
        self.append_batch_log("Batch processing complete.\n")
        self.download_batch_button.config(state=tk.NORMAL)
        self.download_queue.clear()
        self.queue_listbox.delete(0, tk.END)
        self.refresh_search_listbox()

    def append_batch_log(self, text):
        self.batch_log.insert(tk.END, text)
        self.batch_log.see(tk.END)

    # --- Manual Command Builder (using subprocess) ---
    def run_manual_command(self):
        cmd_text = self.manual_cmd_entry.get().strip()
        if not cmd_text:
            messagebox.showerror("Input Error", "Please enter a command.")
            return
        cmd = cmd_text.split()
        self.manual_output.insert(tk.END, f"Running: {' '.join(cmd)}\n")
        outq = queue.Queue()
        threading.Thread(target=self.run_subprocess_command, args=(cmd, outq), daemon=True).start()
        self.after(100, lambda: self.update_manual_output(outq))

    def run_subprocess_command(self, cmd, outq):
        # Fallback method using subprocess for manual commands.
        import subprocess
        try:
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
            for line in process.stdout:
                outq.put(line)
            process.stdout.close()
            process.wait()
        except Exception as e:
            outq.put(f"Error: {e}")

    def update_manual_output(self, outq):
        try:
            while True:
                line = outq.get_nowait()
                self.manual_output.insert(tk.END, line)
                self.manual_output.see(tk.END)
        except queue.Empty:
            if threading.active_count() > 1:
                self.after(100, lambda: self.update_manual_output(outq))
            else:
                self.manual_output.insert(tk.END, "\nCommand complete.\n")

if __name__ == "__main__":
    app = OrpheusGUI()
    app.mainloop()

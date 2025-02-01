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

# --- Import Orpheus-dl API via importlib to avoid namespace conflicts ---
# Load the main API from orpheus.py in the repository root.
orpheus_path = os.path.join(os.path.dirname(__file__), "orpheus.py")
spec = importlib.util.spec_from_file_location("orpheus_entry", orpheus_path)
orpheus_entry = importlib.util.module_from_spec(spec)
spec.loader.exec_module(orpheus_entry)

# Extract the required symbols.
Orpheus = orpheus_entry.Orpheus
DownloadTypeEnum = orpheus_entry.DownloadTypeEnum
MediaIdentification = orpheus_entry.MediaIdentification
ModuleModes = orpheus_entry.ModuleModes


# Load the core download function from orpheus/core.py.
core_path = os.path.join(os.path.dirname(__file__), "orpheus", "core.py")
spec_core = importlib.util.spec_from_file_location("orpheus_core", core_path)
orpheus_core = importlib.util.module_from_spec(spec_core)
spec_core.loader.exec_module(orpheus_core)
orpheus_core_download = orpheus_core.orpheus_core_download

# --- Helper functions for module and config management ---
def load_installed_modules():
    base_dir = os.path.dirname(__file__)
    modules_dir = os.path.join(base_dir, "modules")
    if not os.path.isdir(modules_dir):
        modules_dir = os.path.join(base_dir, "orpheus", "modules")
    if os.path.isdir(modules_dir):
        modules = [
            d for d in os.listdir(modules_dir)
            if os.path.isdir(os.path.join(modules_dir, d)) and d not in ("__pycache__", "example")
        ]
        return modules
    else:
        return []

def load_default_module():
    config_path = os.path.join(os.path.dirname(__file__), "default_module.txt")
    if os.path.exists(config_path):
        with open(config_path, "r") as f:
            return f.read().strip()
    return None

def save_default_module(module_name):
    config_path = os.path.join(os.path.dirname(__file__), "default_module.txt")
    try:
        with open(config_path, "w") as f:
            f.write(module_name.strip())
        return True
    except Exception as e:
        print(f"Error saving default module: {e}")
        return False

def load_config_file():
    base_dir = os.path.dirname(__file__)
    config_path = os.path.join(base_dir, "config", "settings.json")
    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            return f"Error reading config file: {e}"
    else:
        return "{}"

def save_config_file(new_contents):
    base_dir = os.path.dirname(__file__)
    config_dir = os.path.join(base_dir, "config")
    if not os.path.isdir(config_dir):
        os.makedirs(config_dir, exist_ok=True)
    config_path = os.path.join(config_dir, "settings.json")
    try:
        with open(config_path, "w", encoding="utf-8") as f:
            f.write(new_contents)
        return True
    except Exception as e:
        print(f"Error saving config file: {e}")
        return False

# --- GUI Application using the Orpheus API ---
class OrpheusGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Orpheus-dl GUI Wrapper (API Mode)")
        self.geometry("900x750")
        
        #Initialize third party modules dictionary
        self.third_party_modules = {
        ModuleModes.covers: '',
        ModuleModes.lyrics: '',
        ModuleModes.credits: ''}
        
        # Create a persistent Orpheus instance.
        try:
            self.orpheus = Orpheus(False)
        except Exception as e:
            messagebox.showerror("Initialization Error", f"Could not initialize Orpheus: {e}")
            self.destroy()
            return

        self.search_results = []   # Stores SearchResult objects.
        self.batch_queue = []      # Stores selected SearchResult objects.
        self.queued_ids = set()     #Set of result IDs that have been queued

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
        installed_modules = load_installed_modules()
        self.module_combo = ttk.Combobox(search_params, values=installed_modules, state="readonly", width=15)
        self.module_combo.grid(row=0, column=1, padx=5, pady=5)
        default_module = load_default_module()
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
        config_contents = load_config_file()
        self.config_text.insert(tk.END, config_contents)

        self.save_config_button = ttk.Button(config_frame, text="Save Config", command=self.save_config)
        self.save_config_button.pack(pady=5)

        default_frame = ttk.LabelFrame(self.settings_tab, text="Default Module Setting")
        default_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Label(default_frame, text="Select Default Module:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.E)
        installed_modules = load_installed_modules()
        self.default_module_combo = ttk.Combobox(default_frame, values=installed_modules, state="readonly", width=15)
        self.default_module_combo.grid(row=0, column=1, padx=5, pady=5)
        current_default = load_default_module()
        if current_default and current_default in installed_modules:
            self.default_module_combo.set(current_default)
        elif installed_modules:
            self.default_module_combo.set(installed_modules[0])
        else:
            self.default_module_combo.set("")
            
        third_party_frame = ttk.LabelFrame(self.settings_tab, text="Third‑Party Modules Settings")
        third_party_frame.pack(fill=tk.X, padx=10, pady=10)

        # Get the list of available modules.
        available_modules = load_installed_modules()  # This returns a list like ["tidal", "deezer", ...]
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
        if save_config_file(new_config):
            messagebox.showinfo("Config Saved", "Configuration saved successfully.")
        else:
            messagebox.showerror("Error", "Failed to save configuration.")

    def save_default_module_setting(self):
        new_default = self.default_module_combo.get().strip()
        if new_default:
            if save_default_module(new_default):
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
        self.search_results = []

        module_name = self.module_combo.get().strip()
        search_type_str = self.search_type.get().strip()
        query = self.query_entry.get().strip()

        if not (module_name and search_type_str and query):
            messagebox.showerror("Input Error", "Please fill in module, search type, and query.")
            return

        try:
            module = self.orpheus.load_module(module_name)
            query_type = DownloadTypeEnum[search_type_str]
            results = module.search(query_type, query, limit=20)
            if not results:
                self.search_output.insert(tk.END, "No results found.\n")
                return

            # Store results as tuples: (result, query_type)
            self.search_results = [(result, query_type) for result in results]
            for i, (result, _) in enumerate(self.search_results, start=1):
                # Build a detailed display string based on the search type.
                if search_type_str == "track":
                    title = getattr(result, "name", "Unknown Title")
                    artists = getattr(result, "artists", None)
                    # If artists is a list, join them; otherwise, default to "Unknown Artist"
                    if isinstance(artists, list) and artists:
                        artists_str = ", ".join(artists)
                    else:
                        artists_str = "Unknown Artist"
                    year = getattr(result, "year", "Unknown Year")
                    duration = getattr(result, "duration", 0)
                    minutes = duration // 60
                    seconds = duration % 60
                    duration_str = f"{minutes}:{seconds:02}"
                    explicit = getattr(result, "explicit", False)
                    explicit_str = "Explicit" if explicit else ""
                    additional = getattr(result, "additional", None)
                    additional_str = " ".join(additional) if (isinstance(additional, list) and additional) else ""
                    details = f" - {artists_str} (Year: {year}, Duration: {duration_str})"
                    if explicit_str:
                        details += f" [{explicit_str}]"
                    if additional_str:
                        details += f" [{additional_str}]"
                    display_text = f"{i}. {title}{details} (ID: {getattr(result, 'result_id', 'N/A')})"
                elif search_type_str == "album":
                    title = getattr(result, "name", "Unknown Album")
                    artists = getattr(result, "artists", None)
                    if isinstance(artists, list) and artists:
                        artists_str = ", ".join(artists)
                    else:
                        artists_str = "Unknown Artist"
                    year = getattr(result, "year", "Unknown Year")
                    additional = getattr(result, "additional", None)
                    additional_str = " ".join(additional) if (isinstance(additional, list) and additional) else ""
                    details = f" - {artists_str} (Year: {year})"
                    if additional_str:
                        details += f" [{additional_str}]"
                    display_text = f"{i}. {title}{details} (ID: {getattr(result, 'result_id', 'N/A')})"
                elif search_type_str == "artist":
                    title = getattr(result, "name", "Unknown Artist")
                    # Add any other relevant info if available, such as genre, etc.
                    details = ""
                    display_text = f"{i}. {title}{details} (ID: {getattr(result, 'result_id', 'N/A')})"
                else:
                    title = getattr(result, "name", "Unknown")
                    display_text = f"{i}. {title} (ID: {getattr(result, 'result_id', 'N/A')})"
    
                # Append "(Queued)" if this result's ID is in the queued set.
                if getattr(result, 'result_id', None) in self.queued_ids:
                    display_text += " (Queued)"
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
        selected_result, media_type = self.search_results[index]
        result_id = selected_result.result_id
        # Check if already in the queue:
        if (selected_result, media_type) in self.batch_queue or result_id in self.queued_ids:
            messagebox.showinfo("Already Queued", "This item is already in the queue.")
            return
        #Add to internal queue:
        self.batch_queue.append((selected_result, media_type))
        self.queued_ids.add(result_id)
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
        removed_item = self.batch_queue.pop(index)  # (result, media_type)
        result_id = removed_item[0].result_id
        if result_id in self.queued_ids:
            self.queued_ids.remove(result_id)
        self.queue_listbox.delete(index)
        # Refresh the search results listbox to update any queued indicators.
        self.refresh_search_listbox()
        
    def refresh_search_listbox(self):
        self.results_listbox.delete(0, tk.END)
        for i, (result, _) in enumerate(self.search_results, start=1):
            display_text = f"{i}. {result.name} (ID: {result.result_id})"
            if result.result_id in self.queued_ids:
                display_text += " (Queued)"
            self.results_listbox.insert(tk.END, display_text)

    def clear_batch_queue(self):
        self.batch_queue.clear()
        self.queue_listbox.delete(0, tk.END)

    # --- API-based Batch Download ---
    def download_batch(self):
        if not self.batch_queue:
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
            query_type = DownloadTypeEnum[self.search_type.get().strip()]
        except Exception as e:
            self.append_batch_log(f"Error determining media type: {e}\n")
            self.download_batch_button.config(state=tk.NORMAL)
            return

        for result, media_type in self.batch_queue:
            # Use the media type stored with the result
            media_id = result.result_id  # or use an alternate attribute if needed
            module_name = self.module_combo.get().strip()
            media_ident = MediaIdentification(media_type=media_type, media_id=media_id)
            media_to_download = {module_name: [media_ident]}
            self.append_batch_log(f"Downloading: {result.name} (ID: {media_id})\n")
            try:
                orpheus_core_download(self.orpheus, media_to_download, self.third_party_modules, sdm, download_path)
                self.append_batch_log(f"Download complete for {result.name} (ID: {media_id}).\n")
            except Exception as e:
                self.append_batch_log(f"Error downloading {result.name}: {e}\n")
        self.append_batch_log("Batch processing complete.\n")
        self.download_batch_button.config(state=tk.NORMAL)
        self.batch_queue.clear()
        self.queue_listbox.delete(0, tk.END)

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

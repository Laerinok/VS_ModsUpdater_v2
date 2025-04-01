#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
This module is designed to format and export mod information into a JSON file, specifically creating a modlist from the data collected about Vintage Story mods. It handles the organization of mod details and saves them in a structured JSON format.

Key functionalities include:
- Formatting mod data into a structured dictionary, including mod name, version, ModId, side, description, and URLs.
- Sorting the mods by their ModId for consistent ordering in the JSON output.
- Saving the formatted mod data into a JSON file named 'modlist.json' in a specified directory.
- Ensuring the output directory exists before saving the JSON file.
- Handling potential file permission errors and logging relevant information.
- Caching the formatted mod data in a global cache for potential future use.

"""
__author__ = "Laerinok"
__version__ = "2.0.0-dev3"
__date__ = "2025-04-01"


from pathlib import Path
import json
import global_cache
import logging


def save_json(data, filename):
    # Ensure the directory exists
    filename.parent.mkdir(parents=True, exist_ok=True)
    try:
        with open(filename, 'w', encoding='utf-8') as json_file:
            json.dump(data, json_file, indent=4, ensure_ascii=False)
        print(f"A modlist has been exported in JSON format to the following location: {global_cache.config_cache['Backup_Mods']['modlist_folder']}")
        logging.info(f"{filename} has been created successfully.")
    except PermissionError:
        logging.error(f"Error: No write permission for {filename}. Try running as administrator.")
    except Exception as e:
        logging.error(f"Unexpected error while saving {filename}: {e}")


def format_mods_data(mods_data):
    mods_data.sort(key=lambda mod: mod["ModId"].lower() if mod["ModId"] else "")
    # Create a new list for the formatted mods
    formatted_mods = []

    for mod_data in mods_data:
        # Create a dictionary for each formatted mod
        formatted_mod = {
            "Name": mod_data.get("Name", ""),
            "Version": mod_data.get("Local_Version", ""),
            "ModId": mod_data.get("ModId", ""),
            "Side": mod_data.get("Side", ""),
            "Description": mod_data.get("Description", ""),
            "url_mod": mod_data.get("Mod_url", "Local mod"),
            "url_download": mod_data.get("Latest_version_mod_url", "Local mod")
        }
        # Append the formatted mod to the list
        formatted_mods.append(formatted_mod)

    # Create the final data structure
    final_data = {
        "Mods": formatted_mods
    }

    # Save json data to cache
    global_cache.modinfo_json_cache = final_data
    # Save data to modlist.json
    filename = (Path(global_cache.config_cache['Backup_Mods']["modlist_folder"]) / 'modlist.json').resolve()
    save_json(final_data, filename)


if __name__ == "__main__":
    pass

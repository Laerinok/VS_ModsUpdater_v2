#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2024  Laerinok
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

__author__ = "Laerinok"
__date__ = "2025-10-03"  # Last update


# utils.py

import datetime
import json
import logging
import random
import re
import sys
import zipfile
from pathlib import Path
from typing import Any
from urllib.parse import urlparse, parse_qs, unquote
import shutil
import os

import html2text
from packaging.version import Version, InvalidVersion
from rich import print
from rich.console import Console
from rich.prompt import Prompt

import cli
import config
import global_cache
import lang
from enum import Enum
from http_client import HTTPClient

console = Console()

timeout = global_cache.config_cache["Options"].get("timeout", 10)
client = HTTPClient()

class ModType(Enum):
    ZIP = "zip"
    CS = "cs"
    DIR = "dir"

# #### For test and debug ####
def print_dict(dictionary):
    """Print a dictionary in a structured format."""
    for key, value in dictionary.items():
        print(f"{key}: {value}")


def list_display(my_list):
    """Display each element from the list"""
    for element in my_list:
        print(element)


def print_config_cache():
    """ Print the global_cache"""
    print(global_cache.config_cache)


def print_language_cache():
    """ Print the global_cache"""
    print(global_cache.language_cache)


def print_mods_data():
    """ Print the global_cache"""
    print(global_cache.mods_data)

# #### END ####


def setup_directories(path_dir):
    if not path_dir.exists():
        path_dir.mkdir(parents=True, exist_ok=True)


def prompt_yes_no(prompt_message: str, default: bool = True, **kwargs: Any) -> bool:
    """
    Prompts the user for a Yes/No question using manual validation to ensure
    both localized characters (from the 'yes'/'no' keys) and universal 'y'/'n'
    characters are accepted (case-insensitive).

    This version bypasses rich.prompt.Prompt validation for cross-language robustness.
    """
    # 1. Get localized characters (extract the first character from the translation)
    yes_word = lang.get_translation("yes").strip().lower()
    no_word = lang.get_translation("no").strip().lower()

    # Extract the first character for validation and display
    yes_local_char = yes_word[0]
    no_local_char = no_word[0]

    # 2. Define ALL acceptable inputs
    yes_inputs = {yes_local_char, 'y'}
    no_inputs = {no_local_char, 'n'}

    # 3. Determine display and default value
    display_choices = [yes_local_char, no_local_char]
    default_char = no_local_char if not default else yes_local_char

    # 4. Loop until valid input is given
    while True:
        # Construct the final prompt string with the default value displayed
        prompt_str = f"{prompt_message} ({'/'.join(display_choices)}) [{default_char}]: "

        # *** CRITICAL CHANGE: Use console.input() for raw input! ***
        # This bypasses all rich.prompt.Prompt validation logic that was failing.
        try:
            # We use 'console.input' to get the raw string.
            raw_input = console.input(prompt_str, **kwargs)
        except EOFError:
            # Handle Ctrl+D/Ctrl+Z case gracefully
            raw_input = ""
        except KeyboardInterrupt:
            # Handle Ctrl+C gracefully
            print("[indian_red1]Aborting prompt...[/indian_red1]")
            return False  # Assuming No/Exit on interruption

        normalized_input = raw_input.strip().lower()

        # 5. Handle empty input (accepting the default)
        if not normalized_input:
            normalized_input = default_char

        # 6. Validation
        if normalized_input in yes_inputs:
            return True
        elif normalized_input in no_inputs:
            return False
        else:
            # Error message using rich print
            all_valid_chars = sorted(list(yes_inputs.union(no_inputs)))
            print(
                f"[indian_red1]Please select one of the available options: {', '.join(all_valid_chars)}[/indian_red1]")


def prompt_choice(prompt_message: str, choices: list[str], default: str,
                  **kwargs: Any) -> str:
    """
    Prompts the user to choose from a list of strings.
    Handles case-insensitivity and strips spaces after input is received.

    Args:
        prompt_message (str): The question to ask.
        choices (list[str]): The list of valid options.
        default (str): The default choice.
        **kwargs: Additional arguments for rich.prompt.Prompt.ask (e.g., show_choices).

    Returns:
        str: The selected, lowercased, and stripped choice.
    """
    raw_input = Prompt.ask(
        prompt_message,
        choices=choices,
        default=default,
        **kwargs
    )

    # Normalize the input (lowercase and strip spaces) on return
    return raw_input.strip().lower()


def check_mods_directory(mods_dir):
    mods_dir_path = Path(mods_dir).resolve()

    # Check if the directory is empty
    if not any(mods_dir_path.iterdir()):
        console.print(f'{lang.get_translation("utils_warning_mods_directory_empty").format(mods_dir_path=mods_dir_path)}')
        logging.error(f"Warning: The Mods directory {mods_dir_path} is empty!")
        exit_program(extra_msg="Empty mods folder")

    found_valid_file = False

    # Loop through all files in the 'Mods' directory
    for item in mods_dir_path.iterdir():
        if item.is_dir():
            if (item / 'modinfo.json').exists():
                found_valid_file = True
            else:
                print(f"{lang.get_translation('utils_warning_directory_in_mods_folder').format(item_name=item.name)}")
                logging.warning(f"Warning: Directory found in Mods folder without modinfo.json: {item.name}.")
        elif item.suffix.lower() in ['.zip', '.cs']:
            found_valid_file = True  # We found at least one valid file

    # If no valid files were found, exit the program
    if not found_valid_file:
        exit_program(extra_msg=lang.get_translation("utils_no_valid_mod_files_found"))


def validate_workers():
    """
    Validates and returns the adjusted number of workers based on user input or configuration.

    This function retrieves the desired number of workers from command-line arguments or the configuration file,
    ensuring it falls within the allowed range defined by 'min_workers_limit' and 'max_workers_limit'.

    :return: The validated and adjusted number of workers.
    """
    args = cli.parse_args()
    config_max_workers = int(global_cache.config_cache["Options"]["max_workers"])
    # Define the maximum workers allowed
    max_workers_limit = 10
    min_workers_limit = 1  # Define the minimum workers allowed

    # Use the --max-workers argument if provided, otherwise use the config value
    user_max_workers = args.max_workers if args.max_workers is not None else config_max_workers

    # Test to ensure user_max_workers is an integer
    if not isinstance(user_max_workers, int):
        try:
            user_max_workers = int(user_max_workers)  # Try to convert to integer
        except (ValueError, TypeError) as e:
            logging.error(f"Invalid input for max_workers: {e}")
            print(lang.get_translation("utils_error_invalid_max_workers"))
            return min_workers_limit  # Return the minimum workers limit, or raise an error

    # If the user has set max_workers, validate it
    if user_max_workers:
        # Never exceed the max_workers limit and always use at least 1 worker
        return max(min(user_max_workers, max_workers_limit), min_workers_limit)
    else:
        # If the user hasn't set max_workers, use the defaut max_workers
        return min_workers_limit  # We return an integer value for consistency


def get_random_headers():
    """Returns a random User-Agent from the predefined list."""
    return {"User-Agent": random.choice(global_cache.config_cache['USER_AGENTS'])}


def is_zip_valid(zip_path):
    """Checks if a zip file is valid and not corrupted."""
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.testzip()  # Tests the integrity of the zip file
        return True
    except (zipfile.BadZipFile, zipfile.LargeZipFile):
        return False


def normalize_keys(d):
    """Normalize the keys of a dictionary to lowercase"""
    if isinstance(d, dict):
        return {k.lower(): normalize_keys(v) for k, v in d.items()}
    elif isinstance(d, list):
        return [normalize_keys(i) for i in d]
    else:
        return d


def sanitize_json_data(data):
    """Recursively replace None values with empty strings."""
    if isinstance(data, dict):
        return {k: sanitize_json_data(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [sanitize_json_data(item) for item in data]
    elif data is None:
        return ""
    return data


def fix_json(json_data):
    """Fix the JSON string by removing comments, trailing commas, and ignoring the 'website' key."""

    # Remove single-line comments (lines starting with //)
    json_data = re.sub(r'^\s*//[^\n]*$', '', json_data, flags=re.MULTILINE)

    # Remove trailing commas before closing braces/brackets
    json_data = re.sub(r',\s*([}\]])', r'\1', json_data)

    # Try to load the JSON string into a Python dictionary
    try:
        data = json.loads(json_data)
    except json.JSONDecodeError as e:
        logging.error(f"Error parsing JSON: {e}")
        return "Error: Invalid JSON data"

    # Sanitize the data: replace None with empty strings
    data = sanitize_json_data(data)

    # Remove the 'website' key if it exists
    if "website" in data:
        del data["website"]

    # Convert the dictionary back into a formatted JSON string
    json_data_fixed = json.dumps(data, indent=2)
    return json_data_fixed

class VersionCompareState(Enum):
    LOCAL_VERSION_BEHIND = "local_version_behind"
    IDENTICAL_VERSION = "identical_version"
    LOCAL_VERSION_AHEAD = "local_version_ahead"


def version_compare(local_version, online_version) -> VersionCompareState:
    """
    Compares the local version with the online version.
    Args:
        local_version (str): The local version string.
        online_version (str): The online version string.
    Returns:
        VersionCompareState: The comparison result.
    """
    # Compare local and online version
    if Version(local_version) < Version(online_version):
        return VersionCompareState.LOCAL_VERSION_BEHIND
    elif Version(local_version) > Version(online_version):
        return VersionCompareState.LOCAL_VERSION_AHEAD
    else:
        return VersionCompareState.IDENTICAL_VERSION


def is_valid_version(version_string):
    """
    Validate if the version string matches the standard version format.
    Args:
        version_string (str): The version string to validate.
    Returns:
        bool: True if valid, False otherwise.
    """
    try:
        # Try to create a Version object.
        Version(version_string)
        return True
    except InvalidVersion:
        # If the version is not valid, an InvalidVersion exception will be raised.
        return False


def complete_version(version_string):
    """Ensure version has three components (major.minor.patch)."""
    parts = version_string.split(".")
    while len(parts) < 3:  # Add missing components
        parts.append("0")
    return ".".join(parts)


# Retrieve the last game version
def get_latest_game_version(url_api='https://mods.vintagestory.at/api'):
    gameversions_api_url = f'{url_api}/gameversions'
    response = client.get(gameversions_api_url)
    response.raise_for_status()  # Checks that the request was successful (status code 200)
    gameversion_data = response.json()  # Retrieves JSON content
    logging.info(f"Game version data retrieved.")
    # Retrieve the latest version
    return gameversion_data['gameversions'][-1]['name']


def extract_filename_from_url(url):
    # Parse the URL and get the query parameters
    parsed_url = urlparse(url)
    query_params = parse_qs(parsed_url.query)
    # Extract the filename from the 'dl' parameter
    filename = query_params.get('dl', [None])[0]
    return filename


def check_excluded_mods(mod_filename: str, mod_name: str) -> bool:
    """
    Checks if a mod is explicitly excluded by the user configuration (config.ini).

    Args:
        mod_filename (str): The filename of the mod (e.g., ModName.zip).
        mod_name (str): The friendly name of the mod (from modinfo.json).

    Returns:
        bool: True if the mod is explicitly excluded by the user, False otherwise.
    """
    excluded_list = global_cache.config_cache.get("Mod_Exclusion", {}).get("mods",
                                                                           "").split(
        ", ")

    excluded_filenames = {name.strip() for name in excluded_list if name.strip()}

    if mod_filename in excluded_filenames:
        reason_message = lang.get_translation("utils_exclusion_reason_user_config")

        global_cache.mods_data["excluded_mods"].append({
            "Filename": mod_filename,
            "Name": mod_name,
            "Reason": reason_message
        })
        logging.info(f"Mod excluded by user configuration: {mod_name}")
        return True

    return False

def backup_mods(mods_to_backup):
    """
    Create a backup of mods before download and manage a retention policy.
    Handles files (zip, cs) and directories.
    """
    max_backups = int(global_cache.config_cache['Backup_Mods']['max_backups'])
    backup_folder = global_cache.config_cache['BACKUP_FOLDER']

    setup_directories(backup_folder)

    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    backup_path = backup_folder / f"backup_{timestamp}.zip"

    with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as backup_zip:
        for mod in mods_to_backup:
            mod_path = Path(mod.get("Path"))
            mod_type_str = mod.get("Type")
            mod_type = ModType(mod_type_str) if mod_type_str else None

            if not mod_path.exists():
                logging.warning(f"Path for mod {mod.get('Name')} not found at {mod_path}, skipping backup.")
                continue

            if mod_type in [ModType.ZIP, ModType.CS]:
                backup_zip.write(mod_path, arcname=mod_path.name)
                logging.info(f"Backed up file: {mod_path.name}")
            elif mod_type == ModType.DIR:
                for file_path in mod_path.rglob('*'):
                    arcname = file_path.relative_to(mod_path.parent)
                    backup_zip.write(file_path, arcname=arcname)
                logging.info(f"Backed up directory: {mod_path.name}")

    logging.info(f"Backup of mods completed: {backup_path}")

    # Cleanup old backups
    if max_backups > 0:
        backups = sorted(backup_folder.glob("backup_*.zip"),
                         key=lambda p: p.stat().st_mtime,
                         reverse=True)
        if len(backups) > max_backups:
            for old_backup in backups[max_backups:]:
                old_backup.unlink()
                logging.info(f"Deleted old backup: {old_backup}")

def get_default_icon_binary():
    """
    Loads and returns the binary data of the default icon ('assets/no_icon.png').
    """
    default_icon_path = Path(config.APPLICATION_PATH) / 'assets' / 'no_icon.png'
    if default_icon_path.exists():
        with open(default_icon_path, 'rb') as f:
            return f.read()
    else:
        logging.debug(f"Default icon 'no_icon.png' not found at {default_icon_path}.")
        return None

def get_icon_binary(path, mod_type):
    """Gets the binary data of modicon.png from a mod path (zip or directory)."""
    mod_type_enum = ModType(mod_type) if isinstance(mod_type, str) else mod_type
    icon_path = 'modicon.png'
    try:
        if mod_type_enum == ModType.DIR:
            icon_file = path / icon_path
            if icon_file.exists():
                with open(icon_file, 'rb') as f:
                    return f.read()
        elif mod_type_enum == ModType.ZIP:
            with zipfile.ZipFile(path, 'r') as zip_ref:
                if icon_path in zip_ref.namelist():
                    with zip_ref.open(icon_path) as icon_file:
                        return icon_file.read()
    except Exception as e:
        logging.warning(f"Could not read icon for {path}: {e}")
    return None

def escape_rich_tags(text):
    return text.replace("[", r"\[").replace("]", r"\]")


def convert_html_to_markdown(html_content):
    """
    Convert HTML content to Markdown.
    """
    converter = html2text.HTML2Text()
    converter.ignore_links = False  # Keep links
    converter.ignore_images = False  # Keep images
    converter.body_width = 0  # Prevent forced line breaks
    return converter.handle(html_content)


def exit_program(msg=None, extra_msg=None, do_exit=True):
    """Exits the program with an optional message."""
    if msg is None:
        import lang
        msg = lang.get_translation("utils_prg_terminated")

    if extra_msg:
        msg += " " + extra_msg

    logging.info("Program terminated")
    print(f"\n\t*** [indian_red1]{msg}[/indian_red1] ***")

    if do_exit:
        sys.exit()

def download_file(url, destination_path):
    """
    Download the file from the given URL and save it to the destination path.
    Implements error handling and additional security measures.
    """
    if not config.download_enabled:
        logging.info(f"Skipping download - for TEST")
        return  # Skip download if disabled

    mod_filename = Path(destination_path).name
    try:
        decoded_url = unquote(url)

        response = client.get(decoded_url, stream=True, timeout=int(
            global_cache.config_cache["Options"]["timeout"]))

        if response is None:
            raise Exception("HTTPClient reached max retries or returned None.")

        response.raise_for_status()

    except Exception as e:
        logging.error(f"FATAL DOWNLOAD ERROR for {mod_filename} ({url}): {e}")
        print(
            f"[bold red]{lang.get_translation('auto_download_failed')} ({mod_filename}): {escape_rich_tags(str(e))}[/bold red]")
        return

    # Get the total size of the file (if available)
    total_size = int(response.headers.get('content-length', 0))

    if total_size == 0:
        print(f"[bold indian_red1]{lang.get_translation('auto_file_size_unknown')}[/bold indian_red1]")

    with open(destination_path, 'wb') as file:
        for data in response.iter_content(chunk_size=1024):
            file.write(data)

    logging.info(f"Download completed: {destination_path}")


def update_mod_and_handle_files(mod, mods_path):
    """
    Handles the update process for a single mod: download, remove, and install.
    Backup is handled separately.
    """
    mod_type_str = mod.get("Type")
    mod_type = ModType(mod_type_str) if mod_type_str else None
    original_path = Path(mod.get("Path"))
    mod_name = mod.get("Name")

    # 1. Download new version to a temporary file
    url = mod['download_url']
    temp_filename = "temp_" + extract_filename_from_url(os.path.basename(url))
    temp_download_path = mods_path / temp_filename
    try:
        download_file(url, temp_download_path)
        if not temp_download_path.exists() or temp_download_path.stat().st_size == 0:
            raise Exception("Download resulted in an empty or missing file.")
        logging.info(f"Successfully downloaded new version for {mod_name} to {temp_download_path}")
    except Exception as e:
        logging.error(f"Download failed for {mod_name}, aborting update. Error: {e}")
        if temp_download_path.exists():
            os.remove(temp_download_path)
        raise

    # 2. Remove old mod
    try:
        if mod_type == ModType.DIR:
            shutil.rmtree(original_path)
        else:  # zip or cs
            os.remove(original_path)
        logging.info(f"Successfully removed old version of {mod_name}")
    except Exception as e:
        logging.error(f"Failed to remove old version of {mod_name}, aborting update. Error: {e}")
        os.remove(temp_download_path)
        raise

    # 3. Install new mod
    try:
        if mod_type == ModType.DIR:
            original_path.mkdir()
            with zipfile.ZipFile(temp_download_path, 'r') as zip_ref:
                zip_ref.extractall(original_path)
            logging.info(f"Successfully installed new version of {mod_name} directory")
        else:  # zip or cs
            final_filename = extract_filename_from_url(os.path.basename(url))
            final_path = mods_path / final_filename
            shutil.move(str(temp_download_path), str(final_path))
            logging.info(f"Successfully installed new version of {mod_name} file")
            mod['New_Filename'] = final_filename
            mod['New_Path'] = str(final_path)

    except Exception as e:
        logging.critical(f"Failed to install new version of {mod_name} after removing the old one. Mod is broken. Error: {e}")
        raise
    finally:
        if temp_download_path.exists():
            os.remove(temp_download_path)

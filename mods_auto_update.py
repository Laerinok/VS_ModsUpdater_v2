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

"""
This module automates the process of checking for and updating Vintage Story mods. It compares local mod versions with the latest available versions, downloads updates, and manages backups.

Key functionalities include:
- Checking for mod updates by comparing local and latest available versions.
- Fetching changelogs for updated mods.
- Backing up mods before updating to prevent data loss.
- Downloading updated mods using multithreading for efficiency.
- Managing backup retention policies to avoid excessive disk usage.
- Providing detailed logging and user feedback on the update process.
- Handling excluded mods to skip them during the update process.
- Erasing old files before downloading the new ones.
- Resume the list of the mods updated with the changelog.

"""
__author__ = "Laerinok"
__version__ = "2.0.0-dev3"
__date__ = "2025-04-02"  # Last update


# mods_auto_update.py


import datetime
import logging
import os
import zipfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from rich import print
from rich.console import Console
from rich.progress import Progress

import config
import fetch_changelog
import global_cache
from http_client import HTTPClient
from utils import version_compare, check_excluded_mods, \
    setup_directories, extract_filename_from_url, calculate_max_workers

timeout = global_cache.config_cache["Options"].get("timeout", 10)
client = HTTPClient(timeout=timeout)
console = Console()

# Variable to enable/disable the download - for my test
download_enabled = True  # Set to False to disable downloads


def get_mods_to_update(mods_data):
    """
    Check for mods that need updates.

    - If Local_Version < mod_latest_version_for_game_version, the mod needs an update.
    - If the Filename is in excluded_mods, skip the mod.
    - Returns a list of mods that require updates.
    """
    # Extract filenames from excluded_mods to compare correctly
    check_excluded_mods()
    excluded_filenames = [mod['Filename'] for mod in mods_data.get("excluded_mods", [])]

    # Initialize a list to store the mods that need to be updated
    mods_to_update = []

    with Progress() as progress:
        task = progress.add_task("[cyan]Checking mods for updates...",
                                 total=len(mods_data.get("installed_mods", [])))

        # Use ThreadPoolExecutor to parallelize the changelog retrieval
        with ThreadPoolExecutor() as executor:
            futures = []

            for mod in mods_data.get("installed_mods", []):
                futures.append(executor.submit(process_mod, mod, excluded_filenames,
                                               mods_to_update))

            for future in as_completed(futures):
                future.result()  # Wait for completion of each task
                progress.update(task, advance=1)  # Update the progress bar

    # Sort mods_to_update before returning
    mods_to_update.sort(key=lambda mod: mod["Name"].lower())  # Sort by Name
    mods_data["mods_to_update"] = mods_to_update
    return mods_to_update


def process_mod(mod, excluded_filenames, mods_to_update):
    """
    Process each mod to check if it needs an update and fetch its changelog.
    """
    try:
        # Log mod Filename to verify
        logging.info(f"Processing mod: {mod['Name']} - Filename: {mod['Filename']}")

        # Skip the mod if its Filename is in excluded_filenames
        if mod['Filename'] in excluded_filenames:
            logging.info(
                f"Skipping excluded mod: {mod['Name']} - Filename: {mod['Filename']}")
            return  # Skip this mod if it's in the excluded list

        # Proceed with the version comparison
        if mod.get("mod_latest_version_for_game_version"):
            mod_update = version_compare(mod["Local_Version"],
                                         mod["mod_latest_version_for_game_version"])
        else:
            mod_update = False

        if mod_update:
            mod_name = mod['Name']
            mod_assetid = mod['AssetId']
            modversion = mod['mod_latest_version_for_game_version']
            changelog = fetch_changelog.get_raw_changelog(mod_name, mod_assetid,
                                                          modversion)
            mods_to_update.append({
                "Name": mod['Name'],
                "Old_version": mod['Local_Version'],
                "New_version": mod['mod_latest_version_for_game_version'],
                "Changelog": changelog,
                "Filename": mod['Filename'],
                "url_download": mod['Latest_version_mod_url']})

    except ValueError:
        # Skip mods with invalid version formats
        logging.warning(f"Invalid version format for mod: {mod['Name']}")
        return


def backup_mods(mods_to_backup):
    """
    Create a backup of the ZIP mods before download and manage a retention policy.
    """
    max_backups = int(global_cache.config_cache['Backup_Mods']['max_backups'])
    backup_folder_name = global_cache.config_cache['Backup_Mods']['backup_folder']
    backup_folder = (Path(global_cache.config_cache['APPLICATION_PATH']) / backup_folder_name).resolve()

    # Ensure the backup directory exists
    setup_directories(backup_folder)

    # Create a unique backup name with timestamp
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    backup_path = backup_folder / f"backup_{timestamp}.zip"

    modspaths = global_cache.config_cache['ModsPath']['path']

    # Create the ZIP archive
    with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as backup_zip:
        for mod_key in mods_to_backup:
            zip_filename = Path(modspaths) / mod_key
            if zip_filename.is_file():
                backup_zip.write(zip_filename, arcname=zip_filename.name)

    logging.info(f"Backup of mods completed: {backup_path}")

    # Cleanup old backups if the maximum limit is exceeded
    backups = sorted(backup_folder.glob("backup_*.zip"),
                     key=lambda p: p.stat().st_mtime,
                     reverse=True)
    if len(backups) > max_backups:
        for old_backup in backups[max_backups:]:
            old_backup.unlink()
            logging.info(f"Deleted old backup: {old_backup}")


def download_file(url, destination_path, progress_bar, task):
    """
    Download the file from the given URL and save it to the destination path with a progress bar using Rich.
    Implements error handling and additional security measures.
    """
    if not download_enabled:
        logging.info(f"Skipping download for: {url}")
        return  # Skip download if disabled

    response = client.get(url, stream=True, timeout=int(global_cache.config_cache["Options"]["timeout"]))
    response.raise_for_status()  # Will raise an HTTPError for bad responses (4xx, 5xx)

    # Get the total size of the file (if available)
    total_size = int(response.headers.get('content-length', 0))

    if total_size == 0:
        print("[bold red]Warning: The file size is unknown or zero. Download may not complete properly.[/bold red]")

    with open(destination_path, 'wb') as file:
        for data in response.iter_content(chunk_size=1024):
            file.write(data)
            progress_bar.update(task, advance=len(data))  # Update progress bar in the same task

    logging.info(f"Download completed: {destination_path}")


def download_mods_to_update(mods_data):
    """
    Download all mods that require updates using multithreading with a progress bar for each download.
    """
    # Initialize the Rich Progress bar
    with Progress() as progress:
        # Create a single task for all downloads
        task = progress.add_task("[cyan]Downloading mods...", total=len(mods_data))

        # Create a thread pool executor for parallel downloads
        max_workers = calculate_max_workers()
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = []
            for mod in mods_data:
                url = mod['url_download']
                # Extract the filename from the URL (using the name from the URL)
                filename = os.path.basename(url)
                filename = extract_filename_from_url(filename)

                # Set the destination folder path
                destination_folder = Path(global_cache.config_cache['ModsPath']['path']).resolve()
                destination_path = destination_folder / filename  # Combine folder path and filename

                # Submit download tasks to the thread pool with progress bar
                futures.append(executor.submit(download_file, url, destination_path, progress, task))

                # Erase old file
                file_to_erase = mod['Filename']
                filename_value = Path(global_cache.config_cache['ModsPath']['path']) / file_to_erase
                filename_value = filename_value.resolve()
                if not download_enabled:
                    logging.info(f"Skipping download for: {url}")
                    break  # Skip download (and erase) if disabled
                try:
                    os.remove(filename_value)
                    logging.info(f"Old file {file_to_erase} has been deleted successfully.")
                except PermissionError:
                    logging.error(
                        f"PermissionError: Unable to delete {file_to_erase}. You don't have the required permissions.")
                except FileNotFoundError:
                    logging.error(
                        f"FileNotFoundError: The file {file_to_erase} does not exist.")
                except Exception as e:
                    logging.error(
                        f"An unexpected error occurred while trying to delete {file_to_erase}: {e}")

                # Update the progress for each mod with mod name or file name
                mod_name = mod['Name']  # Get the mod name from the data
                progress.update(task, advance=1, description=f"[cyan]Downloading {mod_name}")

            # Wait for all downloads to finish
            for future in futures:
                future.result()  # This will raise an exception if something went wrong


def resume_mods_updated():
    # app_log.txt
    print(f"\nFollowings mods have been updated:")
    logging.info("Followings mods have been updated (More details in updated_mods_changelog.txt):")
    for mod in global_cache.mods_data.get('mods_to_update'):
        print(f"- [green]{mod['Name']} (v{mod['Old_version']} to v{mod['New_version']}):[/green]")
        print(f"[bold][yellow]{mod['Changelog']}[/bold][yellow]\n")
        logging.info(f"\t- {mod['Name']} (v{mod['Old_version']} to v{mod['New_version']})")

    # mod_updated_log.txt
    mod_updated_logger = config.configure_mod_updated_logging()

    for mod in global_cache.mods_data.get('mods_to_update', []):
        name_version = f"*** {mod['Name']} (v{mod['Old_version']} to v{mod['New_version']}) ***"
        mod_updated_logger.info("================================")
        mod_updated_logger.info(name_version)
        if mod.get('Changelog'):
            # Formatage simple pour rendre le changelog lisible
            changelog = mod['Changelog']

            # Si tu veux organiser par section, tu peux ajouter des sauts de ligne ou autres
            changelog = changelog.replace("\n",
                                          "\n\t")  # Ajouter une tabulation pour chaque nouvelle ligne
            mod_updated_logger.info(f"Changelog:\n\t{changelog}")

        mod_updated_logger.info("\n\n")  # Ligne vide pour espacement


if __name__ == "__main__":
    pass

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
__version__ = "2.3.0"
__date__ = "2025-08-24"  # Last update


# mods_auto_update.py


import logging
import os
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
import urllib.parse

from rich import print
from rich.console import Console
from rich.progress import Progress, TextColumn, BarColumn, TimeElapsedColumn

import config
import global_cache
import lang
from http_client import HTTPClient
from utils import extract_filename_from_url, validate_workers, escape_rich_tags

timeout = global_cache.config_cache["Options"].get("timeout", 10)
client = HTTPClient()
console = Console()


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
        decoded_url = urllib.parse.unquote(url)

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
        print(f"[bold indian_red1]{lang.get_translation("auto_file_size_unknown")}[/bold indian_red1]")

    with open(destination_path, 'wb') as file:
        for data in response.iter_content(chunk_size=1024):
            file.write(data)
            # Ne plus mettre à jour la barre de progression ici

    logging.info(f"Download completed: {destination_path}")


def download_mods_to_update(mods_data):
    """
    Download all mods that require updates using multithreading with a progress bar for each download.
    """
    fixed_bar_width = 40

    # Initialize the Rich Progress bar with your custom layout
    with Progress(
        TextColumn("[bold blue]{task.description}", justify="right"),
        TextColumn("-"),
        TimeElapsedColumn(),
        TextColumn("-"),
        BarColumn(bar_width=fixed_bar_width),
        "[progress.percentage]{task.percentage:>3.0f}%",
        "•",
        TextColumn("[bold green]{task.fields[mod_name]}"),
    ) as progress:
        # Create a single task for all downloads
        task = progress.add_task(f"[cyan]{lang.get_translation("auto_downloading_mods")}", total=len(mods_data), mod_name=" ")

        # Create a thread pool executor for parallel downloads
        max_workers = validate_workers()
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = []
            for mod in mods_data:
                url = mod['download_url']
                # Extract the filename from the URL
                filename = os.path.basename(url)
                filename = extract_filename_from_url(filename)

                # Set the destination folder path
                destination_folder = Path(global_cache.config_cache['ModsPath']['path']).resolve()
                destination_path = destination_folder / filename  # Combine folder path and filename

                # Submit download tasks to the thread pool
                futures.append(executor.submit(download_file, url, destination_path))

                # Erase old file
                file_to_erase = mod['Filename']
                filename_value = Path(global_cache.config_cache['ModsPath']['path']) / file_to_erase
                filename_value = filename_value.resolve()
                if not config.download_enabled:
                    logging.info(f"Skipping download - for TEST")
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

                # Update global_cache.mods_data['installed_mods']
                for installed_mod in global_cache.mods_data['installed_mods']:
                    if installed_mod.get('Filename') == mod.get('Filename'):
                        installed_mod['Local_Version'] = mod['New_version']
                        break  # Stop searching once found

            # Wait for all downloads to finish
            for i, future in enumerate(futures):
                future.result()
                mod = mods_data[i]
                mod_name = mod['Name']
                progress.update(task, completed=i + 1, mod_name=mod_name)


def resume_mods_updated():
    # app_log.txt
    print(f"\n{lang.get_translation("auto_mods_updated_resume")}")
    logging.info(
        "Followings mods have been updated (More details in updated_mods_changelog.txt):")
    # Capture the current date and time
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    for mod in global_cache.mods_data.get('mods_to_update'):
        old_version = escape_rich_tags(str(mod['Old_version']))
        new_version = escape_rich_tags(str(mod['New_version']))

        console.print(
            f"- [green]{mod['Name']} (v{old_version} {lang.get_translation("to")} v{new_version})[/green]")
        print(f"[bold][dark_goldenrod]\n{mod['Changelog']}[/dark_goldenrod][/bold]\n")
        logging.info(
            f"\t- {mod['Name']} (v{mod['Old_version']} to v{mod['New_version']})")

    # mod_updated_log.txt
    mod_updated_logger = config.configure_mod_updated_logging()

    for mod in global_cache.mods_data.get('mods_to_update', []):
        name_version = f"*** {mod['Name']} (v{mod['Old_version']} {lang.get_translation("to")} v{mod['New_version']}) - Updated on {current_time} ***"
        mod_updated_logger.info("================================")
        mod_updated_logger.info(name_version)
        if mod.get('Changelog'):
            changelog = mod['Changelog']
            changelog = changelog.replace("\n", "\n\t")
            mod_updated_logger.info(f"Changelog:\n\t{changelog}")

        mod_updated_logger.info("\n\n")


if __name__ == "__main__":
    pass

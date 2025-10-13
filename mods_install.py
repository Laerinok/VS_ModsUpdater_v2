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
This module handles the installation of mods by downloading them from a list.
It supports multithreaded downloads from a 'modlist.json' file.
"""

__author__ = "Laerinok"
__date__ = "2025-08-25"  # Last update

# mods_install.py

import json
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import requests
from rich.progress import Progress, BarColumn, TextColumn, TransferSpeedColumn, \
    TimeRemainingColumn
import utils
import global_cache
from http_client import HTTPClient


def download_file(url: str, destination_path: Path):
    """
    Downloads a single file from a URL to a specified destination.

    Args:
        url (str): The URL of the file to download.
        destination_path (Path): The full path where the file will be saved.

    Returns:
        bool: True if the download was successful, False otherwise.
    """
    try:
        logging.info(f"Starting download for: {destination_path.name} from {url}")

        # Use HTTPClient to handle the download
        client = HTTPClient()
        response = client.get(url, stream=True)
        response.raise_for_status()

        # Open file in binary write mode
        with open(destination_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        logging.info(f"Successfully downloaded {destination_path.name}")
        return True

    except requests.exceptions.RequestException as e:
        logging.error(f"Download failed for {destination_path.name}: {e}")
        return False
    except Exception as e:
        logging.error(
            f"An unexpected error occurred during download of {destination_path.name}: {e}")
        return False


def get_mod_download_info(mod_entry: dict) -> dict:
    """
    Extracts the download URL and filename from a mod entry.

    Args:
        mod_entry (dict): A dictionary containing mod information.

    Returns:
        dict: A dictionary with 'name', 'url', and 'filename', or None if data is missing.
    """
    try:
        url = mod_entry.get('installed_download_url')
        if not url:
            raise ValueError("Missing 'installed_download_url' in mod entry.")

        filename = utils.extract_filename_from_url(url)
        if not filename:
            filename = url.split('/')[-1].split('?')[0]

        return {
            "name": mod_entry.get('Name', 'Unknown Mod'),
            "url": url,
            "filename": filename
        }
    except (KeyError, ValueError) as e:
        logging.error(f"Error processing mod entry: {e}. Entry: {mod_entry}")
        return None


def install_mods_from_json(json_path: Path, mods_dir: Path):
    """
    Orchestrates the multithreaded download of mods from a JSON file.

    Args:
        json_path (Path): The path to the modlist.json file.
        mods_dir (Path): The destination directory for the mods.
    """
    # 1. Validate paths and create mods directory if it doesn't exist
    if not json_path.exists():
        logging.error(f"Error: The file {json_path} was not found.")
        print(f"Error: The file {json_path} was not found.")
        return

    utils.setup_directories(mods_dir)
    logging.info(f"Mods will be saved to: {mods_dir}")

    # 2. Read the modlist.json file
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            mods_list = data.get('Mods', [])
    except json.JSONDecodeError as e:
        logging.error(f"Failed to decode JSON from {json_path}: {e}")
        return
    except Exception as e:
        logging.error(f"An error occurred while reading {json_path}: {e}")
        return

    if not mods_list:
        logging.info("No mods found in modlist.json. Nothing to download.")
        return

    # 3. Determine number of workers
    max_workers = utils.validate_workers()
    logging.info(f"Using {max_workers} worker threads for downloads.")

    # 4. Use ThreadPoolExecutor for concurrent downloads
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Create a progress bar with the mod name column
        with Progress(
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                TimeRemainingColumn(),
                TransferSpeedColumn(),
                "•",
                TextColumn("[bold green]{task.fields[mod_name]}"),
        ) as progress:
            total_tasks = progress.add_task("[cyan]Downloading Mods...",
                                            total=len(mods_list), mod_name=" ")

            futures = {}

            for mod_data in mods_list:
                mod_info = get_mod_download_info(mod_data)
                if mod_info:
                    mod_path = mods_dir / mod_info['filename']
                    future = executor.submit(download_file, mod_info['url'], mod_path)
                    futures[future] = mod_info['name']
                else:
                    progress.update(total_tasks, advance=1)

            for future in as_completed(futures):
                mod_name = futures[future]
                try:
                    success = future.result()
                    if success:
                        logging.info(f"Download completed for {mod_name}")
                    else:
                        logging.error(f"Download failed for {mod_name}")
                except Exception as e:
                    logging.error(f"An error occurred during task for {mod_name}: {e}")
                finally:
                    # Update the progress bar with the current mod name
                    progress.update(total_tasks, advance=1, mod_name=mod_name)

    logging.info("All download tasks have been processed.")
    print("All mod downloads completed.")


def main():
    """
    Main function to initiate the mod installation process.
    """
    "Modlist install"
    modlist_path = Path(global_cache.config_cache['MODLIST_FOLDER']) / 'modlist.json'
    mods_path = Path(global_cache.config_cache['ModsPath']['path'])

    install_mods_from_json(modlist_path, mods_path)


if __name__ == "__main__":
    main()

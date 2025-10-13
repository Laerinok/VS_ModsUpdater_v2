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
__version__ = "2.4.0"
__date__ = "2025-08-24"  # Last update


# mods_auto_update.py


import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

from rich import print
from rich.console import Console
from rich.progress import Progress, TextColumn, BarColumn, TimeElapsedColumn

import config
import global_cache
import lang
from utils import validate_workers, escape_rich_tags, update_mod_and_handle_files

console = Console()

def download_mods_to_update(mods_data):
    """
    Download all mods that require updates using multithreading.
    Each thread handles the full backup, download, and installation process for a single mod.
    """
    if not mods_data:
        return

    mods_path = Path(global_cache.config_cache['ModsPath']['path']).resolve()
    fixed_bar_width = 40

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
        task = progress.add_task(f"[cyan]{lang.get_translation('auto_downloading_mods')}", total=len(mods_data), mod_name=" ")
        max_workers = validate_workers()
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_mod = {executor.submit(update_mod_and_handle_files, mod, mods_path): mod for mod in mods_data}

            for future in as_completed(future_to_mod):
                mod = future_to_mod[future]
                mod_name = mod['Name']
                try:
                    future.result()
                    for installed_mod in global_cache.mods_data['installed_mods']:
                        if installed_mod.get('Filename') == mod.get('Filename'):
                            installed_mod['Local_Version'] = mod['New_version']
                            if 'New_Filename' in mod:
                                installed_mod['Filename'] = mod['New_Filename']
                                installed_mod['Path'] = mod['New_Path']
                            break
                    logging.info(f"Successfully updated {mod_name}")
                except Exception as e:
                    logging.error(f"Failed to update {mod_name}. See previous logs for details. Error: {e}")

                progress.update(task, advance=1, mod_name=mod_name)


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

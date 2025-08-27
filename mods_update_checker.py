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


"""
__author__ = "Laerinok"
__version__ = "2.3.0"
__date__ = "2025-08-25"  # Last update

# mods_update_checker.py

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from packaging.version import Version
from enum import Enum

import global_cache
from utils import version_compare, check_excluded_mods, convert_html_to_markdown

class ModUpdateStatus(Enum):
    UP_TO_DATE = "up_to_date"
    UPDATE_AVAILABLE = "update_available"
    NO_COMPATIBILITY = "no_compatibility"

class ProcessModResult:
    status: ModUpdateStatus
    update_info: dict[str, str] | None

    def __init__(self, status, update_info=None):
        self.status = status
        self.update_info = update_info

def check_for_mod_updates(force_update=False):
    """
    This module automates the process of checking for updates to installed mods.
    It compares local mod versions with the latest available versions and retrieves changelogs for mods that require updates.

    Key functionalities include:
    - Checking for mod updates by comparing local and latest available versions.
    - Handling excluded mods to skip them during the update check.
    - Fetching changelogs for updated mods using the fetch_changelog module.
    - Populating the global_cache['mods_to_update'] list with relevant mod information.
    - Utilizing multithreading to efficiently process multiple mods.
    - Providing detailed logging for debugging and monitoring.
    """
    check_excluded_mods()  # Update excluded mods list
    excluded_filenames = [mod['Filename'] for mod in
                          global_cache.mods_data.get("excluded_mods", [])]
    mods_to_update: list[dict[str, str]] = []
    incompatible_mods: list[dict[str, str]] = []
    with ThreadPoolExecutor() as executor:
        futures = []
        for mod in global_cache.mods_data.get("installed_mods", []):
            # Pass the force_update flag to the worker function
            futures.append(executor.submit(process_mod, mod, excluded_filenames, force_update))

        # We collect the results from the threads
        for future in as_completed(futures):
            mod_data: ProcessModResult = future.result()
            if mod_data.status == ModUpdateStatus.UPDATE_AVAILABLE:
                mods_to_update.append(mod_data.update_info)
            elif mod_data.status == ModUpdateStatus.NO_COMPATIBILITY:
                incompatible_mods.append(mod_data.update_info)

    global_cache.mods_data['mods_to_update'] = sorted(mods_to_update,
                                                      key=lambda mod: mod['Name'].lower())
    global_cache.mods_data['incompatible_mods'] = sorted(incompatible_mods,
                                                          key=lambda mod: mod['Name'].lower())

def process_mod(mod, excluded_filenames, force_update) -> ProcessModResult:
    """
    Processes a single mod to check for updates and fetch changelog.
    Returns the mod data if an update is found, otherwise None.
    """
    if mod['Filename'] in excluded_filenames:
        logging.info(f"Skipping excluded mod: {mod['Name']}")
        return None  # We return None if the mod is excluded

    # Determine the correct download URL
    download_url = mod.get("latest_version_dl_url")
    changelog_markdown = ""
    user_game_ver = Version(global_cache.config_cache['Game_Version']['user_game_version'])

    # Check if a new version is available or if a force update is requested
    if mod.get("mod_latest_version_for_game_version") and version_compare(
            mod["Local_Version"], mod["mod_latest_version_for_game_version"]):
        # A new version is available, use its URL and changelog
        raw_changelog_html = mod.get("Changelog")
        if raw_changelog_html is not None:
            changelog_markdown = convert_html_to_markdown(raw_changelog_html)
        else:
            logging.info(f"Changelog for {mod['Name']} not available.")

    elif force_update:
        # No new version, but force update is active, use the installed version's URL
        download_url = mod.get("installed_download_url")
        # For a forced update, the changelog is not relevant, we can keep it blank or copy the existing one.
        # Here we just keep it blank as it's a re-install of the same version.

    else:
        # If no update is available and an update was necessary for the mod, then we raise an error
        mod_game_version = mod.get("Game_Version", None)
        if mod_game_version:
            mod_game_version = Version(mod_game_version)
            if (mod_game_version.major, mod_game_version.minor) != (user_game_ver.major, user_game_ver.minor):
                return ProcessModResult(ModUpdateStatus.NO_COMPATIBILITY, 
                                        {
                                            "Name": mod['Name'],
                                            "Old_version": mod['Local_Version'],
                                            "Old_version_game_Version": mod.get("Game_Version", None),
                                            "New_version": mod.get('mod_latest_version_for_game_version',
                                                                    mod['Local_Version']),
                                            "Changelog": None,
                                            "Filename": mod['Filename'],
                                            "download_url": None
                                        })
        # No update available or necessary and no force update, so we don't return any data
        return ProcessModResult(ModUpdateStatus.UP_TO_DATE)

    if download_url:
        return ProcessModResult(ModUpdateStatus.UPDATE_AVAILABLE, 
                                {
                                    "Name": mod['Name'],
                                    "Old_version": mod['Local_Version'],
                                    "Old_version_game_Version": mod.get("Game_Version", None),
                                    "New_version": mod.get('mod_latest_version_for_game_version',
                                                            mod['Local_Version']),
                                    "Changelog": changelog_markdown,
                                    "Filename": mod['Filename'],
                                    "download_url": download_url
                                })

    return None

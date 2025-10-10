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
This module automates the process of checking for updates to installed mods.
It compares local mod versions with the latest available versions and retrieves changelogs for mods that require updates.
"""

__author__ = "Laerinok"
__version__ = "2.4.0"
__date__ = "2025-10-10"  # Last update

# mods_update_checker.py

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from packaging.version import Version
from enum import Enum

import global_cache
from utils import version_compare, VersionCompareState, check_excluded_mods, convert_html_to_markdown

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
    Automates the mod update checking process, comparing local versions
    with latest available versions after filtering out user-excluded mods.
    """
    mods_to_process = []
    mods_to_update: list[dict[str, str]] = []
    incompatible_mods: list[dict[str, str]] = []

    # Pre-filter mods excluded by user configuration
    for mod in global_cache.mods_data.get("installed_mods", []):
        if check_excluded_mods(mod.get('Filename'), mod.get('Name')):
            continue
        mods_to_process.append(mod)

    with ThreadPoolExecutor() as executor:
        futures = []
        for mod in mods_to_process:
            futures.append(executor.submit(process_mod, mod, force_update))

        # We collect the results from the threads
        for future in as_completed(futures):
            mod_data: ProcessModResult = future.result()
            if mod_data:
                if mod_data.status == ModUpdateStatus.UPDATE_AVAILABLE:
                    mods_to_update.append(mod_data.update_info)
                elif mod_data.status == ModUpdateStatus.NO_COMPATIBILITY:
                    incompatible_mods.append(mod_data.update_info)

    global_cache.mods_data['mods_to_update'] = sorted(mods_to_update,
                                                      key=lambda mod: mod['Name'].lower())
    global_cache.mods_data['incompatible_mods'] = sorted(incompatible_mods,
                                                          key=lambda mod: mod['Name'].lower())


def process_mod(mod, force_update) -> ProcessModResult:
    """
    Processes a single mod to check for updates and fetch changelog.
    Returns the mod data if an update is found, otherwise None.
    """
    # Determine the correct download URL
    download_url = mod.get("latest_version_dl_url")
    changelog_markdown = ""
    user_game_ver = Version(global_cache.config_cache['Game_Version']['user_game_version'])

    # Check if a new version is available or if a force update is requested
    mod_latest_version_for_game_version = mod.get("mod_latest_version_for_game_version", None)
    version_compare_result = version_compare(mod["Local_Version"], mod_latest_version_for_game_version) if mod_latest_version_for_game_version else None
    if version_compare_result in [VersionCompareState.LOCAL_VERSION_BEHIND, VersionCompareState.LOCAL_VERSION_AHEAD]:
        # A new version is available or the current version is too recent, use its URL and changelog
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

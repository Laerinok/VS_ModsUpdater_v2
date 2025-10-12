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
__date__ = "2025-10-11"  # Last update

# mods_update_checker.py

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from packaging.version import Version, InvalidVersion
from enum import Enum

import global_cache
from utils import version_compare, VersionCompareState, check_excluded_mods

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
    Processes a single mod to determine if an update, downgrade, or re-install is needed.
    """
    local_version_str = mod.get("Local_Version")
    best_compatible_version_str = mod.get("mod_latest_version_for_game_version")
    
    # Handle --force-update first
    if force_update:
        logging.debug(f"Force update for {mod['Name']}. Re-installing version {local_version_str}.")
        return ProcessModResult(ModUpdateStatus.UPDATE_AVAILABLE, {
            "Name": mod['Name'],
            "Old_version": local_version_str,
            "Old_version_game_Version": mod.get("Game_Version_API"),
            "New_version": local_version_str,
            "Changelog": "",
            "Filename": mod['Filename'],
            "download_url": mod.get("installed_download_url")
        })

    # If a best compatible version exists, compare it to the local version
    if best_compatible_version_str:
        if local_version_str != best_compatible_version_str:
            logging.info(f"Update/Downgrade found for {mod['Name']}. Local: {local_version_str}, Compatible: {best_compatible_version_str}")
            return ProcessModResult(ModUpdateStatus.UPDATE_AVAILABLE, {
                "Name": mod['Name'],
                "Old_version": local_version_str,
                "Old_version_game_Version": mod.get("Game_Version_API"),
                "New_version": best_compatible_version_str,
                "Changelog": mod.get("Changelog", ""),
                "Filename": mod['Filename'],
                "download_url": mod.get("latest_version_dl_url")
            })
        else:
            # The local version is the best compatible version
            logging.info(f"{mod['Name']} is already the best compatible version ({local_version_str}).")
            return ProcessModResult(ModUpdateStatus.UP_TO_DATE)

    # If NO compatible version exists, check if the installed mod is itself incompatible
    else:
        user_game_ver_str = global_cache.config_cache['Game_Version']['user_game_version']
        local_game_ver_str = mod.get("Game_Version_API")

        if local_game_ver_str and local_game_ver_str != "unknown":
            try:
                user_game_ver = Version(user_game_ver_str)
                local_game_ver = Version(local_game_ver_str)
                if (local_game_ver.major, local_game_ver.minor) != (user_game_ver.major, user_game_ver.minor):
                    logging.warning(f"Incompatible mod: {mod['Name']} (for game v{local_game_ver}) has no compatible version for game v{user_game_ver}.")
                    return ProcessModResult(ModUpdateStatus.NO_COMPATIBILITY, {
                        "Name": mod['Name'],
                        "Old_version": local_version_str,
                        "Old_version_game_Version": local_game_ver_str
                    })
            except InvalidVersion:
                logging.warning(f"Could not parse game version for {mod['Name']} to check incompatibility.")

    # If no action was taken, the mod is considered up-to-date
    logging.info(f"{mod['Name']} is considered up-to-date.")
    return ProcessModResult(ModUpdateStatus.UP_TO_DATE)

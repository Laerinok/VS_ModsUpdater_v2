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
__date__ = "2025-10-03"  # Last update

# mods_update_checker.py

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

import global_cache
from utils import version_compare, VersionCompareState, check_excluded_mods, convert_html_to_markdown


def check_for_mod_updates(force_update=False):
    """
    Automates the mod update checking process, comparing local versions
    with latest available versions after filtering out user-excluded mods.
    """

    # Reset excluded_mods list. (Technical Debt Note: Review if fetch_mod_info runs first
    # and if clearing its API failures here is desirable.)
    global_cache.mods_data["excluded_mods"] = []

    mods_to_process = []

    # Pre-filter mods excluded by user configuration (Case 1)
    for mod in global_cache.mods_data.get("installed_mods", []):
        mod_filename = mod.get('Filename')
        mod_name = mod.get('Name')

        # If excluded, utils.check_excluded_mods adds the reason to global_cache.
        if check_excluded_mods(mod_filename, mod_name):
            continue

        mods_to_process.append(mod)

    mods_to_update = []

    # Launch parallel processing on the remaining mods
    with ThreadPoolExecutor() as executor:
        futures = []
        for mod in mods_to_process:
            # IMPORTANT: Removed 'excluded_filenames' argument.
            futures.append(executor.submit(process_mod, mod, force_update))

        for future in as_completed(futures):
            mod_data = future.result()
            if mod_data:
                mods_to_update.append(mod_data)

    global_cache.mods_data['mods_to_update'] = sorted(mods_to_update,
                                                      key=lambda item: item[
                                                          "Name"].lower())


def process_mod(mod, force_update):
    """
    Processes a single mod to check for updates and fetch changelog.
    Returns the mod data if an update is found, otherwise None.
    """
    mod_name = mod.get('Name')

    if not mod.get("Mod_url"):
        # This mod failed API fetch in fetch_mod_info.py (Case 2),
        # so it has incomplete data and should be skipped for update check.
        # It should already be in the 'excluded_mods' list.
        logging.warning(
            f"Skipping update check for {mod_name}: missing API data (Mod_url).")
        return None

    # Determine the correct download URL
    download_url = mod.get("latest_version_dl_url")
    changelog_markdown = ""

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
        # No update needed and no force update, so we don't return any data
        return None

    if download_url:
        return {
            "Name": mod['Name'],
            "Old_version": mod['Local_Version'],
            "New_version": mod.get('mod_latest_version_for_game_version',
                                   mod['Local_Version']),
            "Changelog": changelog_markdown,
            "Filename": mod['Filename'],
            "download_url": download_url
        }

    return None

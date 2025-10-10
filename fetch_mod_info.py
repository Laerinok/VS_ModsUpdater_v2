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
This module is designed to scan and retrieve information about Vintage Story mods, both locally from zip files and online via API calls. It automates the process of extracting essential mod details, such as mod ID, name, version, and description, and enriches this information with data fetched from the Vintage Story mod API.

Key functionalities include:
- Scanning a specified mods folder for zip and .cs files.
- Extracting mod metadata from modinfo.json within zip files.
- Parsing version, side, namespace, and description information from .cs files.
- Validating zip files to ensure they are not corrupted.
- Fetching additional mod details from the Vintage Story mod API, including asset ID, mod URL, and compatible releases, using multithreading for efficiency.
- Handling excluded mods by retrieving specific mainfile URLs.
- Sorting mods by name for consistent presentation.
- Managing potential errors and logging relevant information.
"""

__author__ = "Laerinok"
__version__ = "2.4.0"
__date__ = "2025-10-10"  # Last update

# fetch_mod_info.py

import json
import logging
import re
import sys
import time
import zipfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from packaging.version import Version
from rich import print
from rich.progress import Progress, TextColumn, BarColumn, TimeElapsedColumn

import cli
import config
import global_cache
import lang
from http_client import HTTPClient
from utils import fix_json, is_zip_valid, validate_workers

timeout = global_cache.config_cache["Options"].get("timeout", 10)
client = HTTPClient()


def get_mod_path():
    # Ensure the directory exists
    if "ModsPath" not in global_cache.config_cache or "path" not in \
            global_cache.config_cache["ModsPath"]:
        print(
            f"[indian_red1]{lang.get_translation("error")}[/indian_red1] {lang.get_translation("fetch_mod_info_error_mods_path_missing")}")
        logging.error(
            "Error: The ModsPath or 'path' key is missing in the configuration.")
        time.sleep(2)
        sys.exit(1)

    args = cli.parse_args()
    if args.modspath:
        mods_path = args.modspath.resolve()
        global_cache.config_cache['ModsPath']['path'] = mods_path
    else:
        mods_path = Path(global_cache.config_cache['ModsPath']['path']).resolve()

    if not mods_path.exists():
        print(
            f"[indian_red1]{lang.get_translation("error")}[/indian_red1] {lang.get_translation("fetch_mod_info_error_mods_path_not_found").format(mods_path=mods_path)}")
        logging.error(f"Error: The mods path {mods_path} is not found.")
        time.sleep(2)
        sys.exit(1)

    return mods_path


def get_modinfo_from_zip(zip_path):
    """Gets modid, name, version, and description from modinfo.json in a zip file."""
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            file_list = zip_ref.namelist()

            if 'modinfo.json' in file_list:
                modinfo_path = 'modinfo.json'
            else:
                modinfo_path = next(
                    (f for f in file_list if f.endswith('/modinfo.json')), None)

                if not modinfo_path:
                    return None, None, None, None, None

            with zip_ref.open(modinfo_path) as modinfo_file:
                raw_json = modinfo_file.read().decode('utf-8-sig')
                fixed_json = fix_json(raw_json)
                modinfo = json.loads(fixed_json)

                modinfo_lower = {k.lower(): v for k, v in modinfo.items()}
                dependencies = modinfo_lower.get('dependencies', {})
                if dependencies:
                    game_version_dependency: str | None = dependencies.get('game', None)
                return (
                    modinfo_lower.get('modid'),
                    modinfo_lower.get('name'),
                    modinfo_lower.get('version'),
                    modinfo_lower.get('description'),
                    game_version_dependency
                )

    except zipfile.BadZipFile:
        logging.error(f"Error: {zip_path} is not a valid zip file.")
    except json.JSONDecodeError:
        logging.error(f"Error: Failed to parse modinfo.json in {zip_path}")
    except Exception as e:
        logging.error(f"Unexpected error processing {zip_path}: {e}")

    return None, None, None, None, None


def get_cs_info(cs_path):
    """Gets Version, Side, namespace information from a .cs file."""
    with open(cs_path, 'r', encoding='utf-8') as cs_file:
        content = cs_file.read()
        version_match = re.search(r'Version\s*=\s*"([^"]+)"', content)
        side_match = re.search(r'Side\s*=\s*"([^"]+)"', content)
        namespace_match = re.search(r'namespace\s+([A-Za-z0-9_]+)', content)
        description_match = re.search(r'Description\s*=\s*"([^"]+)"', content)

        version = version_match.group(1) if version_match else None
        side = side_match.group(1) if side_match else None
        description = description_match.group(1) if description_match else None
        namespace = namespace_match.group(1) if namespace_match else None
        modid = namespace.lower().replace(" ", "") if namespace else None
        mod_url_api = f'{config.URL_BASE_MOD_API}{modid}'
        return version, side, namespace, modid, mod_url_api, description


def process_mod_file(file, mods_data, invalid_files):
    """Process a mod file (zip or cs), and add the results to mods_data or invalid_files."""
    if file.suffix == '.zip':
        if is_zip_valid(file):
            modid, modname, local_mod_version, description, game_version_dependency = get_modinfo_from_zip(file)
            if modid and modname and local_mod_version:
                mods_data["installed_mods"].append({
                    "Name": modname,
                    "Local_Version": local_mod_version,
                    "ModId": modid,
                    "Description": description,
                    "Filename": file.name,
                    "Game_Version": game_version_dependency
                })
            else:
                invalid_files.append(file.name)
        else:
            invalid_files.append(file.name)
    elif file.suffix == '.cs':
        local_mod_version, side, namespace, modid, mod_url_dl, description = get_cs_info(
            file)
        if local_mod_version and namespace and modid:
            mods_data["installed_mods"].append({
                "Name": namespace,
                "Local_Version": local_mod_version,
                "ModId": modid,
                "Description": description,
                "Filename": file.name
            })
        else:
            invalid_files.append(file.name)


def get_mainfile_from_excluded_mods(sorted_releases, excluded_mods):
    """
    Récupère le mainfile correspondant au Filename des mods exclus.
    """
    excluded_filenames = {mod['Filename'] for mod in excluded_mods}
    mainfiles = []
    for release in sorted_releases:
        if release['filename'] in excluded_filenames:
            mainfiles.append(release['mainfile'])
    return mainfiles


def get_compatible_releases(mod_json, user_game_version, exclude_prerelease):
    """
    Retrieve all compatible releases for the mod based on the user_game_version and changelogs
    """
    releases = mod_json.get("mod", {}).get("releases", [])
    user_ver = Version(user_game_version.lstrip("v"))
    compatible_releases = []
    for release in releases:
        for tag in release.get("tags", []):
            if not tag:
                continue
            try:
                tag_ver = Version(tag.lstrip("v"))
                if exclude_prerelease.lower() == "true" and Version(
                        release['modversion']).is_prerelease:
                    continue
                if tag_ver <= user_ver and (tag_ver.major, tag_ver.minor) == (
                        user_ver.major, user_ver.minor):
                    compatible_releases.append(release)
                    break
            except Exception:
                continue
    if not compatible_releases:
        logging.info(
            f"{mod_json['mod']['name']}: No compatible release found for game version {user_game_version}.")
        return []

    sorted_releases = sorted(
        compatible_releases,
        key=lambda r: (Version(r.get("modversion") or "0.0.0"), r.get("created") or ""),
        reverse=True
    )
    return sorted_releases


def get_installed_versions_download_urls(all_releases, global_cache_installed_mods):
    """
    Finds the download URL for the exact installed version of a mod.
    """
    installed_urls = {}
    if not global_cache_installed_mods or not all_releases:
        return installed_urls

    for installed_mod in global_cache_installed_mods:
        installed_version = installed_mod.get("Local_Version")
        installed_filename = installed_mod.get("Filename")
        if installed_version and installed_filename:
            for release in all_releases:
                if release.get("modversion") == installed_version:
                    installed_urls[installed_filename] = release.get("mainfile")
                    break

    return installed_urls


def get_mod_api_data(mod):
    """
    Retrieve mod infos from API, including the changelog for the latest compatible version.
    """
    modid = mod['ModId']
    logging.debug(f"Attempting to fetch data for mod '{modid}' from API.")
    mod_url_api = f'{config.URL_BASE_MOD_API}{modid}'
    logging.debug(f"Retrieving mod info from: {mod_url_api}")

    changelog = None
    try:
        response = client.get(mod_url_api, timeout=int(
            global_cache.config_cache["Options"]["timeout"]))
        response.raise_for_status()
        mod_json = response.json()
    except Exception as e:
        logging.warning(
            f"Failed to retrieve mod info for mod: {modid} at link {mod_url_api}. Error: {e}")
        mod["Mod_url"] = "Local mod"
        return None, None, None, None, None, None, None

    if mod_json['statuscode'] != '200':
        logging.warning(
            f"Failed to retrieve mod info for mod: {modid} (status code {mod_json['statuscode']}) at link {mod_url_api}")
        mod["Mod_url"] = "Local mod"
        return None, None, None, None, None, None, None

    mod_assetid = mod_json["mod"]["assetid"]
    side = mod_json["mod"]["side"]
    mod_url = f"{global_cache.config_cache['URL_MOD_DB']}{mod_assetid}"
    exclude_prerelease = global_cache.config_cache['Options']['exclude_prerelease_mods']

    installed_download_urls_dict = get_installed_versions_download_urls(
        mod_json.get("mod", {}).get("releases", []), [mod])

    encoded_installed_download_url = None
    if mod['Filename'] in installed_download_urls_dict:
        installed_download_url = installed_download_urls_dict[mod['Filename']]
        # Correction 1: Assign the URL directly, fixing the missing assignment and potential double-encoding
        encoded_installed_download_url = installed_download_url

    sorted_releases = get_compatible_releases(mod_json,
                                              global_cache.config_cache['Game_Version']['user_game_version'],
                                              exclude_prerelease)
    if sorted_releases:
        latest_compatible_version_str = sorted_releases[0].get('modversion')
        all_changelogs = []
        local_version_str = mod.get("Local_Version")
        all_api_releases = mod_json.get("mod", {}).get("releases", [])

        if local_version_str and latest_compatible_version_str and all_api_releases:
            try:
                local_version = Version(local_version_str)
                latest_compatible_version = Version(latest_compatible_version_str)

                releases_for_changelog = []
                for release in all_api_releases:
                    release_version_str = release.get("modversion")
                    if not release_version_str:
                        continue
                    try:
                        release_version = Version(release_version_str)
                        if local_version < release_version <= latest_compatible_version:
                            releases_for_changelog.append(release)
                    except Exception:
                        logging.warning(f"Could not parse release version: {release_version_str} for mod {mod['ModId']}")

                releases_for_changelog.sort(key=lambda r: Version(r.get("modversion", "0")))

                for release in releases_for_changelog:
                    changelog_text = release.get('changelog')
                    if changelog_text:
                        all_changelogs.append(
                            f"### {lang.get_translation('changelog_version_title')} {release.get('modversion')}\n{changelog_text}")

            except Exception as e:
                logging.warning(f"Error processing changelogs for mod {mod['ModId']}: {e}")
                all_changelogs = []

        if all_changelogs:
            changelog = "\n\n".join(all_changelogs)
        else:
            changelog = sorted_releases[0].get('changelog')
    else:
        changelog = None

    mainfile_excluded_file = get_mainfile_from_excluded_mods(sorted_releases,
                                                             global_cache.mods_data[
                                                                 'excluded_mods'])
    if any(excluded_mod['Filename'] == mod['Filename'] for excluded_mod in
           global_cache.mods_data['excluded_mods']):
        if mainfile_excluded_file:
            mainfile_url = mainfile_excluded_file[0]
            # Correction 2: Removing redundant urllib.parse.quote (double encoding fix)
            encoded_mainfile_url = mainfile_url
            mod_latest_version_for_game_version = sorted_releases[0]['modversion']
            return mod_assetid, mod_url, encoded_mainfile_url, mod_latest_version_for_game_version, side, None, changelog
        else:
            global_cache.mods_data["installed_mods"][-1]["Side"] = side
            global_cache.mods_data["installed_mods"][-1]["Mod_url"] = mod_url
            return mod_assetid, mod_url, None, None, side, encoded_installed_download_url, changelog

    if not sorted_releases:
        global_cache.mods_data["installed_mods"][-1]["Side"] = side
        global_cache.mods_data["installed_mods"][-1]["Mod_url"] = mod_url
        return mod_assetid, mod_url, None, None, side, encoded_installed_download_url, changelog

    mainfile_url = sorted_releases[0]['mainfile']
    # Correction 3: Removing redundant urllib.parse.quote (double encoding fix)
    encoded_mainfile_url = mainfile_url

    mod_latest_version_for_game_version = sorted_releases[0]['modversion']
    return mod_assetid, mod_url, encoded_mainfile_url, mod_latest_version_for_game_version, side, encoded_installed_download_url, changelog


def scan_and_fetch_mod_info(mods_folder):
    """
    Orchestrates the scanning of the mods folder, extraction of basic mod information, and retrieval of detailed mod data from the API.
    """
    invalid_files = []

    max_workers = validate_workers()
    # mod_files = list(mods_folder.iterdir())  # old code. to delete
    excluded_mods_from_config = global_cache.config_cache.get('Mods_Exclusion', {}).get(
        'mods', [])

    # Filter out files that are in the exclusion list
    all_mod_files = list(mods_folder.iterdir())
    mod_files = [f for f in all_mod_files if f.name not in excluded_mods_from_config]

    # New section to display excluded mods
    if excluded_mods_from_config:
        print(
            f"\n[bold orange3]{lang.get_translation('main_excluded_mods_title')}[/bold orange3]")
        for mod in excluded_mods_from_config:
            print(f"- [indian_red1]{mod}[/indian_red1]")
        print()
    total_files = len(mod_files)
    fixed_bar_width = 40
    with Progress(
            TextColumn("[bold blue]{task.description}", justify="right"),
            TextColumn("-"),
            TimeElapsedColumn(),
            TextColumn("-"),
            BarColumn(bar_width=fixed_bar_width),
            "[progress.percentage]{task.percentage:>3.0f}%",
            "•",
    ) as progress:
        task = progress.add_task(
            f"[cyan]{lang.get_translation("fetch_mod_info_scanning_mods")}",
            total=total_files)
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = []
            for file in mods_folder.iterdir():
                futures.append(
                    executor.submit(process_mod_file, file, global_cache.mods_data,
                                    invalid_files))

            for idx, future in enumerate(as_completed(futures)):
                future.result()
                progress.update(task, advance=1)

    global_cache.mods_data["installed_mods"].sort(
        key=lambda item: item["Name"].lower() if item["ModId"] else "")

    mod_ids = [mod['ModId'] for mod in global_cache.mods_data["installed_mods"]]
    mods = global_cache.mods_data[
        "installed_mods"]

    with Progress(
            TextColumn("[bold blue]{task.description}", justify="right"),
            TextColumn("-"),
            TimeElapsedColumn(),
            TextColumn("-"),
            BarColumn(bar_width=fixed_bar_width),
            "[progress.percentage]{task.percentage:>3.0f}%",
            "•",
            TextColumn("[bold green]{task.fields[mod_name]}"),
            "•",
    ) as progress:
        api_task = progress.add_task(
            f"[green]{lang.get_translation("fetch_mod_info_fetching_mod_info")}",
            total=len(mod_ids), mod_name=" ")
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            api_futures = []
            future_to_mod = {}
            for mod in mods:
                future = executor.submit(get_mod_api_data, mod)
                api_futures.append(future)
                future_to_mod[future] = mod
            for future in as_completed(api_futures):
                mod = future_to_mod[future]
                mod_assetid, mod_url, mainfile_url, mod_latest_version_for_game_version, side, installed_download_url, changelog_from_api = future.result()

                if mod_assetid and mod_url:
                    mod["AssetId"] = mod_assetid
                    mod["Mod_url"] = mod_url
                    mod["mod_latest_version_for_game_version"] = mod_latest_version_for_game_version
                    mod["latest_version_dl_url"] = mainfile_url
                    mod["Side"] = side
                    mod["installed_download_url"] = installed_download_url
                    mod["Changelog"] = changelog_from_api
                    logging.debug(
                        f"Received assetid: {mod_assetid}, mod_url: {mod_url}, and changelog for mod: {mod['Name']}")
                else:
                    reason_message = lang.get_translation("fetch_mod_info_exclusion_reason_api_failure")
                    # Add local mods to the excluded list here
                    global_cache.mods_data["excluded_mods"].append({"Filename": mod['Filename'], "Name": mod['Name'], "Reason": reason_message})
                    logging.warning(
                        f"Failed to retrieve API data for mod: {mod['Name']}. Skipping update for this mod.")
                progress.update(api_task, advance=1,
                                description=f'[cyan]{lang.get_translation("fetch_mod_info_fetching_mod_info_name")}',
                                mod_name=mod['Name'])
    return {"installed_mods": global_cache.mods_data["installed_mods"], "excluded_mods": global_cache.mods_data["excluded_mods"]}


if __name__ == "__main__":
    pass

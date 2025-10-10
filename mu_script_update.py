#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2024 Laerinok
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.

"""
This module checks for updates to the ModsUpdater script itself by comparing the current version with the latest version available on ModDB via their API.

It fetches and parses the API response to extract version information and download URLs.
Key functionalities include:
- Determining the correct API URL based on the operating system.
- Fetching and parsing the ModDB API response to locate version information and download links.
- Extracting the latest version number and download URL from the JSON content.
- Comparing the current script version with the latest available version.
- Returning a boolean indicating whether an update is available, along with the download URL, latest version and changelog text.
- Handling potential network errors and JSON parsing issues, with appropriate logging.
"""

__author__ = "Laerinok"
__version__ = "2.4.0"
__date__ = "2025-08-26"  # Last update

# mu_script_update.py

import logging
import utils
from http_client import HTTPClient
import config
import global_cache

# Initialize the HTTP client for making requests.
client = HTTPClient()


def modsupdater_update():
    """
    Fetches and verifies the latest ModsUpdater version via the ModDB API,
    and also retrieves the changelog.

    Returns:
        tuple: A tuple containing (new_version_available, download_url, latest_version, changelog_text)
               or (None, None, None, None) if an error occurs.
    """
    logging.info("Checking for the latest ModsUpdater script version via API...")

    system = config.SYSTEM.lower()
    api_url = config.URL_SCRIPT.get(system)

    if not api_url:
        logging.error(f"API URL is not defined for the system '{system}'.")
        return None, None, None, None

    try:
        response = client.get(api_url, timeout=int(
            global_cache.config_cache["Options"]["timeout"]))
        response.raise_for_status()

        data = response.json()

        if "mod" not in data or "releases" not in data["mod"] or not data["mod"][
            "releases"]:
            logging.error("API response did not contain a valid mod or releases list.")
            return None, None, None, None

        latest_release = data["mod"]["releases"][0]
        latest_version = latest_release.get("modversion")
        download_url = latest_release.get("mainfile")
        changelog_html = latest_release.get("changelog")

        if not latest_version or not download_url or not changelog_html:
            logging.error(
                "The API response did not contain complete version, download, or changelog information.")
            return None, None, None, None

        # Convert the HTML changelog to a readable Markdown format for the console.
        changelog_text = utils.convert_html_to_markdown(changelog_html)

        new_version = utils.version_compare(__version__, latest_version) == utils.VersionCompareState.LOCAL_VERSION_BEHIND

        logging.info(
            f"Current version: {__version__}, Latest version: {latest_version}")

        return new_version, download_url, latest_version, changelog_text

    except Exception as e:
        logging.error(f"Error while checking for an update via the API: {e}")
        return None, None, None, None


if __name__ == "__main__":
    pass

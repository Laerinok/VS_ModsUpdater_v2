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

__author__ = "Laerinok"
__version__ = "2.0.0-dev1"
__date__ = "2024-11-07"  # Last update

# utils.py

import re
import logging
import requests
from packaging.version import Version, InvalidVersion


def print_dict(dictionary):  # For test and debug
    """Print a dictionary in a structured format."""
    for key, value in dictionary.items():
        print(f"{key}: {value}")


def normalize_keys(d):
    """Normalize the keys of a dictionary to lowercase"""
    if isinstance(d, dict):
        return {k.lower(): normalize_keys(v) for k, v in d.items()}
    elif isinstance(d, list):
        return [normalize_keys(i) for i in d]
    else:
        return d


def fix_json(json_data):
    # Correction 1 : Remove final commas
    json_data = re.sub(r",\s*([}\]])", r"\1", json_data)

    # Correction 2 : Add missing quotation marks around keys
    json_data = re.sub(r'(?<!")(\b\w+\b)(?=\s*:)', r'"\1"', json_data)
    return json_data


def version_compare(local_version, online_version):
    # Compare local and online version
    if Version(local_version) < Version(online_version):
        new_version = True
        return new_version
    else:
        new_version = False
        return new_version


def setup_directories(path_dir):
    if not path_dir.exists():
        path_dir.mkdir(parents=True, exist_ok=True)


def log_error(message):
    print(message)
    logging.error(message)


def is_valid_version(version_string):
    try:
        # Try to create a Version object.
        Version(version_string)
        return True
    except InvalidVersion:
        # If the version is not valid, an InvalidVersion exception will be raised.
        return False


# Retrieve the last game version
def get_last_game_version(url_api='https://mods.vintagestory.at/api'):
    gameversions_api_url = f'{url_api}/gameversions'
    try:
        response = requests.get(gameversions_api_url)
        response.raise_for_status()  # Checks that the request was successful (status code 200)
        gameversion_data = response.json()  # Retrieves JSON content
        logging.info(f"Game version data retrieved.")
        # Retrieve the latest version
        return gameversion_data['gameversions'][0]['name'][1:]
    except:
        logging.warning(f"Cannot reach gameversion api.")
        return None

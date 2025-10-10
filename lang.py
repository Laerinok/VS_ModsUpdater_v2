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
This module manages language translations for the Vintage Story Mods Updater application, using a global cache to store and retrieve translations. It allows the application to support multiple languages by loading translations from JSON files based on the user's language setting.

Key functionalities include:
- Retrieving the language setting from the global configuration cache.
- Loading translations from a specified JSON file into the global language cache.
- Handling cases where the language file is not found or cannot be parsed, raising appropriate exceptions.
- Caching translations to avoid redundant file reads and improve performance.
- Providing a central point for accessing and managing language-specific text within the application.

"""
__author__ = "Laerinok"
__version__ = "2.4.0"
__date__ = "2025-08-24"  # Last update

# lang.py

import json
import logging
import os
from pathlib import Path

import global_cache


# config.load_config()


def get_language_setting():
    """Retrieve the language setting from the global cache."""
    if not global_cache.config_cache:
        logging.error("Configuration cache is empty. Ensure configuration is loaded.")
        raise RuntimeError("Configuration cache is empty. Ensure configuration is loaded.")
    return global_cache.config_cache["Language"]["language"]


def load_translations(path=None):
    """
    Load translations into the global cache based on the current language setting.
    """
    # If translations are already loaded, return them from the cache
    if global_cache.language_cache:
        return global_cache.language_cache

    lang_file_path = None

    # Determine the path of the language file
    if path:
        lang_file_path = Path(path)
    elif global_cache.config_cache:
        language = get_language_setting()
        appdir = os.environ.get('APPDIR')
        if appdir:
            lang_file_path = Path(appdir) / "lang" / f"{language}.json"
        else:
            lang_file_path = Path() / "lang" / f"{language}.json"

    # Handle the case where lang_file_path could not be determined
    if not lang_file_path or not lang_file_path.exists():
        logging.error(f"[Error] Language file not found: {lang_file_path}. Ensure the path is correct.")
        raise FileNotFoundError(
            f"[Error] Language file not found: {lang_file_path}. Ensure the path is correct."
        )

    # Load translations from the language file
    try:
        with open(lang_file_path, 'r', encoding='utf-8') as file:
            translations = json.load(file)
            global_cache.language_cache.update(translations)
    except json.JSONDecodeError as e:
        logging.error(f"[Error] Failed to parse language file: {lang_file_path}. {e}")
        raise ValueError(f"[Error] Failed to parse language file: {lang_file_path}. {e}")
    except FileNotFoundError as e:
        logging.error(f"[Error] Unable to locate the language file: {lang_file_path}. {e}")
        raise FileNotFoundError(f"[Error] Unable to locate the language file: {lang_file_path}. {e}")

    return global_cache.language_cache


def get_translation(key):
    """Retrieve a translation from the cache."""
    if not global_cache.language_cache:
        load_translations()  # Ensure translations are loaded
    return global_cache.language_cache.get(key, f"Translation not found: {key}")


if __name__ == "__main__":
    pass

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
Global Cache Management for Vintage Story Mod Updater

This module handles caching for various global data used throughout the script. It manages:
- Configuration data loaded from config.ini / System information like paths and environment variables
- Language translations loaded from JSON files
- Mod-related data (mod info, updates, etc.)
"""
__author__ = "Laerinok"
__version__ = "2.3.0"
__date__ = "2025-08-24"  # Last update


# global_cache.py


config_cache = {}  # Configuration cache
# set the defaut timeout in globcal_cache:
config_cache.setdefault("Options", {"timeout": 10})

language_cache = {}  # Translation cache
mods_data = {"installed_mods": [],
             "excluded_mods": [],
             "mods_to_update": [],
             "incompatible_mods": []
             }  # Mod cache
modinfo_json_cache = {}
total_mods = 0

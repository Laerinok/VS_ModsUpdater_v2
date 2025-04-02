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
Module for handling HTTP requests with persistence, retries, and proper session management.

This module defines an HTTPClient class that manages requests and retries, improves error handling,
and ensures that session cookies and headers are maintained throughout requests. It can be used for
API calls, downloading files, and any HTTP requests requiring a persistent session.
"""


__author__ = "Laerinok"
__version__ = "2.0.1-rc2"
__date__ = "2025-04-02"  # Last update

# cli.py
import argparse
from pathlib import Path


def parse_args():
    """Parses command-line arguments."""
    parser = argparse.ArgumentParser(description="ModsUpdater options")

    parser.add_argument('--no-pause', action='store_true', help='Disable the pause at the end')
    parser.add_argument('--modspath', type=str, help='Enter the mods directory (in quotes).')
    parser.add_argument('--no-pdf', action='store_true', help='Disable the PDF modlist generation')
    parser.add_argument('--no-json', action='store_true', help='Disable the JSON modlist generation')

    parser.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'], help='Set the logging level')
    parser.add_argument('--max-workers', type=int, help='Set the maximum number of workers for downloads')
    parser.add_argument('--timeout', type=int, help='Set the timeout for downloads')

    parser.add_argument('--backup-folder', type=str, help='Set the backup folder name')
    parser.add_argument('--max-backups', type=int, help='Set the maximum number of backups to keep')

    args = parser.parse_args()

    # Vérification de l'existence du chemin
    if args.modspath:
        path_modspath = Path(args.modspath).resolve()
        if not path_modspath.exists():
            print(f"Error: Mods directory '{args.modspath}' not found.")
            exit(1)

        # Vérification si le chemin est un répertoire
        if not path_modspath.is_dir():
            print(f"Error: '{args.modspath}' is not a directory.")
            exit(1)

        args.modspath = path_modspath

    return args

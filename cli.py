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
__version__ = "2.3.0"
__date__ = "2025-08-24"  # Last update


# cli.py


import argparse
from pathlib import Path
import sys


def parse_args():
    """Parses command-line arguments."""
    parser = argparse.ArgumentParser(description="ModsUpdater options")

    parser.add_argument('--no-pause', action='store_true', help='Disable the pause at the end')
    parser.add_argument('--modspath', type=str, help='Enter the mods directory (in quotes).')
    parser.add_argument('--no-json', action='store_true',help='Disable the JSON modlist generation')
    parser.add_argument('--no-pdf', action='store_true', help='Disable the PDF modlist generation')
    parser.add_argument('--no-html', action='store_true',help='Disable the HTML modlist generation')
    parser.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'], help='Set the logging level')
    parser.add_argument('--max-workers', type=int, help='Set the maximum number of workers for downloads')
    parser.add_argument('--timeout', type=int, help='Set the timeout for downloads')
    parser.add_argument('--install-modlist', action='store_true', help='Download mods from modlist.json to the mods folder.')
    parser.add_argument('--force-update', action='store_true', help='Force a re-download and re-install of all mods, regardless of version.')
    parser.add_argument('--dry-run', action='store_true', help='List mods with updates without downloading them.')

    args = parser.parse_args()

    # Checking the path's existence
    if args.modspath:
        path_modspath = Path(args.modspath).resolve()
        if not path_modspath.exists():
            print(f"Error: Mods directory '{args.modspath}' not found.")
            exit(1)

        # Checking if the path is a directory
        if not path_modspath.is_dir():
            print(f"Error: '{args.modspath}' is not a directory.")
            exit(1)

        args.modspath = path_modspath

    # Checking max-workers
    if args.max_workers is not None:
        if args.max_workers <= 0:
            print("Error: max-workers must be a positive integer.")
            sys.exit(1)

    # Checking timeout
    if args.timeout is not None:
        if not isinstance(args.timeout, int):
            print("Error: timeout must be an integer.")
            sys.exit(1)
        elif args.timeout <= 0:
            print("Error: timeout must be a positive integer.")
            sys.exit(1)

    return args

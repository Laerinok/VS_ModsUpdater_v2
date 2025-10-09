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
This module provides functionality for exporting reports.
"""

__author__ = "Laerinok"
__version__ = "2.3.0"
__date__ = "2025-10-09"  # Last update

# export_report.py

from datetime import datetime
from pathlib import Path

from rich import print

import global_cache
import lang


def generate_dry_run_report(mods_to_update):
    """
    Generates a text report listing mods that have updates available.
    The report is saved as dry_run_report.txt in the logs directory.
    """
    report_content = []
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Add a header to the report
    report_content.append(lang.get_translation('dry_run_report_header'))
    report_content.append(f"{lang.get_translation('dry_run_report_generated_on')} {current_time}")
    report_content.append("=" * 50)
    report_content.append("")

    if not mods_to_update:
        report_content.append(lang.get_translation('dry_run_report_no_updates'))
    else:
        for mod in mods_to_update:
            name_version = f"*** {mod.get('Name', 'Unknown Name')} ({lang.get_translation('dry_run_report_installed')}: v{mod.get('Old_version', 'N/A')} -> {lang.get_translation('dry_run_report_available')}: v{mod.get('New_version', 'N/A')}) ***"
            report_content.append("==============================================================================")
            report_content.append(name_version)

            changelog = mod.get('Changelog')
            if changelog and changelog.strip():
                # Indent changelog for readability
                indented_changelog = '\n'.join([f"    {line}" for line in changelog.splitlines()])
                report_content.append(f"{lang.get_translation('dry_run_report_changelog')}:\n{indented_changelog}")
            else:
                report_content.append(lang.get_translation('dry_run_report_changelog_unavailable'))

            report_content.append("\n")

    # Get logs path from cache and save the file
    logs_path_str = global_cache.config_cache.get('LOGS_PATH')
    if not logs_path_str:
        print("[bold red]Error: Could not find logs path in configuration.[/bold red]")
        return None

    report_file_path = Path(logs_path_str) / "dry_run_report.txt"

    try:
        with open(report_file_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(report_content))
        return str(report_file_path)
    except IOError as e:
        print(f"[bold red]Error writing dry run report: {e}[/bold red]")
        return None

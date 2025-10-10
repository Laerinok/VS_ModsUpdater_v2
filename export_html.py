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

"""
Module to export the list of mods to HTML format.
"""
__author__ = "Laerinok"
__version__ = "2.4.0"
__date__ = "2025-08-24"  # Last update


# export_html.py


import base64
import logging
from pathlib import Path

from rich import print

import config
import global_cache
import lang
from html_generator import generate_basic_table


def format_mods_html_data(mods_data):
    """
    Formats the mod data into HTML rows for the table, embedding icons as Data URLs.

    Args:
        mods_data (dict): A dictionary containing mod data.

    Returns:
        str: A string containing the HTML table rows for the mods.
    """
    rows = []
    for mod in mods_data:
        name = mod.get("Name", "Unknown Name")
        version = mod.get("Local_Version", "")
        description = mod.get("Description", "No description available.")
        icon_binary = mod.get("IconBinary")
        mod_url = mod.get("Mod_url")
        if icon_binary:
            base64_icon = base64.b64encode(icon_binary).decode('utf-8')
            mime_type = "image/png"  # Assuming the icons are in PNG format
            icon_data_url = f"data:{mime_type};base64,{base64_icon}"
            icon_html = f'<td><img src="{icon_data_url}" alt="{name} Icon" width="50" height="50"></td>'
        else:
            icon_html = '<td></td>'

        name_with_link = name
        if mod_url:
            name_with_link = f'<a href="{mod_url}" target="_blank">{name} ({version})</a>'
        row = f'<tr>{icon_html}<td>{name_with_link}</td><td>{description}</td></tr>'
        rows.append(row)
    return ''.join(rows)


def export_mods_to_html():
    """
    Exports the list of installed mods to an HTML file, embedding icons as Data URLs.
    """
    logging_level = global_cache.config_cache.get('LOGGING_LEVEL', 'DEBUG')
    config.configure_logging(logging_level)

    logging.info("Starting mod list export to HTML.")
    try:
        mods_data = sorted(global_cache.mods_data['installed_mods'], key=lambda mod: mod.get('Name', '').lower())
        logging.info(f"Found {len(mods_data)} installed mods.")

        num_installed_mods = len(mods_data)
        mod_table_rows = format_mods_html_data(mods_data)  # Note: icons_folder_path is removed
        basic_html = generate_basic_table(num_installed_mods)
        logging.info("Generated basic HTML structure.")

        insertion_point = basic_html.find("</tbody>")
        if insertion_point != -1:
            html_content = basic_html[:insertion_point] + mod_table_rows + basic_html[insertion_point:]
        else:
            html_content = basic_html
            logging.warning("Could not find '</tbody>' tag in basic HTML. Mod rows might not be inserted correctly.")

        output_folder = global_cache.config_cache['MODLIST_FOLDER']
        output_filename = "modlist.html"
        output_path = Path(output_folder) / output_filename
        logging.info(f"Output path will be: {output_path}")

        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_content)
        print(f"\n[dodger_blue1]{lang.get_translation("export_html_modilst")}[/dodger_blue1]\n[green]{output_path}[/green]")
        logging.info(f"Mod list successfully exported to {output_path}")
    except KeyError as e:
        logging.error(f"Error accessing data: {e}. Check if 'installed_mods' or other necessary keys exist in global_cache.mods_data.")
    except Exception as e:
        logging.error(f"An unexpected error occurred during HTML export: {e}")


if __name__ == '__main__':
    export_mods_to_html()

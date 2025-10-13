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
"""
__author__ = "Laerinok"
__date__ = "2025-08-24"  # Last update


# html_generator.py

import base64
import lang


def get_image_data_url(image_path):
    """Encodes an image file as a Data URL."""
    try:
        with open(image_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode("utf-8")
            mime_type = "image/png"  # Assuming the banner is PNG
            return f"data:{mime_type};base64,{encoded_string}"
    except FileNotFoundError:
        return ""


def generate_basic_table(num_mods):
    """
    Generates a basic HTML structure for a table of mods.

    Args:
        num_mods: The number of installed mods.

    Returns:
        str: A string containing the basic HTML structure of the table.
    """
    base_title = lang.get_translation("export_pdf_installed_mods")
    title = f"Vintage Story - {base_title}"
    banner_data_url = get_image_data_url("assets/banner.png")
    banner_html = f'<img src="{banner_data_url}" alt="Banner" style="display: block; margin-left: auto; margin-right: auto; margin-top: 30px; margin-bottom: 100px; width: 95%; max-width: 1200px;">' if banner_data_url else ""
    footer_text = '<a href="https://mods.vintagestory.at/modsupdater" target="_blank", style="color: black; font-size: 0.8em; text-decoration: none;">ModsUpdater by Laerinok</a>'

    html_table = f"""
    <!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
body {{
    display: flex;
    flex-direction: column;
    align-items: center; /* Center the page content horizontally */
    font-family: sans-serif;
    background-color: #c8dc9f;
    margin: 20px;
    position: relative; /* Important for the absolute positioning of the footer */
    min-height: 100vh; /* Ensures the body takes at least the height of the screen */
    padding-bottom: 60px; /* Adds space at the bottom for the footer */
    box-sizing: border-box; /* Includes padding and border in the width and height */
}}

footer {{
    position: absolute;
    bottom: 10px;
    left: 50%; /* Positionne le bord gauche au centre */
    transform: translateX(-50%); /* Déplace l'élément de la moitié de sa largeur vers la gauche pour le centrer */
    background-color: #f0f5dc;
    padding: 5px 10px;
    border-radius: 5px;
    box-shadow: 1px 1px 3px #888888;
    margin-top: 20px; /* Crée un peu d'espace au-dessus du footer */
}}
        h1 {{
            color: #333;
            text-align: center; /* Center the title */
            margin-bottom: 20px;
        }}
        table {{
            width: 95%; /* Use a percentage for responsiveness */
            max-width: 1200px; /* Set a maximum width for larger screens */
            border-collapse: collapse;
            margin-top: 20px;
            background-color: #f0f5dc; /* Light yellowish-green table background color */
            box-shadow: 2px 2px 5px #888888;
        }}
        th, td {{
            border: 1px solid black; /* Set border color to black */
            padding: 8px;
            text-align: left;
            font-size: 0.9em;
            background-color: white;
        }}
        th {{
            background-color: #f2f2f2;
            font-weight: bold;
            text-align: center;
        }}
        tr:nth-child(even) {{ /* Style for even rows to improve readability */
            background-color: #f9f9f9;
        }}
        a {{ /* Basic style for links */
            color: #007bff;
            text-decoration: none;
        }}
        a:hover {{
            text-decoration: underline;
        }}
        /* Style for the first column (icon) */
        table th:nth-child(1),
        table td:nth-child(1) {{
            width: 100px; /* Set the desired width to 100 pixels */
            text-align: center; /* Center the icon in the column */
        }}
        /* Style for the second column (Name and Version) */
        table th:nth-child(2),
        table td:nth-child(2) {{
            width: 33.33%; /* Approximately 1/3 of the remaining width */
        }}
        /* Style for the third column (Description) */
        table th:nth-child(3),
        table td:nth-child(3) {{
            width: 66.67%; /* Approximately 2/3 of the remaining width */
        }}
    </style>
</head>
<body>
    {banner_html}
    <h1>{num_mods} {base_title}</h1>
    <table>
        <tbody>
        </tbody>
    </table>
    <footer>
        {footer_text}
    </footer>
</body>
</html>
    """
    return html_table


if __name__ == '__main__':
    pass

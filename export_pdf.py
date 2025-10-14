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
This module automates the creation of a PDF document containing a list of Vintage Story mods, including their icons, names, versions, and descriptions. It leverages multithreading to efficiently process mod information and generate a visually appealing PDF.

Key functionalities include:
- Extracting and resizing mod icons from ZIP archives.
- Generating a PDF with a table layout, displaying mod icons, names, versions, and descriptions.
- Using multithreading to accelerate the processing of mod data and icon extraction.
- Incorporating a banner and background image for enhanced visual appeal.
- Adding a footer with a link to the ModsUpdater project.
- Handling potential errors during image processing and PDF creation, with appropriate logging.
- Supporting Cyrillic and other Unicode characters by embedding a suitable font.
- Normalizing strings for case-insensitive sorting of mods by name.
- Retrieving local versions of excluded mods to ensure accurate version display.

"""
__author__ = "Laerinok"
__date__ = "2025-08-25"  # Last update


# export_pdf.py


import concurrent.futures
import logging
import os
import sys
from io import BytesIO
from pathlib import Path

import unicodedata
from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Image, Paragraph, \
    Spacer
from rich import print
from rich.progress import Progress

import config
import global_cache
import lang
from utils import validate_workers, get_default_icon_binary

# Suppress Pillow debug messages
logging.getLogger("PIL").setLevel(logging.WARNING)


def resize_image(image_data, max_size=100):
    """
    Resize the image to fit within the specified max width or height while maintaining the aspect ratio.
    Returns the resized image data in PNG format with compression.
    """
    try:
        image = PILImage.open(BytesIO(image_data))
        width, height = image.size

        if width > max_size or height > max_size:
            if width > height:
                new_width = max_size
                new_height = int(height * (max_size / width))
            else:
                new_height = max_size
                new_width = int(width * (max_size / height))
            image = image.resize((new_width, new_height), PILImage.Resampling.LANCZOS)

        output_io = BytesIO()
        image.save(output_io, format='PNG', optimize=True)
        output_io.seek(0)  # Reset pointer to the beginning
        return output_io.getvalue()  # Return the binary data
    except Exception as e:
        logging.error(f"Error resizing image: {e}")
    return image_data  # Return original data if resizing fails

# Function to create the PDF with Platypus.Table
def create_pdf_with_table(modsdata, pdf_path, args):
    num_mods = global_cache.total_mods
    # Initialize the PDF document
    doc = SimpleDocTemplate(pdf_path,
                            pagesize=A4,
                            leftMargin=20,
                            topMargin=20,
                            rightMargin=20,
                            bottomMargin=20
                            )

    # Add a cyrillic font (for example, DejaVu Sans)
    font_path = Path(config.APPLICATION_PATH) / 'fonts' / 'NotoSansCJKsc-Regular.ttf'
    pdfmetrics.registerFont(TTFont('NotoSansCJKsc-Regular', font_path))

    styles = getSampleStyleSheet()
    style_normal = styles["Normal"]
    style_normal.fontName = "NotoSansCJKsc-Regular"
    style_normal.fontSize = 8
    style_title = styles["Title"]
    style_title.fontName = "NotoSansCJKsc-Regular"
    style_title.textColor = colors.Color(47/255, 79/255, 79/255)  # Vert forêt en RGB normalisé
    style_title.fontSize = 14

    elements = []

    # Add the banner image
    try:
        path_img = Path(config.APPLICATION_PATH) / 'assets' / 'banner.png'
        banner = Image(str(path_img))  # Path to your image
        banner.drawWidth = A4[0] - 40  # Adjust width to fit the page minus margins
        banner.drawHeight = 120  # Adjust height as needed
        elements.append(banner)
    except Exception as e:
        logging.debug(f"Error loading banner image: {e}")

    # Add a space of 50 points below the image
    elements.append(Spacer(1, 50))

    def draw_background(canvas):
        # Path to the background image
        background_path = Path(
            config.APPLICATION_PATH) / 'assets' / 'background.jpg'

        if background_path.exists():
            try:
                # Page Dimensions
                page_width, page_height = A4

                # Direct use of ReportLab to display the image
                canvas.drawImage(
                    str(background_path),
                    0,  # Position X
                    0,  # Position Y
                    width=page_width,
                    height=page_height,
                    preserveAspectRatio=True,
                    mask='auto'  # Transparence
                )
            except Exception as error:
                logging.error(f"Error displaying background image: {error}")
                # Fallback en cas d'échec
                canvas.setFillColorRGB(200 / 255, 220 / 255, 160 / 255)
                canvas.rect(0, 0, A4[0], A4[1], fill=1)
        else:
            # Fallback if the image does not exist
            canvas.setFillColorRGB(200 / 255, 220 / 255, 160 / 255)
            canvas.rect(0, 0, A4[0], A4[1], fill=1)

    # Add a link at the bottom-right corner (footer) of the page
    def draw_footer(canvas):
        # Creating the style for the link
        styles_local = getSampleStyleSheet()
        link_style_custom = styles_local["Normal"].clone("LinkStyle")
        link_style_custom.textColor = colors.black
        link_style_custom.fontSize = 8

        # The footer text
        footer_text = '<a href="https://mods.vintagestory.at/modsupdater">ModsUpdater by Laerinok</a>'
        link_paragraph = Paragraph(footer_text, link_style_custom)

        # Calculating the text size (width and height)
        footer_width, footer_height = link_paragraph.wrap(A4[0] - 475, 100)  # 120 x 100
        text_width = footer_width
        text_height = footer_height
        x_position = A4[0] - text_width - 20
        y_position = 10  # Marge du bas

        # Draw the colored background just behind the text (adjusted size)
        canvas.setFillColorRGB(240 / 255, 245 / 255, 220 / 255)
        canvas.roundRect(x_position, y_position, footer_width, footer_height, radius=10, fill=1)

        # Centered positioning of the text
        link_paragraph.drawOn(canvas,
                              x_position + (footer_width - text_width) / 2 + 15,
                              y_position + (footer_height - text_height) / 2)

    # Title
    elements.append(Paragraph(f"{num_mods} {lang.get_translation("export_pdf_installed_mods")}", style_title))

    # Add a space below the title
    elements.append(Spacer(1, 10))

    # Data for the table: rows
    data = []  # no header (empty table. the first entry is the header)

    # Fill the table with mod data
    for idx, mod_info in enumerate(modsdata.values()):
        # Icon (with direct insertion, not HTML)
        icon = mod_info.get("icon")
        icon_image = None
        if icon:
            try:
                icon_image = Image(icon)
                icon_image.drawWidth = 25
                icon_image.drawHeight = 25
            except Exception as e:
                logging.error(f"Failed to load icon for mod '{mod_info['name']}': {e}")
        else:
            icon_image = ""  # Placeholder if no icon is present

        # Modify the style for links
        link_style = styles["Normal"].clone("LinkStyle")
        link_style.textColor = colors.black  # Set your desired color here
        link_style.fontName = "NotoSansCJKsc-Regular"

        # Name and version with hyperlink
        url = mod_info.get("url_moddb", "")
        if url and url != 'Local mod':
            name_and_version = f'<b><a href="{url}">{mod_info["name"]} (v{mod_info["version"]})</a></b>'
            name_and_version_paragraph = Paragraph(name_and_version,
                                                   link_style)  # Use the custom style for links
        else:
            name_and_version = f"<b>{mod_info['name']}</b> (v{mod_info['version']})"
            name_and_version_paragraph = Paragraph(name_and_version, style_normal)

        # Description
        description = str(mod_info.get('description', ''))
        description_paragraph = Paragraph(description, style_normal)

        # Add the row
        data.append([icon_image, name_and_version_paragraph, description_paragraph])

    # Create the table
    table = Table(data, colWidths=[30, 180, 330])  # Adjust column widths
    table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (0, -1), 'CENTER'),                       # Center horizontal align
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),                      # Middle vertical align
        ('GRID', (0, 0), (-1, -1), 1, colors.black),                 # Grid lines
        ('FONTNAME', (0, 0), (-1, -1), 'NotoSansCJKsc-Regular'),                 # Normal font for rows
        ('FONTSIZE', (0, 0), (-1, 0), 8),                          # Font size
        ('BACKGROUND', (0, 0), (-1, -1), (240/255, 245 / 255, 220 / 255)),  # Alternating row background (light soft green)
    ]))

    # Add the table to the document
    elements.append(table)

    # Check the flag here to decide whether to build the PDF.
    # The `args` object is now passed as a parameter from `generate_pdf`.
    if not args.no_pdf:
        try:
            # Build the PDF
            def draw_background_and_footer(canvas):
                draw_background(canvas)
                draw_footer(canvas)
            doc.build(elements,
                      onFirstPage=lambda canvas, document: draw_background_and_footer(canvas),
                      onLaterPages=lambda canvas, document: draw_background_and_footer(canvas))
            print(f"\n[dodger_blue1]{lang.get_translation("export_pdf_modilst")}[/dodger_blue1]\n[green]{pdf_path}[/green]")
            logging.info(f"PDF successfully created: {pdf_path}")
        except PermissionError as e:
            print(lang.get_translation("export_pdf_permission_error").format(pdf_path=pdf_path))
            logging.error(f"{e} - PermissionError: Unable to access the file '{pdf_path}'. ")
            sys.exit()


def process_mod(mod_info):
    """
    Process to extract mod information and capitalize the first letter of the mod name.
    """
    mod_name = mod_info["Name"].capitalize()
    version = mod_info["Local_Version"]
    icon_binary_data = mod_info.get("IconBinary")

    if not icon_binary_data:
        icon_binary_data = get_default_icon_binary()

    resized_icon_binary_data_pdf = None
    if icon_binary_data:
        resized_icon_binary_data_pdf = resize_image(icon_binary_data, max_size=25)  # Resize for PDF

    return {
        mod_info["ModId"]: {
            "name": mod_name,
            "version": version,
            "description": mod_info["Description"] if mod_info["Description"] is not None else "",
            "url_moddb": mod_info["Mod_url"],
            "icon": BytesIO(resized_icon_binary_data_pdf) if resized_icon_binary_data_pdf else None  # Use resized for PDF
        }
    }


def normalize_string_case_insensitive(s):
    """Normalize a string for case-insensitive sorting."""
    s = s.lstrip()
    return ''.join(c for c in unicodedata.normalize('NFD', s.lower()) if unicodedata.category(c) != 'Mn')


# Main function to orchestrate the PDF generation
def generate_pdf(mod_info_data, args):
    """
    Generates the PDF with a list of mods and their details using multithreading.
    """
    pdf_name = f"modlist.pdf"

    output_dir = Path(global_cache.config_cache.get('MODLIST_FOLDER', '.'))
    os.makedirs(output_dir, exist_ok=True)
    output_pdf_path = str(output_dir / pdf_name)

    logging.info(f"Attempting to save PDF to: {output_pdf_path}")

    # Ensure the directory exists
    Path(output_pdf_path).parent.mkdir(parents=True, exist_ok=True)

    global_cache.total_mods = len(mod_info_data)
    mod_info_for_pdf = {}

    max_workers = validate_workers()

    # The mod processing will always run, but the progress bar will only be displayed
    # if --no-pdf is not used.
    if not args.no_pdf:
        with Progress() as progress:
            task = progress.add_task(
                f"[cyan]{lang.get_translation("export_pdf_generating_file")}",
                total=global_cache.total_mods)

            with concurrent.futures.ThreadPoolExecutor(
                    max_workers=max_workers) as executor:
                futures = [executor.submit(process_mod, mod_info) for mod_info in
                           global_cache.mods_data['installed_mods']]

                for future in concurrent.futures.as_completed(futures):
                    result = future.result()
                    mod_info_for_pdf.update(result)
                    progress.update(task, advance=1)
    else:
        # If PDF generation is disabled, processing runs without a progress bar.
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(process_mod, mod_info) for mod_info in
                       global_cache.mods_data['installed_mods']]

            for future in concurrent.futures.as_completed(futures):
                result = future.result()
                mod_info_for_pdf.update(result)

    sorted_mod_info = dict(sorted(mod_info_for_pdf.items(),
                                  key=lambda item: normalize_string_case_insensitive(
                                      item[1]['name'])))
    # Pass the args object to the function that will handle the PDF creation.
    create_pdf_with_table(sorted_mod_info, output_pdf_path, args)

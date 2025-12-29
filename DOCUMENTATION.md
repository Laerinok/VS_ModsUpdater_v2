# Vintage Story Mods Updater Documentation

This document provides a comprehensive guide to using and developing the Vintage Story Mods Updater application.

## Table of Contents

- [User Guide](#user-guide)
  - [Introduction](#introduction)
  - [Key Features](#key-features)
  - [Installation](#installation)
  - [First-Time Setup](#first-time-setup)
  - [Configuration (`config.ini`)](#configuration-configini)
  - [Command-Line Arguments](#command-line-arguments)
  - [Output Files](#output-files)
  - [Troubleshooting](#troubleshooting)
- [Developer Guide](#developer-guide)
  - [Project Architecture](#project-architecture)
  - [Module Overview](#module-overview)
  - [Development Setup](#development-setup)
  - [Contributing](#contributing)

---

## User Guide

### Introduction

The Vintage Story Mods Updater is a powerful command-line tool designed to simplify the management of your mods for the game Vintage Story. It automates checking for updates, downloading new versions, and maintaining a clean and organized mods folder. Additionally, it can generate detailed lists of your installed mods in various formats.

### Key Features

- **Script Update Check:** Checks if a new version of the ModsUpdater tool is available.
- **Configuration Migration:** Automatically manages the migration of the old configuration file format to the new one, ensuring compatibility during application updates.
- **Update Check:** Compares the local versions of your mods with the latest versions available on ModDB.
- **Automatic Download:** Automatically downloads available updates (configurable).
- **Manual Download:** Displays changelogs and allows you to choose which updates to download.
- **Backup Management:** Creates backups of your mods before updating them, with a configurable retention policy.
- **Excluded Mods Management:** Allows you to ignore certain mods during update checks and downloads.
- **Mod List Generation:** Creates a PDF, JSON, and HTML document listing your installed mods.
- **Command Line Interface (CLI):** Integration with arguments to customize execution.
- **Multilingual Support:** The interface is available in several languages (configurable).

### Installation

1.  Download the latest version of the application for your operating system (Windows or Linux) from the [ModDB page](https://mods.vintagestory.at/modsupdater).
2.  Extract the downloaded archive to a folder of your choice.
3.  (Linux only) Make the `VS_ModsUpdater.AppImage` file executable.

### First-Time Setup

When you run the application for the first time, it will guide you through a setup process:

1.  **Language Selection:** You will be prompted to select your preferred language.
2.  **Mods Directory:** The application will ask you to provide the path to your Vintage Story `Mods` directory. It will suggest a default path, but you can enter a custom one.
3.  **Game Version:** You can specify a target game version. The updater will not download mod versions that are incompatible with this game version.
4.  **Update Mode:** You can choose between automatic or manual updates.

After the initial setup, a `config.ini` file will be created. You can edit this file at any time to change your settings.

### Configuration (`config.ini`)

The `config.ini` file stores all the settings for the application. Here is a detailed explanation of each section and option:

#### `[ModsUpdater]`

-   `version`: The current version of the ModsUpdater application. (Informational)

#### `[Logging]`

-   `log_level`: The level of detail for logs. `DEBUG` is the most verbose. (Options: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`)

#### `[Options]`

-   `exclude_prerelease_mods`: Set to `true` to ignore pre-release versions of mods (e.g., `v1.2.0-rc.1`).
-   `auto_update`: Set to `true` for automatic downloads of updates, or `false` for manual mode.
-   `max_workers`: The maximum number of parallel threads for downloading mods. (Recommended: 1-10)
-   `timeout`: The timeout in seconds for network requests. (Recommended: 5-30)

#### `[Backup_Mods]`

-   `backup_folder`: The directory where backups are stored. Can be a full path.
-   `max_backups`: The maximum number of backups to keep.
-   `modlist_folder`: The directory where the generated mod lists are saved. Can be a full path.

#### `[ModsPath]`

-   `path`: The full path to your Vintage Story `Mods` directory.

#### `[Language]`

-   `language`: The language code for the application's interface (e.g., `en_US`).

#### `[Game_Version]`

-   `user_game_version`: The target game version for mod updates. If left empty, the latest compatible version of a mod will be downloaded.

#### `[Mod_Exclusion]`

-   `mods`: A comma-separated list of mod filenames to exclude from updates (e.g., `mod_a.zip, my_old_mod.cs`).

### Command-Line Arguments

You can override the settings in `config.ini` for a single run using command-line arguments:

-   `--no-pause`: Disables the "Press Enter to exit" message at the end.
-   `--modspath "<path>"`: Specifies a different `Mods` directory.
-   `--no-json`: Disables the generation of the JSON mod list.
-   `--no-pdf`: Disables the generation of the PDF mod list.
-   `--no-html`: Disables the generation of the HTML mod list.
-   `--log-level <level>`: Sets a different logging level.
-   `--max-workers <number>`: Sets a different number of download workers.
-   `--timeout <seconds>`: Sets a different network timeout.

**Example:**

```bash
VS_ModsUpdater.exe --modspath "D:\Vintage Story\mods" --no-pdf
```

### Output Files

The application can generate the following files in the `modlist_folder`:

-   **`modlist.json`**: A machine-readable list of your mods in JSON format.
-   **`modlist.pdf`**: A human-readable PDF document with your mod list, including icons and descriptions.
-   **`modlist.html`**: An HTML page with your mod list, with links to the mods' pages.

### Troubleshooting

-   **"Mods directory not found"**: Make sure the `path` in your `config.ini` or the `--modspath` argument is correct.
-   **"Permission denied"**: Try running the application as an administrator.
-   **Network errors**: Check your internet connection and consider increasing the `timeout` value in `config.ini`.

---

## Developer Guide

### Project Architecture

The application is built with a modular architecture, where each module has a specific responsibility. The core components are:

- **Main Entry Point (`main.py`):** Orchestrates the entire process, from initialization to exit.
- **Configuration (`config.py`):** Handles loading, creating, and migrating the `config.ini` file.
- **Command-Line Interface (`cli.py`):** Parses and validates command-line arguments.
- **Global Cache (`global_cache.py`):** A central, in-memory store for application data, such as configuration, language strings, and mod information.
- **Mod Processing Pipeline:**
  1.  `fetch_mod_info.py`: Scans the mods folder and fetches data from the ModDB API.
  2.  `mods_update_checker.py`: Compares local and remote versions to identify mods that need updating.
  3.  `mods_auto_update.py` / `mods_manual_update.py`: Handle the download and installation of updates.
- **Exporters (`export_*.py`):** Modules responsible for generating the JSON, PDF, and HTML mod lists.
- **Utilities (`utils.py`):** A collection of helper functions used throughout the application.

### Module Overview

This section provides a detailed description of each Python module in the project.

#### `main.py`

-   **Purpose:** The main entry point of the application. It orchestrates the entire process from start to finish.
-   **Key Functions:**
    -   `initialize_config()`: Handles the initial setup and configuration loading.
    -   `welcome_display()`: Displays the welcome message and checks for script updates.
    -   The main execution block (`if __name__ == "__main__":`) calls the different modules in the correct order to perform the mod update process.

#### `cli.py`

-   **Purpose:** Handles the parsing and validation of command-line arguments.
-   **Key Functions:**
    -   `parse_args()`: Uses `argparse` to define and parse the command-line arguments.

#### `config.py`

-   **Purpose:** Manages the `config.ini` file, including its creation, loading, and migration.
-   **Key Functions:**
    -   `load_config()`: Reads the `config.ini` file and populates the `global_cache`.
    -   `create_config()`: Creates a new `config.ini` file during the first-time setup.
    -   `migrate_config_if_needed()`: Checks the configuration version and runs the migration logic if necessary.

#### `fetch_mod_info.py`

-   **Purpose:** Gathers all necessary information about the installed mods.
-   **Key Functions:**
    -   `scan_and_fetch_mod_info()`: The main function that scans the mods directory, reads local mod data, and fetches additional information from the ModDB API.
    -   `get_modinfo_from_zip()` and `get_cs_info()`: Extract metadata from mod files.
    -   `get_mod_api_data()`: Fetches data for a single mod from the API.

#### `mods_update_checker.py`

-   **Purpose:** Compares the local mod versions with the latest available versions to find updates.
-   **Key Functions:**
    -   `check_for_mod_updates()`: Iterates through the installed mods and identifies which ones have updates.

#### `mods_auto_update.py`

-   **Purpose:** Handles the automatic download and installation of mod updates.
-   **Key Functions:**
    -   `download_mods_to_update()`: Downloads all the mods that have updates available.
    -   `resume_mods_updated()`: Displays a summary of the updated mods.

#### `mods_manual_update.py`

-   **Purpose:** Handles the manual, interactive update process.
-   **Key Functions:**
    -   `perform_manual_updates()`: Prompts the user for each mod update and downloads the selected ones.

#### `export_json.py`, `export_pdf.py`, `export_html.py`

-   **Purpose:** These modules are responsible for exporting the list of installed mods to different formats.
-   **Key Functions:** They each have a main function (`format_mods_data`, `generate_pdf`, `export_mods_to_html`) that takes the mod data and generates the corresponding output file.

#### `html_generator.py`

-   **Purpose:** Provides the HTML template for the `export_html.py` module.
-   **Key Functions:**
    -   `generate_basic_table()`: Returns a string with the basic HTML structure.

#### `utils.py`

-   **Purpose:** A collection of various helper functions used throughout the application.
-   **Key Functions:** Includes functions for file system operations, data validation, version comparison, and more.

#### `lang.py`

-   **Purpose:** Handles language translations.
-   **Key Functions:**
    -   `load_translations()`: Loads a language file from the `lang` directory.
    -   `get_translation()`: Retrieves a specific translation string.

#### `http_client.py`

-   **Purpose:** A wrapper around an HTTP client library (`requests`) to handle network requests.

#### `global_cache.py`

-   **Purpose:** Defines the global cache objects (`config_cache`, `language_cache`, `mods_data`, `modinfo_json_cache`) that are used to store data in memory and share it between modules.

### Development Setup

1.  Clone the repository from GitHub.
2.  Install the required Python dependencies: `pip install -r requirements.txt`.
3.  Run the application from the command line: `python main.py`.

### Contributing

Contributions are welcome! If you want to contribute to the project, please follow these steps:

1.  Fork the repository.
2.  Create a new branch for your feature or bug fix.
3.  Make your changes.
4.  Submit a pull request.

If you are adding a new language, you can create a new JSON file in the `lang` directory, following the structure of the existing language files.

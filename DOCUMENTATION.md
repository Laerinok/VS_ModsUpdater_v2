# Vintage Story Mods Updater Documentation

This document provides a comprehensive guide to using and developing the Vintage Story Mods Updater application (v2.5.0+).

## Table of Contents

- [User Guide](#user-guide)
  - [Introduction](#introduction)
  - [Key Features](#key-features)
  - [File Locations](#file-locations)
  - [Installation & Setup](#installation--setup)
    - [Windows](#windows)
    - [Linux (AppImage & Desktop Integration)](#linux-appimage--desktop-integration)
    - [macOS](#macos)
  - [First-Time Setup](#first-time-setup)
  - [How Mods Are Handled (Zip vs. Directory)](#how-mods-are-handled-zip-vs-directory)
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

The Vintage Story Mods Updater is a powerful command-line tool designed to simplify the management of your mods for the game Vintage Story. It automates checking for updates, downloading new versions, maintaining a clean mods folder, and managing compatibility with specific game versions.

### Key Features

- **Script Update Check:** Checks if a new version of the ModsUpdater tool is available.
- **Configuration Migration:** Automatically manages the migration of old configuration files to the new format.
- **Update Check:** Compares local mod versions with the latest versions on ModDB.
- **Smart Incompatibility Handling:**
  - **Downgrade Support:** Offers to downgrade a mod if the installed version is too new for your game version.
  - **Incompatibility Warning:** Alerts you if a mod is incompatible with your defined game version.
- **Automatic Download:** Automatically downloads available updates (configurable).
- **Manual Download:** Displays changelogs and allows you to choose which updates to download.
- **Backup Management:** Creates backups of your mods before updating them, with a configurable retention policy.
- **Detailed Exclusion Management:** Allows you to ignore certain mods. The summary explains *why* a mod was excluded (User config, API missing, etc.).
- **Mod List Generation:** Creates PDF, JSON, and HTML documents listing your installed mods.
- **Command Line Interface (CLI):** robust arguments to customize execution, including "Dry Run" and "Force Update" modes.
- **Multilingual Support:** The interface is available in over 10 languages.

### File Locations

The location of configuration and data files differs between operating systems to follow platform standards.

| File / Directory | Windows Location | Linux & macOS Location |
| :--- | :--- | :--- |
| **`config.ini`** | Same directory as `.exe` | `~/.config/VS_ModsUpdater/config.ini` |
| **`logs/`** | Same directory as `.exe` | `~/.local/share/VS_ModsUpdater/logs/` |
| **`backup_mods/`** | Same directory as `.exe` | `~/.local/share/VS_ModsUpdater/backup_mods/` |
| **`modlist/`** | Same directory as `.exe` | `~/.local/share/VS_ModsUpdater/modlist/` |

> **Note:**
> - On Linux/macOS, these paths respect `XDG_CONFIG_HOME` and `XDG_DATA_HOME` environment variables if set.
> - **You can override the default location of `config.ini` by using the `--config-path` command-line argument.**

### Installation & Setup

#### Windows
1.  Download the latest `.zip` from the [ModDB page](https://mods.vintagestory.at/modsupdater).
2.  Extract the archive to a folder of your choice.
3.  Run `VS_ModsUpdater.exe`.

#### Linux (AppImage & Desktop Integration)
1.  Download the `VS_ModsUpdater.AppImage` from ModDB or GitHub.
2.  Make the file executable: `chmod +x VS_ModsUpdater.AppImage`.
3.  **Desktop Integration:** To verify or add the application to your system menu:
    - Place the AppImage and the `vs-mods-updater.desktop` file (provided in the release) in the same directory.
    - (Optional) Move the `.desktop` file to `~/.local/share/applications/` to make it appear in your launcher.

#### macOS
**Note:** The macOS version is built automatically via GitHub Actions and is provided "as is" without direct testing by the author (due to lack of hardware).
1.  Download the binary from the **GitHub Releases** page (due to file size limits on ModDB).
2.  Extract and run via terminal.

### First-Time Setup

When you run the application for the first time, it will guide you through a setup process:

1.  **Language Selection:** Select your preferred interface language.
2.  **Mods Directory:** Provide the path to your Vintage Story `Mods` directory.
3.  **Game Version:** Specify your target game version (e.g., `1.20.1`). The updater will use this to determine mod compatibility.
4.  **Update Mode:** Choose between automatic or manual updates.

### How Mods Are Handled (Zip vs. Directory)

The updater is flexible and supports mods in different formats:

-   **.zip Files**: Standard format. The updater replaces the old `.zip` with the new one.
-   **.cs Files**: Simple code mods. Replaced directly.
-   **Directories**: Supported primarily for **Mod Organizer 2** users.
    - The updater identifies a folder as a mod if it contains a `modinfo.json`.
    - **Important:** When updating a directory mod, the **contents** are replaced, but the **folder name remains unchanged**. This ensures compatibility with mod managers that rely on specific folder naming (e.g., preserving the `modid`).

### Configuration (`config.ini`)

The `config.ini` file stores all settings.

#### `[ModsUpdater]`
-   `version`: The current version of the application. (Informational)

#### `[Logging]`
-   `log_level`: Detail level for logs. Options: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`.

#### `[Options]`
-   `exclude_prerelease_mods`: `true` to ignore beta/rc versions.
-   `auto_update`: `true` for automatic downloads, `false` for manual selection.
-   `max_workers`: Max parallel threads for downloading. (Limit: 10).
-   `timeout`: Timeout in seconds for network requests. (Recommended: 5-30).
-   `incompatibility_behavior`: Defines how to handle mods incompatible with `user_game_version`.
    - `0` (Ask): Prompts the user for action. (Default)
    - `1` (Abort): Stops the process if incompatibility is found.
    - `2` (Ignore): Continues processing, ignoring the warning.

#### `[Backup_Mods]`
-   `backup_folder`: Directory for backups. Can be a name (relative) or full path.
-   `max_backups`: Number of backups to keep before deleting old ones.
-   `modlist_folder`: Directory for generated mod lists.

#### `[ModsPath]`
-   `path`: The full path to your Vintage Story `Mods` directory.

#### `[Language]`
-   `language`: The language code (e.g., `en_US`, `fr_FR`).

#### `[Game_Version]`
-   `user_game_version`: The target game version (e.g., `1.20.4`).
    - If set, mods requiring a newer game version will be skipped or flagged.
    - If empty or `latest_version`, the absolutely latest mod version is fetched, regardless of game compatibility.

#### `[Mod_Exclusion]`
-   `mods`: A comma-separated list of filenames to ignore (e.g., `mod_a.zip, my_old_mod.cs`).

### Command-Line Arguments

Override `config.ini` settings or trigger specific modes for a single run:

-   `--modspath "<path>"`: Specifies a different `Mods` directory.
-   `--config-path "<path>"`: Specifies a custom configuration file location (useful for multi-instance servers).
-   `--install-modlist`: Downloads and installs mods listed in `modlist.json` to the mods folder.
-   `--force-update`: Forces a re-download/re-install of all mods, regardless of version comparison.
-   `--dry-run`: Simulates the update process (checks versions and incompatibilities) without downloading or deleting files.
-   `--no-pause`: Disables the "Press Enter to exit" message.
-   `--no-json` / `--no-pdf` / `--no-html`: Disables generation of specific mod list formats.
-   `--log-level <level>`: Overrides logging level.
-   `--max-workers <number>`: Overrides thread count.
-   `--timeout <seconds>`: Overrides network timeout.

**Example:**
```bash
# Run a simulation using a specific config file
VS_ModsUpdater.exe --config-path "C:\Server1\config.ini" --dry-run
```

### Output Files

Files generated in the `modlist_folder`:
-   **`modlist.json`**: Machine-readable mod data.
-   **`modlist.pdf`**: Visual document with icons and descriptions.
-   **`modlist.html`**: Web-viewable list with direct links.

### Troubleshooting

-   **"Mods directory not found"**: Check the `path` in `config.ini` or your `--modspath` argument.
-   **Network errors**: Increase the `timeout` value in `config.ini` if your connection is slow.

---

## Developer Guide

### Project Architecture

The application uses a modular architecture:

- **Entry & Config:** `main.py` (entry point), `config.py` (settings management), `cli.py` (argument parsing).
- **Core Logic:**
  - `fetch_mod_info.py`: Scans directories and queries the ModDB API.
  - `mods_update_checker.py`: Logic for version comparison and compatibility checks.
  - `mods_auto_update.py` / `mods_manual_update.py`: Execution of download and installation.
- **Data & Utils:**
  - `global_cache.py`: Shared memory state (config, mod data).
  - `utils.py`: Helper functions (File I/O, Zip handling, Version parsing).
  - `lang.py`: Internationalization system.
- **Exporters:** `export_json.py`, `export_pdf.py`, `export_html.py`.

### Module Overview

#### `main.py`
Orchestrates the lifecycle. Initializes config, checks for self-updates, and calls the update pipeline.

#### `cli.py`
Defines `argparse` logic. now handles complex flags like `--force-update` and `--dry-run` to modify global state before execution.

#### `fetch_mod_info.py`
Enhanced in v2.x to handle `InvalidVersion` exceptions and perform robust API lookups. It populates `global_cache.mods_data`.

#### `utils.py`
Contains critical file handling.
- **Key Update:** `backup_mods` now uses `strict_timestamps=False` to prevent crashes on Linux systems with zero-epoch file dates.
- **Key Update:** `get_latest_game_version` iterates backwards to find the latest *valid* semantic version from the API.

#### `mods_update_checker.py`
Implements the logic for `VersionCompareState`. It determines if a mod is `LOCAL_VERSION_BEHIND`, `AHEAD`, or `IDENTICAL`, and checks against `user_game_version`.

### Development Setup

1.  Clone the repository.
2.  Install dependencies: `pip install -r requirements.txt`.
3.  Run: `python main.py`.

### Contributing

1.  Fork the repository.
2.  Create a feature branch.
3.  Submit a Pull Request.
4.  **Translations:** Add new JSON files to the `/lang/` directory to support new languages.
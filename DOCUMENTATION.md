# Vintage Story Mods Updater Documentation

This document provides a comprehensive guide to using and developing the Vintage Story Mods Updater application (v2.6.0+).

## Table of Contents

- [User Guide](#user-guide)
  - [Introduction](#introduction)
  - [Key Features](#key-features)
  - [File Locations & Profiles](#file-locations--profiles)
  - [Installation & Setup](#installation--setup)
    - [Windows](#windows)
    - [Linux (AppImage & Desktop Integration)](#linux-appimage--desktop-integration)
    - [macOS](#macos)
  - [First-Time Setup](#first-time-setup)
  - [How Mods Are Handled (Zip vs. Directory)](#how-mods-are-handled-zip-vs-directory)
  - [Configuration (config.ini)](#configuration-configini)
    - [[ModsUpdater]](#modsupdater)
    - [[Logging]](#logging)
    - [[Options]](#options)
    - [[Backup_Mods]](#backup_mods)
    - [[ModsPath]](#modspath)
    - [[Language]](#language)
    - [[Game_Version]](#game_version)
    - [[Mod_Exclusion]](#mod_exclusion)
  - [Command-Line Arguments](#command-line-arguments)
  - [Output Files](#output-files)
  - [Troubleshooting](#troubleshooting)
- [Developer Guide](#developer-guide)
  - [Project Architecture](#project-architecture)
  - [Module Overview](#module-overview)
    - [main.py](#mainpy)
    - [cli.py](#clipy)
    - [fetch_mod_info.py](#fetch_mod_infopy)
    - [utils.py](#utilspy)
    - [mods_update_checker.py](#mods_update_checkerpy)
  - [Development Setup](#development-setup)
  - [Contributing](#contributing)

---

## User Guide

### Introduction

The Vintage Story Mods Updater is a standalone command-line utility designed to automate the management of your Vintage Story game mods. It interfaces directly with the Vintage Story ModDB API to check for updates, verify compatibility with your targeted game version, safely backup old mod versions, and clean up any residue to prevent conflicts.

### Key Features

* **Multi-Profile Support:** Isolate different configurations, modlists, backups, and logs for multiple server or client instances using separate profiles.
* **Auto-Migration:** Automatically migrates legacy config files and asset folders into the new structured profile-based directories.
* **Compatibility & Downgrading:** Safely alerts you to incompatible mods and can automatically offer to downgrade a mod if your installed version is too new for the selected game version.
* **Auto-Clearing Cache:** Automatically deletes the local Vintage Story game cache after updating mods to prevent texture errors or startup crashes.
* **Detailed Logs & Summaries:** Generates clean command-line outputs, session log files, and rich mod summaries including reasons for exclusion.
* **Mod List Generation:** Exports details of your installed mods into PDF, HTML, and JSON formats.

### File Locations & Profiles

To support multiple game/server instances, all settings and files are organized into **profiles**. By default, the application loads the `default` profile. 

All files associated with a profile (configuration, logs, backups, reports) are stored inside its respective profile directory.

#### Profile Folder Locations

| Platform | Profile Root Directory | Active Default Profile Directory |
| :--- | :--- | :--- |
| **Windows** | `profiles/` (relative to the executable) | `profiles/default/` |
| **Linux & macOS** | `~/.config/VS_ModsUpdater/profiles/` | `~/.config/VS_ModsUpdater/profiles/default/` |

#### Files within a Profile Directory

Unless an absolute path is explicitly defined in `config.ini`, the following files reside inside the active profile directory (e.g., `profiles/{profile_name}/`):

* **`config.ini`:** The localized configuration file for the profile.
* **`logs/`:** Folder containing execution log files (e.g., `updater.log`).
* **`backup_mods/`:** Directory holding zip archives of mods backed up prior to an update.
* **`modlist/`:** Directory holding exported mod list files (JSON, PDF, HTML).

> **Note:** On Linux and macOS, these paths respect the `XDG_CONFIG_HOME` and `XDG_DATA_HOME` environment variables if set.

---

### Installation & Setup

#### Windows

1. Download the latest release `.zip` from the [ModDB project page](https://mods.vintagestory.at/modsupdater).
2. Extract the archive to a folder of your choice (do not place the application inside the Vintage Story mods directory itself).
3. Run `VS_ModsUpdater.exe`.

#### Linux (AppImage & Desktop Integration)

1. Download the `VS_ModsUpdater.AppImage` and `vs-mods-updater.desktop` files.
2. Make the AppImage executable:
   ```bash
   chmod +x VS_ModsUpdater.AppImage
3. To integrate the updater into your desktop application menu, place the `vs-mods-updater.desktop` file into `~/.local/share/applications/` and verify the icon and executable paths inside the file align with your AppImage location.

#### macOS

The macOS release is built automatically via GitHub Actions and is provided "as is" on the GitHub Releases page (due to upload limits on ModDB). Extract the archive and launch the binary via your terminal.

---

### First-Time Setup

On its initial run, the updater initiates an interactive setup process in the console:

1. **Language Selection:** Choose your interface language from over 10 supported options.
2. **Mods Directory Location:** Specify the absolute path to your Vintage Story `Mods` directory.
3. **Cache Directory Location:** The application automatically attempts to detect your local game cache path. You will be prompted to confirm or specify it.
4. **Target Game Version:** Choose your target game version (or select the default `latest_stable_version`).
5. **Update Mode:** Decide between automatic downloads or a manual prompt system.

---

### How Mods Are Handled (Zip vs. Directory)

The updater handles mods in various formats:

* **`.zip` files:** The standard format. The updater compares metadata, downloads the new file, and deletes the older `.zip` file from your mods folder.
* **`.cs` files:** Plain C# script mods are verified and updated directly.
* **Directories (Folders):** Intended primarily for Mod Organizer 2 users. A folder is recognized as a mod if it contains a valid `modinfo.json`. When updated, the contents of the directory are overwritten, but the folder name remains unchanged to preserve stability for external managers.

---

### Configuration (config.ini)

Each profile folder contains its own `config.ini` file.

#### [ModsUpdater]

* **`version`**: Current version of the application (e.g., `2.6.0`).

#### [Logging]

* **`log_level`**: Sets the level of logging detail recorded in `logs/updater.log`. Options: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`.

#### [Options]

* **`exclude_prerelease_mods`**: `true` to exclude pre-release mod versions, `false` to include them.
* **`auto_update`**: `true` to download updates automatically; `false` to prompt the user before each download.
* **`max_workers`**: Maximum number of parallel threads used for downloading mods (min `1`, max `10`).
* **`timeout`**: Timeout limit in seconds for network API requests.
* **`incompatibility_behavior`**: Actions to take when a mod is incompatible with the target game version:
  * `0` (Ask): Prompt the user on how to proceed.
  * `1` (Abort): Terminate the updater execution safely.
  * `2` (Ignore): Proceed with the update loop despite the mismatch warning.
* **`clear_cache_after_update`**: `true` to automatically purge the Vintage Story cache folder upon successful updates, reducing UI or texture glitch risks.

#### [Backup_Mods]

* **`backup_folder`**: Relative path (inside the profile folder) or absolute path where old mods are zipped up before being updated.
* **`max_backups`**: Maximum number of mod backup archives to retain. Set to `0` to disable automatic cleanup.
* **`modlist_folder`**: Directory where generated mod lists are exported.

#### [ModsPath]

* **`path`**: Absolute path to your Vintage Story `Mods` folder.
* **`cache_path`**: Absolute path to your Vintage Story `Cache` directory (crucial if `clear_cache_after_update` is enabled).

#### [Language]

* **`language`**: The active language locale code (e.g., `en_US`, `fr_FR`, `de_DE`).

#### [Game_Version]

* **`user_game_version`**: The game version target for mod updates:
  * Set to `latest_stable_version` (Default) to update only to mods compatible with the newest stable release.
  * Set a specific version (e.g., `1.20.1`) to pin updates to that version.
  * Set to `latest_version` to target absolute newest releases, including experimental pre-releases or release candidates.

#### [Mod_Exclusion]

* **`mods`**: Comma-separated list of mod filenames (e.g., `mod_a.zip, old_mod.cs`) to completely ignore during checks and updates.

---

### Command-Line Arguments

Execute the updater from the command line with the following options to customize or override settings for a single execution:

| Argument | Description |
| :--- | :--- |
| `--config-path <path_or_profile>` | Specify a custom path to a configuration file or a simple profile name (e.g., `--config-path server1` automatically resolves to `profiles/server1/config.ini`). |
| `--modspath "<path>"` | Temporarily override the configured Vintage Story mods directory. Must be enclosed in quotation marks if the path contains spaces. |
| `--no-pause` | Disable the "Press any key to exit..." console pause at the end of the script execution (useful for automated scripts). |
| `--no-json` | Disable the automatic generation of the mod list in JSON format at the end of execution. |
| `--no-pdf` | Disable the automatic generation of the mod list in PDF format at the end of execution. |
| `--no-html` | Disable the automatic generation of the mod list in HTML format at the end of execution. |
| `--log-level <level>` | Override the logging level for this run. Options: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL` (must be uppercase). |
| `--max-workers <num>` | Override the maximum concurrent thread count used for mod downloads (min `1`, max `10`). |
| `--timeout <secs>` | Override the HTTP request timeout threshold in seconds during update checks and downloads. |
| `--dry-run` | Run a simulated trial. Checks for updates and potential incompatibilities without downloading or modifying any files. |
| `--only-modlist` | Skip checking or downloading updates entirely; immediately generate and export the mod lists (JSON, PDF, HTML) based on currently installed mods, then exit. |
| `--force-update` | Force a complete re-download and re-installation of all mods matching the target game version, regardless of their current status. |
| `--install-modlist` | Read your local `modlist.json` file and download clean versions of all listed mods directly into your target mods folder. |
---

### Output Files

Upon execution, the updater can write several files to your profile folder:

* **`logs/updater.log`**: Detailed traceback, debug, and network events.
* **`updated_mods_changelog.txt`**: Saved in your active profile directory, this document aggregates the release notes/changelogs of all mods updated during the execution.
* **`modlist/modlist.json`**: Structural JSON document representing all currently active local mods and versions.
* **`modlist/modlist.html`**: Interactive web page listing active mods.
* **`modlist/modlist.pdf`**: Styled document list summarizing your active mods.

---

### Troubleshooting

* **Crash due to timestamp errors (Linux/macOS):** Ensure you are using v2.5.0+. Older versions crashed during backup creation on Linux because zip files did not support file modification timestamps prior to 1980.
* **Application closes instantly on Linux:** This occurs when executed directly via double-click and the script has no active updates to perform. Run the AppImage from an active terminal context (`./VS_ModsUpdater.AppImage`) to inspect the final summary output.
* **Mod conflicts or visual issues after updating:** Ensure `clear_cache_after_update` is set to `true` inside your configuration file, or delete your Vintage Story game cache manually.

---

## Developer Guide

### Project Architecture

The application is built in Python. When packaged for distribution, PyInstaller bundle scripts package the runtime dependencies, platform-specific icons, and translation files (`lang/*.json`) into standalone executables.

The update pipeline flow:

1. **CLI Parsing:** `cli.py` handles input arguments.
2. **Config Initialization:** `config.py` runs, verifying profile folders. It handles automatic migrations from legacy configurations.
3. **Scanning & Local Check:** The mods directory is scanned. Mod files are parsed to extract metadata.
4. **API Sync:** `fetch_mod_info.py` makes parallel requests to ModDB, fetching mod profiles and sorting eligible version tables.
5. **Logic Resolution:** `mods_update_checker.py` evaluates versions (updating, downgrading, or marking exclusions), filtering out user-specified ignore lists.
6. **Execution:** Backups are written, files are replaced, cache is cleaned, and reports are compiled.

### Module Overview

#### main.py

The orchestrator. Initializes profiling, config migration, updates checks, self-update validations, file actions, and report triggers.

#### cli.py

Defines options, overrides defaults, validates inputs, and maps CLI-defined profile names to the active directories.

#### fetch_mod_info.py

Provides thread-safe utilities to query ModDB JSON API, formats version records, validates semantic version strings, and catches network failures.

#### utils.py

A comprehensive utility library that handles semantic version comparisons, operating system specific directory defaults, localized console messages, file structure validation, and directory manipulation.

#### mods_update_checker.py

Centralizes update logic comparisons, handles complex version pinning requirements, assesses compatibility parameters, and constructs lists of files designated for upgrade/downgrade.

---

### Development Setup

1. **Clone the repository:**
   ```bash
   git clone -b dev https://github.com/Laerinok/VS_ModsUpdater_v2.git
   cd VS_ModsUpdater_v2
   ```
2. **Create and activate a virtual environment:**
   ```bash
   python -m venv venv
   ```
   * **On Windows:**
     ```cmd
     venv\Scripts\activate
     ```
   * **On Linux/macOS:**
     ```bash
     source venv/bin/activate
     ```
3. **Install package dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
4. **Run the program locally:**
   ```bash
   python main.py
   ```

---

### Contributing

Pull Requests must be targeted against the `dev` branch. Please ensure all modifications conform to clean code standards and preserve compatibility with Windows, Linux (AppImage), and macOS compilation patterns.
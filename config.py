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
# Manage configuration using a global cache.
"""


__author__ = "Laerinok"
__version__ = "2.4.0"  # Don't forget to change EXPECTED_VERSION
__date__ = "2025-10-11"  # Last update


# config.py

import configparser
import logging
import os
import platform
import shutil
from pathlib import Path

from rich import print

import global_cache
import lang
import utils

# The target version after migration
EXPECTED_VERSION = "2.4.0"

# Variable to enable/disable the download - for my test
download_enabled = True  # Set to False to disable downloads

# Constant for os
SYSTEM = platform.system()
HOME_PATH = Path.home()
XDG_CONFIG_HOME_PATH = os.getenv('XDG_CONFIG_HOME', os.path.expanduser('~/.config'))

MODS_PATHS = {
    "Windows": Path(HOME_PATH) / 'AppData' / 'Roaming' / 'VintagestoryData' / 'Mods',
    "Linux": Path(XDG_CONFIG_HOME_PATH) / 'VintagestoryData' / 'Mods'
}

# Retrieve the application directory from the APPDIR environment variable
appdir = os.environ.get('APPDIR')

if appdir:
    APPLICATION_PATH = Path(appdir)
else:
    # Case where the application is run outside the AppImage (for development)
    APPLICATION_PATH = Path.cwd()

APP_NAME = "VS_ModsUpdater"
USER_CONFIG_DIR = Path.home() / ".config" / APP_NAME
USER_DATA_DIR = Path.home() / ".local" / "share" / APP_NAME
USER_CACHE_DIR = Path.home() / ".cache" / APP_NAME

# Retrieve the application directory
appdir = os.environ.get('APPDIR')
if appdir:
    APPLICATION_PATH = Path(appdir)
else:
    APPLICATION_PATH = Path.cwd()

# Constants for paths
if SYSTEM == "Windows":
    CONFIG_FILE = APPLICATION_PATH / 'config.ini'
    TEMP_PATH = APPLICATION_PATH / 'temp'
    LOGS_PATH = APPLICATION_PATH / 'logs'
    BACKUP_FOLDER = APPLICATION_PATH / 'backup_mods'
    MODLIST_FOLDER = APPLICATION_PATH / 'modlist'
else:  # Linux or other systems (where AppImage will run)
    CONFIG_FILE = USER_CONFIG_DIR / 'config.ini'
    TEMP_PATH = USER_CACHE_DIR / 'temp'
    LOGS_PATH = USER_DATA_DIR / 'logs'
    BACKUP_FOLDER = USER_DATA_DIR / 'backup_mods'
    MODLIST_FOLDER = USER_DATA_DIR / 'modlist'

LANG_PATH = APPLICATION_PATH / 'lang'

# Constants for supported languages
# The following dictionary defines the languages supported by the application.
# To add a new language, add a new entry with the country code as the key
# and a list containing the language code (e.g., "en") and the language name
# (e.g., "English") as the value.
# The numeric index for user selection is generated automatically.
_languages_to_process = {
    "DE": ["de", "Deutsch"],
    "US": ["en", "English"],
    "ES": ["es", "Español"],
    "FR": ["fr", "Français"],
    "IT": ["it", "Italiano"],
    "JP": ["ja", "日本語"],
    "KR": ["ko", "한국어"],
    "PL": ["pl", "Polski"],
    "BR": ["pt", "Português (Brasil)"],
    "PT": ["pt", "Português (Portugal)"],
    "RU": ["ru", "Русский"],
    "UA": ["uk", "Yкраїнська"],
    "CN": ["zh", "简体中文"],
}

# Sort by language code (value[0]), then by country code (key) for stability.
# This ensures a consistent order for the user, regardless of how the dictionary
# is defined above.
_sorted_languages = sorted(_languages_to_process.items(), key=lambda item: (item[1][0], item[0]))

# Dynamically create the final SUPPORTED_LANGUAGES dictionary with numeric indices.
# This avoids having to manually re-number languages when adding or removing one.
SUPPORTED_LANGUAGES = {
    key: value + [str(i)]
    for i, (key, value) in enumerate(_sorted_languages, 1)
}
DEFAULT_LANGUAGE = "en_US"

# Constants for url
URL_BASE_MOD_API = "https://mods.vintagestory.at/api/mod/"
URL_BASE_MOD_DOWNLOAD = "https://moddbcdn.vintagestory.at/"
URL_BASE_MODS = 'https://mods.vintagestory.at/'
URL_MOD_DB = "https://mods.vintagestory.at/show/mod/"
URL_SCRIPT = {
    "windows": 'https://mods.vintagestory.at/api/mod/1403',
    "linux": 'https://mods.vintagestory.at/api/mod/1525'
}

# Default configuration
DEFAULT_CONFIG = {
    "ModsUpdater": {"version": __version__},
    "Logging": {"log_level": "DEBUG"},
    # Dans DEFAULT_CONFIG
    "Options": {"exclude_prerelease_mods": "false", "auto_update": "true", "max_workers": str(4), "timeout": str(10), "incompatibility_behavior": "0"},
    "Backup_Mods": {"backup_folder": "backup_mods", "max_backups": str(3), "modlist_folder": "modlist"},
    "ModsPath": {"path": MODS_PATHS[SYSTEM]},
    "Language": {"language": DEFAULT_LANGUAGE},
    "Game_Version": {"user_game_version": "latest_version"},
    "Mod_Exclusion": {'mods': ""}
}

# Mapping for renamed sections or options
RENAME_MAP = {
    "Game_Version_max": "user_game_version",
    "ModPath": "ModsPath",
    "ver": "version",
    "disable_mod_dev": "exclude_prerelease_mods",
    "mod1": "mods",
    "mod2": "mods",
    "mod3": "mods",
    "mod4": "mods",
    "mod5": "mods",
    "mod6": "mods",
    "mod7": "mods",
    "mod8": "mods",
    "mod9": "mods",
    "mod10": "mods",
}

# Static list of User-Agents
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:115.0) Gecko/20100101 Firefox/115.0",
]


def rename_old_config(config_file_path):
    """
    Renames the old config.ini file to config.old with error handling.

    Args:
        config_file_path (Path): The path to the config.ini file.
    """
    old_config_path = config_file_path.with_suffix(".old")
    try:
        if config_file_path.exists():
            shutil.move(str(config_file_path), str(old_config_path))  # Using shutil.move for more robustness
            logging.info(f"Old configuration file renamed to '{old_config_path.name}'.")
        else:
            logging.info(f"Configuration file '{config_file_path.name}' not found, no action needed.")
    except FileNotFoundError:
        logging.error(f"Error: Source file '{config_file_path.name}' not found during renaming.")
    except PermissionError:
        logging.error(f"Error: Permission denied while renaming '{config_file_path.name}' to '{old_config_path.name}'. Ensure the file is not open and you have the necessary permissions.")
    except OSError as e:
        logging.error(f"System error occurred while renaming '{config_file_path.name}' to '{old_config_path.name}': {e}")
    except Exception as e:
        logging.error(f"An unexpected error occurred while renaming '{config_file_path.name}' to '{old_config_path.name}': {e}")


def read_version_from_config_file():
    config_parser = configparser.ConfigParser()
    config_parser.read(CONFIG_FILE, encoding='utf-8')  # Read the configuration file
    return config_parser.get('ModsUpdater', 'version', fallback=None)


def migrate_config_if_needed():
    current_version = read_version_from_config_file()  # Function to read the version from config.ini
    if current_version != EXPECTED_VERSION:
        # If the configuration version is outdated, initiate the migration
        old_config = configparser.ConfigParser()
        old_config.read(CONFIG_FILE, encoding='utf-8')  # Read the current configuration file
        rename_old_config(CONFIG_FILE)
        migrate_config(old_config)  # Migrate the configuration to the new version
        return True  # Migration done
    return False  # Migration not done


def migrate_config(old_config):
    """
    Migrate the configuration from an old version to the new format.
    - Ensures all sections and options from DEFAULT_CONFIG are present.
    - Preserves user-defined values when possible.
    - Renames or modifies settings when necessary.
    - Removes obsolete keys.
    - Keeps the order of sections and keys as defined in DEFAULT_CONFIG.
    """
    new_config = configparser.ConfigParser()

    logging.info("Starting migration process of old config.ini...")

    # Step 1: Update the version
    new_config["ModsUpdater"] = {"version": EXPECTED_VERSION}
    logging.debug("Set ModsUpdater version to %s", EXPECTED_VERSION)

    # Step 2: Copy existing values and add missing ones while maintaining order
    for section, default_options in DEFAULT_CONFIG.items():
        new_config[section] = {}

        if section in old_config:
            # Copy existing values while keeping the order from DEFAULT_CONFIG
            for key in default_options.keys():
                new_config[section][key] = old_config[section].get(key,
                                                                   default_options[key])
        else:
            # Add missing sections with default values
            new_config[section] = default_options.copy()

    # Step 3: Apply specific migration rules
    # - Rename sections/keys if necessary

    # Migration: version → version
    if "ModsUpdater" in old_config and "version" in old_config["ModsUpdater"]:
        new_config["ModsUpdater"]["version"] = __version__
        logging.debug("Migrated version to version: %s", __version__)

    # Migration: Game_Version_max → user_game_version
    if "Game_Version_max" in old_config:
        user_game_version = old_config["Game_Version_max"].get("version")
        user_game_version = None if str(
            user_game_version) == "100.0.0" else user_game_version
        new_config["Game_Version"]["user_game_version"] = user_game_version or 'latest_version'
        logging.debug("Migrated Game_Version_max to user_game_version: %s",
                      user_game_version)

    # Migration: ModPath → ModsPath
    if "ModPath" in old_config:
        mods_path = old_config["ModPath"].get("path", "").strip()
        if mods_path:
            new_config["ModsPath"]["path"] = mods_path
            logging.debug("Migrated ModPath to ModsPath: %s", mods_path)

    # Migration: Mod_Exclusion (dictionary to list format)
    if "Mod_Exclusion" in old_config:
        mods_list = [
            value.strip()
            for key, value in old_config["Mod_Exclusion"].items()
            if value.strip()
        ]
        if mods_list:
            new_config["Mod_Exclusion"]["mods"] = ", ".join(mods_list)
            logging.debug("Migrated Mod_Exclusion with %d mods", len(mods_list))

    # Migration: log_level
    if "Logging" in old_config and "log_level" in old_config["Logging"]:
        log_level = old_config["Logging"].get("log_level")
        new_config["Logging"]["log_level"] = log_level
        logging.debug("Migrated log_level: %s", log_level)
    else:
        new_config["Logging"]["log_level"] = DEFAULT_CONFIG['Logging']['log_level']
        logging.debug(f"Set log_level to default: {DEFAULT_CONFIG['Logging']['log_level']}")

    # Step 4: Remove obsolete sections
    for section in list(new_config.keys()):
        if section != "DEFAULT" and section not in DEFAULT_CONFIG:
            del new_config[section]
            logging.debug("Removed obsolete section: %s", section)

    # Step 5: Write the updated configuration while preserving section order
    try:
        with open(CONFIG_FILE, "w", encoding='utf-8') as configfile:
            for section in DEFAULT_CONFIG.keys():
                if section in new_config:
                    configfile.write(f"[{section}]\n")
                    for key, value in new_config[section].items():
                        # Convert all values to strings before writing
                        configfile.write(f"{key} = {str(value)}\n")
                    configfile.write("\n")
        logging.info("Configuration migration completed successfully.")
        # print(lang.get_translation("config_configuration_migrated").format(EXPECTED_VERSION=EXPECTED_VERSION))
        # print("Configuration migration completed successfully.")
    except Exception as e:
        logging.error("Error occurred while writing the migrated config: %s", str(e))


def create_config(language, mod_folder, user_game_version, auto_update, behavior_choice):
    """
    Create the config.ini file with default or user-specified values.
    """
    if SYSTEM != "Windows":
        USER_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        USER_DATA_DIR.mkdir(parents=True, exist_ok=True)
        USER_CACHE_DIR.mkdir(parents=True, exist_ok=True)

    DEFAULT_CONFIG["Language"]["language"] = language[0]
    DEFAULT_CONFIG["ModsPath"]["path"] = mod_folder
    DEFAULT_CONFIG["Game_Version"]["user_game_version"] = user_game_version
    DEFAULT_CONFIG["Options"]["auto_update"] = auto_update
    DEFAULT_CONFIG["Options"]["incompatibility_behavior"] = behavior_choice

    config_parser = configparser.ConfigParser()
    for section, options in DEFAULT_CONFIG.items():
        config_parser.add_section(section)
        for key, value in options.items():
            config_parser.set(section, key, str(value))
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as configfile:
            config_parser.write(configfile)
            logging.info(f"Config.ini file created at {CONFIG_FILE}")
    except (FileNotFoundError, IOError, PermissionError) as e:
        logging.error(f"Failed to create config file at {CONFIG_FILE}: {e}")


def load_config():
    """
    Load the configuration from config.ini or create a default one if it doesn't exist.
    """
    if SYSTEM != "Windows":
        USER_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        USER_DATA_DIR.mkdir(parents=True, exist_ok=True)
        USER_CACHE_DIR.mkdir(parents=True, exist_ok=True)
        LOGS_PATH.mkdir(parents=True, exist_ok=True)

    try:
        config_parser = configparser.ConfigParser()
        config_parser.read(CONFIG_FILE, encoding='utf-8')

        # ### Populate global_cache ###
        global_cache.config_cache['APPLICATION_PATH'] = APPLICATION_PATH
        global_cache.config_cache["SYSTEM"] = platform.system()
        # Fill the global cache with config.ini data
        for section in config_parser.sections():
            global_cache.config_cache[section] = {key: value for key, value in
                                                  config_parser.items(section)}

        # Fill with constants
        global_cache.config_cache['SYSTEM'] = platform.system()
        global_cache.config_cache['HOME_PATH'] = Path.home()
        global_cache.config_cache['XDG_CONFIG_HOME_PATH'] = os.getenv(
            'XDG_CONFIG_HOME',
            str(global_cache.config_cache['HOME_PATH'] / '.config'))
        global_cache.config_cache['URL_BASE_MOD_API'] = URL_BASE_MOD_API
        global_cache.config_cache['URL_BASE_MOD_DOWNLOAD'] = URL_BASE_MOD_DOWNLOAD
        global_cache.config_cache['URL_BASE_MODS'] = URL_BASE_MODS
        global_cache.config_cache['URL_MOD_DB'] = URL_MOD_DB
        # Paths
        global_cache.config_cache['CONFIG_FILE'] = CONFIG_FILE
        global_cache.config_cache['TEMP_PATH'] = TEMP_PATH
        global_cache.config_cache['LOGS_PATH'] = LOGS_PATH
        global_cache.config_cache['BACKUP_FOLDER'] = BACKUP_FOLDER
        global_cache.config_cache['MODLIST_FOLDER'] = MODLIST_FOLDER
        global_cache.config_cache['LANG_PATH'] = LANG_PATH
        global_cache.config_cache["MODS_PATHS"] = {
            "Windows": Path(
                HOME_PATH) / 'AppData' / 'Roaming' / 'VintagestoryData' / 'Mods',
            "Linux": Path(XDG_CONFIG_HOME_PATH) / 'VintagestoryData' / 'Mods'
        }
        # Fill cache with user-agent
        global_cache.config_cache['USER_AGENTS'] = USER_AGENTS

        # Retrieve excluded mods from the config file
        excluded_mods = config_parser.get("Mod_Exclusion", "mods",
                                          fallback="").split(", ")

        # Ensure we don't have empty strings in the list
        excluded_mods = [mod.strip() for mod in excluded_mods if mod.strip()]
        for mod in excluded_mods:
            global_cache.mods_data["excluded_mods"].append({"Filename": mod})

        # Handle the game version
        user_game_version = global_cache.config_cache.get("Game_Version", {}).get(
            "user_game_version")

        # Explicitly handle old configurations with "None" or empty values
        if user_game_version in ["None", ""]:
            user_game_version = "latest_version"
            global_cache.config_cache.setdefault("Game_Version", {})[
                "user_game_version"] = "latest_version"
            logging.info(
                "Detected old game version setting. Updated to 'latest_version'.")

        if user_game_version == 'latest_version':
            latest_game_version = utils.get_latest_game_version()
            if latest_game_version:
                global_cache.config_cache.setdefault("Game_Version", {})[
                    "user_game_version"] = latest_game_version
                logging.info(
                    f"Game version set to the latest available version: {latest_game_version}")
            else:
                logging.warning(
                    "Unable to retrieve the latest game version. The version is left empty.")

    except Exception as e:
        logging.error(f"Error occurred while loading the config.ini file: {e}")
        raise
    return global_cache.config_cache


def config_exists():
    """ Check if the config.ini file exists. """
    return CONFIG_FILE.exists()


def ask_mods_directory():
    """Ask the user to choose a folder for the mods."""
    default_path = str(MODS_PATHS[SYSTEM])  # Convert Path to string for Prompt
    while True:
        mods_directory = utils.Prompt.ask(
            lang.get_translation("config_ask_mod_directory"),
            default=default_path
        )

        mods_path = Path(mods_directory)  # Convert input to Path object

        if mods_directory == "":  # User pressed Enter for default
            logging.info(f"Using default mods directory: {default_path}")
            return default_path

        if mods_path.is_dir():
            logging.info(f"Using mods directory: {mods_directory}")
            return str(mods_directory)  # Return as string for consistency
        else:
            print(lang.get_translation("config_invalid_directory").format(
                mods_directory=mods_directory))
            logging.warning(f"Invalid directory entered: {mods_directory}")


def ask_language_choice():
    """Ask the user to select a language at the first script launch."""
    print(f"[dodger_blue1]Please select your language:[/dodger_blue1]")

    # Display a message to prompt the user for language selection
    language_options = list(SUPPORTED_LANGUAGES.keys())
    for index, region in enumerate(language_options, start=1):
        language_name = SUPPORTED_LANGUAGES[region][1]
        print(f"    [bold]{index}.[/bold] {language_name} ({region})")

    # Use utils.prompt_choice to get the user's input
    choice_index = utils.prompt_choice(
        "Enter the number of your language choice (leave blank for default English)",
        choices=[str(i) for i in range(1, len(language_options) + 1)],
        show_choices=False,  # <-- This is now correctly handled by **kwargs
        default=SUPPORTED_LANGUAGES["US"][2]  # Default to English (US)
    )

    # Convert the user's choice to the corresponding language key
    chosen_region = language_options[int(choice_index) - 1]
    language_code = SUPPORTED_LANGUAGES.get(chosen_region)[0]
    chosen_language = f'{language_code}_{chosen_region}'
    language_name = SUPPORTED_LANGUAGES[chosen_region][1]
    return chosen_language, language_name


def ask_game_version():
    """Ask the user to select the game version the first script launch."""
    while True:
        user_game_version = utils.Prompt.ask(
            lang.get_translation("config_game_version_prompt"),
            default=""
        )

        # If the user left the input empty, it will use the last game version
        if user_game_version == "":
            user_game_version = "latest_version"
            return user_game_version

        # If valid, complete and return the version
        if utils.is_valid_version(user_game_version):
            return utils.complete_version(user_game_version)
        else:
            # If the format is invalid, display an error message and ask for the version again.
            print(
                f"[bold indian_red1]{lang.get_translation('config_invalid_game_version')}[/bold indian_red1]")


def ask_auto_update():
    """Ask the user to choose between manual or auto update (using words or numbers)."""

    # Normalize the translated words for comparison
    auto_key = lang.get_translation("config_choose_update_mode_auto").lower()
    manual_key = lang.get_translation("config_choose_update_mode_manual").lower()

    # Define the set of ALL acceptable inputs (numbers + normalized words)
    # 1 is for manual, 2 is for auto (using 1/2 is clearer than 1/2 depending on the order)
    # Let's assume 1 for Manual, 2 for Auto. We must stick to one mapping.

    # Define the choices presented to Rich, which must be unique and normalized
    # The first element listed is often shown as the default choice by Rich if the 'default'
    # value is missing, but here 'default' is explicitly set.
    choices_list = ['1', manual_key, '2', auto_key]  # All valid inputs

    # The default key (used for comparison AND as the default value for Rich)
    default_key = auto_key

    # Construct the message to display options clearly (e.g., "Choose mode: [1: Manual, 2: Auto]")
    # We must ensure the message is updated in the language files to be generic:
    # "config_choose_update_mode": "Choose update mode (1: Manual / 2: Auto):"

    prompt_msg = lang.get_translation("config_choose_update_mode")

    while True:
        # We use utils.prompt_choice (which handles case-insensitivity and strips spaces)
        auto_update_input = utils.prompt_choice(
            prompt_msg,
            choices=choices_list,
            default=default_key  # Rich will try to display this if possible
        )

        # Check against the normalized word key OR the number key
        if auto_update_input == auto_key or auto_update_input == '2':
            logging.info("Auto update selected.")
            return True
        elif auto_update_input == manual_key or auto_update_input == '1':
            logging.info("Manual update selected.")
            return False
        else:
            # This path is theoretically unreachable if Rich's validation works,
            # but it's good practice to keep it for debugging.
            print(lang.get_translation("config_invalid_update_choice"))


def ask_incompatibility_behavior():
    """Ask the user how to handle incompatible mods."""
    print(f"\n{lang.get_translation('config_incompatibility_prompt')}")
    print(f"  [bold]0.[/bold] {lang.get_translation('config_incompatibility_ask')}")
    print(f"  [bold]1.[/bold] {lang.get_translation('config_incompatibility_abort')}")
    print(f"  [bold]2.[/bold] {lang.get_translation('config_incompatibility_ignore')}")

    choice = utils.prompt_choice(
        lang.get_translation("config_choose_behavior_prompt"),
        choices=['0', '1', '2'],
        default='0'
    )
    return choice


def configure_logging(logging_level):
    # Vérifier si un FileHandler est déjà présent
    if not any(isinstance(handler, logging.FileHandler) for handler in
               logging.getLogger().handlers):
        # Enlever les handlers existants si nécessaire.
        if logging.getLogger().hasHandlers():
            logging.getLogger().handlers.clear()

        # S'assurer que les répertoires existent avant de configurer le logging.
        utils.setup_directories(LOGS_PATH)

        log_file = Path(LOGS_PATH) / f'app_log.txt'

        # Créer un handler pour le fichier.
        file_handler = logging.FileHandler(log_file, mode='w', encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)

        # Créer un format de log.
        formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        file_handler.setFormatter(formatter)

        # Ajouter le handler au logger.
        logging.getLogger().addHandler(file_handler)

        log_level = logging_level.upper()

        valid_log_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if log_level not in valid_log_levels:
            logging.warning(
                f"Invalid log level '{log_level}' in configuration. Defaulting to 'DEBUG'.")
            log_level = "DEBUG"

        # Appliquer le niveau de log
        logging.getLogger().setLevel(getattr(logging, log_level, logging.DEBUG))

        logging.debug(
            f"Logging configured successfully with '{log_level}' level and custom file handler!")

    else:
        # If FileHandler is already present, do nothing.
        pass


def configure_mod_updated_logging():
    # Create a distinct logger for the mod_updated_log.txt file
    mod_updated_logger = logging.getLogger('mod_updated_logger')

    # Check if a FileHandler is already present to avoid duplication
    if not any(isinstance(handler, logging.FileHandler) for handler in
               mod_updated_logger.handlers):
        log_file = Path(LOGS_PATH) / 'updated_mods_changelog.txt'

        file_handler = logging.FileHandler(log_file, mode='w', encoding='utf-8')
        file_handler.setLevel(logging.INFO)  # INFO Level

        # Simple format without timestamp or level
        formatter = logging.Formatter("%(message)s")
        file_handler.setFormatter(formatter)

        mod_updated_logger.addHandler(file_handler)

        # Disable propagation to the root logger
        mod_updated_logger.propagate = False

    return mod_updated_logger


if __name__ == "__main__":
    pass

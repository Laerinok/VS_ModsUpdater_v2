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
__version__ = "2.0.1"  # Don't forget to change EXPECTED_VERSION
__date__ = "2025-04-03"  # Last update


# config.py

import configparser
import logging
import os
import platform
from pathlib import Path

from rich import print
from rich.prompt import Prompt

import global_cache
import utils
import lang

# The target version after migration
EXPECTED_VERSION = "2.0.1"

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

# Constants for paths
APPLICATION_PATH = Path.cwd()
CONFIG_FILE = APPLICATION_PATH / 'config.ini'
TEMP_PATH = APPLICATION_PATH / 'temp'
LOGS_PATH = APPLICATION_PATH / 'logs'
LANG_PATH = APPLICATION_PATH / 'lang'

# Constants for supported languages
SUPPORTED_LANGUAGES = {
    "DE": ["de", "Deutsch", '1'],
    "US": ["en", "English", '2'],
    "ES": ["es", "Español", '3'],
    "FR": ["fr", "Français", '4'],
    "IT": ["it", "Italiano", '5'],
    "JP": ["ja", "日本語", '6'],
    "BR": ["pt", "Português (Brasil)", '7'],
    "PT": ["pt", "Português (Portugal)", '8'],
    "RU": ["ru", "Русский", '9'],
    "UA": ["uk", "Yкраїнська", '10'],
    "CN": ["zh", "简体中文", '11']
}
DEFAULT_LANGUAGE = "en_US"

# Constants for url
URL_BASE_MOD_API = "https://mods.vintagestory.at/api/mod/"
URL_BASE_MOD_DOWNLOAD = "https://moddbcdn.vintagestory.at/"
URL_BASE_MODS = 'https://mods.vintagestory.at/'
URL_MOD_DB = "https://mods.vintagestory.at/show/mod/"
URL_SCRIPT = {
    "windows": 'https://mods.vintagestory.at/modsupdater#tab-files',
    "linux": 'https://mods.vintagestory.at/modsupdaterforlinux#tab-files'
}

# Default configuration
DEFAULT_CONFIG = {
    "ModsUpdater": {"version": __version__},
    "Logging": {"log_level": "DEBUG"},
    "Options": {"exclude_prerelease_mods": "false", "auto_update": "true", "max_workers": str(4), "timeout": str(10)},
    "Backup_Mods": {"backup_folder": "backup_mods", "max_backups": str(3), "modlist_folder": "modlist"},
    "ModsPath": {"path": MODS_PATHS[SYSTEM]},
    "Language": {"language": DEFAULT_LANGUAGE},
    "Game_Version": {"user_game_version": str("")},
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


def read_version_from_config_file():
    config = configparser.ConfigParser()
    config.read(CONFIG_FILE)  # Read the configuration file
    return config.get('ModsUpdater', 'version', fallback=None)


def migrate_config_if_needed():
    current_version = read_version_from_config_file()  # Function to read the version from config.ini
    if current_version != EXPECTED_VERSION:
        # If the configuration version is outdated, initiate the migration
        old_config = configparser.ConfigParser()
        old_config.read(CONFIG_FILE)  # Read the current configuration file
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
        new_config["Game_Version"]["user_game_version"] = user_game_version or 'None'
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
        new_config["Logging"]["log_level"] = DEFAULT_CONFIG['Logging']["log_level"]
        logging.debug(f"Set log_level to default: {DEFAULT_CONFIG['Logging']["log_level"]}")

    # Step 4: Remove obsolete sections
    for section in list(new_config.keys()):
        if section != "DEFAULT" and section not in DEFAULT_CONFIG:
            del new_config[section]
            logging.debug("Removed obsolete section: %s", section)

    # Step 5: Write the updated configuration while preserving section order
    try:
        with open(CONFIG_FILE, "w") as configfile:
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


def create_config(language, mod_folder, user_game_version, auto_update):
    """
    Create the config.ini file with default or user-specified values.
    """
    DEFAULT_CONFIG["Language"]["language"] = language[0]
    DEFAULT_CONFIG["ModsPath"]["path"] = mod_folder
    DEFAULT_CONFIG["Game_Version"]["user_game_version"] = user_game_version
    DEFAULT_CONFIG["Options"]["auto_update"] = auto_update

    config = configparser.ConfigParser()
    for section, options in DEFAULT_CONFIG.items():
        config.add_section(section)
        for key, value in options.items():
            config.set(section, key, str(value))
    try:
        with open(CONFIG_FILE, 'w') as configfile:
            config.write(configfile)
            logging.info(f"Config.ini file created")
    except (FileNotFoundError, IOError, PermissionError) as e:
        logging.error(f"Failed to create config file: {e}")


def load_config():
    # Check if the configuration file exists
    if not CONFIG_FILE.exists():
        raise FileNotFoundError(f"The configuration file {CONFIG_FILE} was not found.")

    try:
        config = configparser.ConfigParser()
        config.read(CONFIG_FILE)

        # ### Populate global_cache ###
        global_cache.config_cache['APPLICATION_PATH'] = APPLICATION_PATH
        global_cache.config_cache["SYSTEM"] = platform.system()
        # Fill the global cache with config.ini data
        for section in config.sections():
            global_cache.config_cache[section] = {key: value for key, value in
                                                  config.items(section)}
        # Fill with constants
        global_cache.config_cache['SYSTEM'] = platform.system()
        global_cache.config_cache['HOME_PATH'] = Path.home()
        global_cache.config_cache['XDG_CONFIG_HOME_PATH'] = os.getenv('XDG_CONFIG_HOME', str(global_cache.config_cache['HOME_PATH'] / '.config'))
        global_cache.config_cache['URL_BASE_MOD_API'] = URL_BASE_MOD_API
        global_cache.config_cache['URL_BASE_MOD_DOWNLOAD'] = URL_BASE_MOD_DOWNLOAD
        global_cache.config_cache['URL_BASE_MODS'] = URL_BASE_MODS
        global_cache.config_cache['URL_MOD_DB'] = URL_MOD_DB
        # Paths
        global_cache.config_cache["MODS_PATHS"] = {
            "Windows": Path(
                HOME_PATH) / 'AppData' / 'Roaming' / 'VintagestoryData' / 'Mods',
            "Linux": Path(XDG_CONFIG_HOME_PATH) / 'VintagestoryData' / 'Mods'
        }
        # Fill cache with user-agent
        global_cache.config_cache['USER_AGENTS'] = USER_AGENTS

        # Retrieve excluded mods from the config file
        excluded_mods = config.get("Mod_Exclusion", "mods", fallback="").split(", ")

        # Ensure we don't have empty strings in the list
        excluded_mods = [mod.strip() for mod in excluded_mods if mod.strip()]
        for mod in excluded_mods:
            global_cache.mods_data["excluded_mods"].append({"Filename": mod})

        # Handle the game version
        user_game_version = global_cache.config_cache.get("Game_Version", {}).get("user_game_version")
        if user_game_version == "None":
            user_game_version = None
        if not user_game_version:
            latest_game_version = utils.get_latest_game_version()
            if latest_game_version:
                global_cache.config_cache.setdefault("Game_Version", {})["user_game_version"] = latest_game_version
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
    """
    Check if the config.ini file exists.
    """
    return CONFIG_FILE.exists()


def ask_mods_directory():
    """Ask the user to choose a folder for the mods."""
    default_path = str(MODS_PATHS[SYSTEM])  # Convert Path to string for Prompt
    while True:
        mods_directory = Prompt.ask(
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
            print(lang.get_translation("config_invalid_directory").format(mods_directory=mods_directory))
            logging.warning(f"Invalid directory entered: {mods_directory}")


def ask_language_choice():
    """Ask the user to select a language at the first script launch."""
    print(f"[bold cyan]Please select your language:[/bold cyan]")

    # Display a message to prompt the user for language selection
    language_options = list(SUPPORTED_LANGUAGES.keys())
    for index, region in enumerate(language_options, start=1):
        language_name = SUPPORTED_LANGUAGES[region][1]
        print(f"    [bold]{index}.[/bold] {language_name} ({region})")

    # Use Prompt.ask to get the user's input
    choice_index = Prompt.ask(
        "Enter the number of your language choice (leave blank for default English)",
        choices=[str(i) for i in range(1, len(language_options) + 1)],
        show_choices=False,
        default=2
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
        user_game_version = Prompt.ask(
            lang.get_translation("config_game_version_prompt"),
            default=""
            )

        # If the user left the input empty, it will use the last game version
        if user_game_version == "":
            user_game_version = None
            return user_game_version

        # If valid, complete and return the version
        if utils.is_valid_version(user_game_version):
            return utils.complete_version(user_game_version)
        else:
            # If the format is invalid, display an error message and ask for the version again.
            print(f"[bold red]{lang.get_translation("config_invalid_game_version")}[/bold red]")


def ask_auto_update():
    """Ask the user to choose between manual or auto update."""
    while True:
        auto_update_input = Prompt.ask(
            lang.get_translation("config_choose_update_mode"),
            choices=[lang.get_translation("config_choose_update_mode_manual"), lang.get_translation("config_choose_update_mode_auto")],
            default=lang.get_translation("config_choose_update_mode_auto")
        ).lower()

        if auto_update_input == "auto":
            logging.info("Auto update selected.")
            return True
        elif auto_update_input == "manual":
            logging.info("Manual update selected.")
            return False
        else:
            print(lang.get_translation("config_invalid_update_choice"))


def configure_logging(logging_level):
    # Vérifier si un FileHandler est déjà présent
    if not any(isinstance(handler, logging.FileHandler) for handler in logging.getLogger().handlers):
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
            logging.warning(f"Invalid log level '{log_level}' in configuration. Defaulting to 'DEBUG'.")
            log_level = "DEBUG"

        # Appliquer le niveau de log
        logging.getLogger().setLevel(getattr(logging, log_level, logging.DEBUG))

        logging.debug(f"Logging configured successfully with '{log_level}' level and custom file handler!")

    else:
        # If FileHandler is already present, do nothing.
        pass


def configure_mod_updated_logging():
    # Créer un logger distinct pour le fichier mod_updated_log.txt
    mod_updated_logger = logging.getLogger('mod_updated_logger')

    # Vérifier si un FileHandler est déjà présent pour éviter la duplication
    if not any(isinstance(handler, logging.FileHandler) for handler in mod_updated_logger.handlers):
        log_file = Path(LOGS_PATH) / 'updated_mods_changelog.txt'

        file_handler = logging.FileHandler(log_file, mode='w', encoding='utf-8')
        file_handler.setLevel(logging.INFO)  # Niveau INFO

        # Format simple sans timestamp ni niveau
        formatter = logging.Formatter("%(message)s")
        file_handler.setFormatter(formatter)

        mod_updated_logger.addHandler(file_handler)

        # Désactiver la propagation vers le logger global
        mod_updated_logger.propagate = False

    return mod_updated_logger


if __name__ == "__main__":
    pass

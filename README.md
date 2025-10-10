# - ModsUpdater for Vintage Story (Windows/Linux) -

This program automates the management of your mods for the game Vintage Story. It allows you to check for updates, download them (automatically or manually), and generate a list of your installed mods in JSON, PDF, and HTML format.

[ModsUpdater on ModDB](https://mods.vintagestory.at/modsupdater) / [ModsUpdater for Linux on ModDB](https://mods.vintagestory.at/modsupdaterforlinux)

## Key Features

- Script Update Check: Checks if a new version of the ModsUpdater tool is available.
- Configuration Migration: Automatically manages the migration of the old configuration file format to the new one, ensuring compatibility during application updates.
- Update Check: Compares the local versions of your mods with the latest versions available on ModDB.
- **Mod Downgrade**: If an installed mod is too new for the selected game version, the updater will offer to downgrade it to the latest compatible version.
- **Incompatibility Check**: The application warns if an installed mod is incompatible with the selected game version, even when no alternative version is available.
- Automatic Download: Automatically downloads available updates (configurable).
- Manual Download: Displays changelogs and allows you to choose which updates to download.
- Backup Management: Creates backups of your mods before updating them, with a configurable retention policy.
- Excluded Mods Management: Allows you to ignore certain mods during update checks and downloads.
- **Detailed Exclusion Reasons**: Displays the specific reason for a mod's exclusion in the final summary (e.g., 'Excluded by user in config.ini' or 'API data unavailable').
- Mod List Generation (PDF/JSON/HTML): Creates a PDF, JSON, or HTML document listing your installed mods.
- Command Line Interface (CLI): Integration with arguments to customize execution.
- Multilingual Support: The interface is available in several languages (configurable).

**Important Note Regarding Configuration Migration:**

During updates of the ModsUpdater application, the format of the `config.ini` file may evolve. To facilitate these updates, the application includes an automatic migration mechanism. If an older version of the configuration file is detected, the application will attempt to convert it to the new format. In most cases, this migration will occur transparently. However, it is always recommended to check your `config.ini` file after an application update to ensure that all your settings are correctly preserved. In case of any issues, a backup of your old configuration (`config.old`) is kept (beside the `config.ini`file).

## Configuration (`config.ini`)

The `config.ini` file contains the configuration parameters for the application. It is located in the same directory as the main script. Here are the main sections and their options:

```ini
[ModsUpdater]
version = 2.4.0
```
* `version`: Current version of the ModsUpdater application (information).

```ini
[Logging]
log_level = INFO
```
* `log_level`: Level of detail for logs recorded by the application (e.g., DEBUG, INFO, WARNING, ERROR). DEBUG will display the most details.

```ini
[Options]
exclude_prerelease_mods = false
auto_update = true
max_workers = 4
timeout = 10
```
* `exclude_prerelease_mods`: true to exclude pre-release mod versions during update checks, false to include them.
* `auto_update`: true to enable automatic downloading of updates (after checking), false to use manual mode where you confirm each download.
* `max_workers`: Maximum number of threads to use for downloading mods in parallel. Increasing this value may speed up downloads but may also consume more system resources. **The maximum value allowed for this setting is 10.**
* `timeout`: Timeout in seconds for HTTP requests during update checks and mod downloads. **A typical useful range is between 5 and 30 seconds. Setting it too low might cause connection errors on slower networks, while setting it too high might make the application wait unnecessarily long if a server is unresponsive.**

```ini
[Backup_Mods]
backup_folder = backup_mods
max_backups = 3
modlist_folder = Modlist
```
* `backup_folder`: Name of the directory (created in the application directory by default) where mod backups will be stored. **You can also specify a full path if you wish to store backups elsewhere.**
* `max_backups`: Maximum number of mod backups to keep. Older backups will be deleted when this limit is reached.
* `modlist_folder`: Name of the directory (created in the application directory by default) where the mod lists in PDF and JSON format will be saved. **You can also specify a full path if you wish to save the lists elsewhere.**

```ini
[ModsPath]
path = D:\Game\VintagestoryData\Mods
```
* `path`: Full path to the directory where your Vintage Story mods are installed on your computer. This is crucial for the application to find your mods. (Example for Windows: D:\Game\VintagestoryData\Mods)

```ini
[Language]
language = en_US
```
* `language`: Language code to use for the application interface (e.g., en_US for English, fr_FR for French). This value must correspond to the name of a file (without the `.json` extension) present in the `lang` subdirectory of the application. Make sure the corresponding language file exists.

```ini
[Game_Version]
user_game_version = 1.20.5
```    
* `user_game_version`:    Maximum game version target for mod updates.
  * If you specify a version (for example, 1.20.5), the application will not download mod updates that are only compatible with Vintage Story versions higher than the one specified.
  * If this option is left empty (``), set to `None`, or set to `latest_version`, the application will download the latest available update for each mod, regardless of the compatible Vintage Story version. Caution: this means you might download mods that are not compatible with your current game version. If you want to stay on a specific Vintage Story version, define the version, but remember to change it when you update the game.

```ini
[Incompatibility]
incompatibility_behavior = 0
```
* `incompatibility_behavior`: Defines how the application handles incompatible mods.
  * `0` (ask): Prompts the user for action before continuing. (Default)
  * `1` (abort): Stops the process automatically if an incompatibility is detected.
  * `2` (ignore): Continues the process, ignoring the incompatibility.

```ini
[Mod_Exclusion]
mods = mod_a.zip, my_old_mod.cs
```
* `mods`: List of filenames (without the path) of mods to ignore during update checks and downloads. Filenames should be separated by **commas and spaces** (e.g., mod_a.zip, my_old_mod.cs).


## Command Line Arguments Usage

The script can be executed with arguments to customize its behavior:

- `--no-pause`: Disables the pause at the end of the script execution. Useful for non-interactive execution or in automated scripts.
- `--modspath "<path>"`: Allows you to specify the path to the Vintage Story mods directory directly during execution. The path must be enclosed in quotation marks if it contains spaces. This argument replaces the path defined in the `config.ini` file.
- `--no-json`: Disables the automatic generation of the mod list in JSON format at the end of execution.
- `--no-pdf`: Disables the automatic generation of the mod list in PDF format at the end of execution.
- `--no-html`: Disables the automatic generation of the mod list in HTML format at the end of execution.
- `--log-level <level>`: Sets the level of detail for logs recorded by the application. Possible options are: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL` (in uppercase). This argument replaces the log level defined in the `[Logging]` section of `config.ini`.
- `--max-workers <number>`: Allows you to specify the maximum number of threads to use for mod processing. This argument replaces the `max_workers` value defined in the `[Options]` section of `config.ini`.
- `--timeout <seconds>`: Sets the timeout in seconds for HTTP requests during update checks and mod downloads. This argument replaces the `timeout` value defined in the `[Options]` section of `config.ini`.
- `--install-modlist`: Download mods from modlist.json to the mods folder.
- `--force-update`: Force a re-download and re-install of all mods, regardless of version.
- `--dry-run`: Performs a trial run that checks for updates and incompatibilities without downloading or modifying any files.

**Usage Examples:**

```bash
VS_ModsUpdater.exe --modspath "D:\Vintage Story\mods" --no-pdf
```
This command will execute the script using the specified mods directory (`D:\Vintage Story\mods`) and will disable the generation of the PDF mod list file. The mods path specified here will replace the one configured in `config.ini`.



```bash
VS_ModsUpdater.exe --log-level INFO --max-workers 6 --timeout 15
```
This command will execute the script by setting the log level to `INFO`, using a maximum of 6 threads for mod processing, and a timeout of 15 seconds for HTTP requests. These parameters will replace those defined in the `config.ini` file for this execution.


## License

This program is distributed under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License.


    
=============================  
Supported Languages:

    Deutsch
    English
    Español
    Français
    Italiano
    日本語
    한국어 (From gitHub. Thanks purple8cloud)
    Polski (From gitHub. Thanks MaLiN2223)
    Português (Brasil)
    Português (Portugal)
    Русский
    Yкраїнська
    简体中文

=============================    
(Latest update: 2024-10-10 / v2.4.0)
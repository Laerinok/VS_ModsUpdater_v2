# Changelog

All notable changes to this project will be documented in this file.

## [2.6.0] - 2026-02-06

### Added
- **Config**: Added `latest_stable_version` as a valid value for `user_game_version`. This is now the default setting.
- **Config**: Added automatic migration logic to update existing configurations with empty or "None" game versions to `latest_stable_version`.

### Changed
- **Config**: The default value for `user_game_version` is now `latest_stable_version` instead of `latest_version`. This ensures that by default, the updater will ignore unstable game versions (pre-releases, release candidates) to protect users from incompatible mod updates.
- **Core**: Updated `utils.get_latest_game_version` to support filtering for stable versions only.
- **Build**: Pinned dependencies versions in `requirements.txt` to ensure build stability and reproducibility.

### Fixed
- **Core**: Implemented robust path resolution for assets and translations on macOS.

## [2.5.0] - 2026-01-31

### Added
- **CLI**: Added `--config-path` argument. This allows users to specify a custom location for the configuration file, enabling management of multiple game instances with isolated settings.

### Changed
- **API Logic**: Improved `utils.get_latest_game_version` to validate version numbers received from the API. It now iterates backwards to find the latest *valid* semantic version, ignoring malformed entries.
- **UI**: Changed "Installed game version" to "Target Game Version" in the main display to clarify that this is a configuration setting, not a local file detection.

### Fixed
- **Backup System**: Resolved a critical crash (`ValueError: ZIP does not support timestamps before 1980`) occurring when archiving mods with invalid or pre-1980 modification dates (typically on Linux filesystems).
- **Core**: Fixed an issue where invalid game version strings returned by the API (e.g., `.4.4-dev.2`) caused the application to crash on startup, particularly on Linux systems.
- **Stability**: Added safeguards in `fetch_mod_info.py` to handle `InvalidVersion` exceptions gracefully during mod compatibility checks.
- **Refactoring**: Renamed variables in the main execution block to resolve shadowing warnings.
- **Update Logic**: Fixed version sorting to prioritize mod releases matching the current game version over newer backports (e.g., prevents v0.5.19 for 1.21.4 from overriding v0.5.18 for 1.21.6).

## [2.4.1] - 2025-10-16

### Fixed
- **macOS**: Added the default mods path (`~/Library/Application Support/VintagestoryData/Mods`) to ensure the application can locate the game's mod directory.
- **macOS**: Corrected the update script URL for the macOS (Darwin) release, which was preventing the application from checking for new versions.

## [2.4.0] - 2025-10-14

### Added
- **Build**: Implemented GitHub Actions workflow to automatically build releases for Windows (.exe), Linux (AppImage), and macOS (.dmg).
- **Build**: Automatic selection of platform-specific icons (`.ico`, `.png`, `.icns`).
- **Core**: Support for Directory-Based Mods (e.g., managed by Mod Organizer 2), provided they contain a `modinfo.json`.
- **Core**: Mod downgrade capability. If an installed mod is too new for the selected game version, the updater offers to downgrade it.
- **Core**: Proactive incompatibility check. Warns if an installed mod is incompatible with the game version, even if no update is available.
- **Config**: Added `incompatibility_behavior` option (Ask, Abort, or Ignore).
- **CLI**: Added `--dry-run` argument to simulate updates without modifying files.
- **UX**: Display of specific reasons for mod exclusion (e.g., 'Excluded by user' or 'API data unavailable').
- **UX**: Initial configuration summary now includes the incompatibility behavior choice.
- **UX**: Dry-run report now includes the game version used for simulation.
- **i18n**: Added Polish (pl_PL) language support.

### Fixed
- **Core**: Critical fix for `ValueError` crash when processing local-only mods not found on ModDB.
- **Core**: Critical fix for `AttributeError: 'NoneType'` when downloads failed after all retries.
- **Core**: Fixed double URL encoding issues causing download failures for certain mods.
- **Core**: Overhauled update detection logic to use ModDB API data for compatibility checks, fixing issues with missing local `modinfo.json`.
- **Core**: Fixed detection of mods installed as directories.
- **CLI**: Restored broken `--dry-run` functionality.
- **Config**: Fixed `UnicodeDecodeError` during config migration on systems with special characters in paths.
- **Config**: Fixed an issue where `max_backups = 0` deleted all backups instead of disabling the limit.
- **Linux**: Corrected backup directory path to use `~/.local/share/VS_ModsUpdater/backup_mods/`.
- **Reports**: Fixed broken links for local-only mods in reports.
- **Reports**: Fixed mod icons not displaying in HTML/PDF reports.
- **UX**: Fixed "Yes/No" prompts to accept universal ASCII input (e.g., 'n') alongside localized characters (e.g., Cyrillic).
- **UX**: Restored display of exclusion reasons in the final summary.
- **UX**: Markdown rendering for changelogs in the console.

### Changed
- **UX**: "Yes/No" prompts now explicitly display all valid inputs (e.g., `(o/n, y/n)`).
- **Performance**: Reworked update check logic to pre-filter excluded mods, preventing unnecessary network calls.
- **Performance**: Removed unused dependencies (beautifulsoup4, Pygments, striprtf), reducing app size by ~15MB.
- **Refactoring**: Centralized user input logic into `utils.prompt_yes_no`.
- **Refactoring**: Dynamic language list generation in configuration.

## [2.3.0] - 2025-08-26

### Added
- **UX**: Prompt to display the changelog for new script updates on demand.
- **Core**: Support for a new API to check for ModsUpdater updates.
- **UX**: Improved console output with clickable links and centered text.

### Fixed
- **Core**: Fixed exclusion list logic; excluded mods are now properly skipped during scans.
- **Core**: Local mods are now correctly identified in the exclusion list.
- **UI**: Resolved misaligned text in the console display.

### Changed
- **UI**: Rephrased game version display for clarity.
- **Code**: Cleanup of unused imports and code.

## [2.2.2] - 2025-08-25

### Changed
- **Config**: The program now automatically uses the latest game version if no specific version is indicated in `config.ini`.
- **UI**: `config.ini` now shows 'latest_version' instead of an empty value for clarity.

## [2.2.1] - 2025-08-??

### Fixed
- **Core**: Fixed crash when using `--force-update` on mods without available updates.
- **CLI**: Fixed `--no-pdf` and `--no-json` flags not suppressing progress messages.
- **CLI**: Fixed argument parsing logic for export functions.

### Changed
- **UX**: `install-modlist` command now shows the name of the mod being downloaded.

## [2.2.0] - 2025-08-??

### Added
- **CLI**: Added `--force-update` to force re-download/re-install of all mods.
- **CLI**: Added `--install-mods` to download mods listed in `modlist.json`.
- **Logs**: Update date and time are now displayed in `updated_mods_changelog.txt`.

### Fixed
- **Core**: Exported JSON now lists the *installed* version's URL, not the latest available.
- **Core**: Mod changelogs are now fetched directly from the API.
- **API**: Adapted to API changes (removal of 'v' prefix in version strings).
- **Config**: Explicit UTF-8 encoding for reading/writing `config.ini`.
- **UI**: Fixed warning message for empty mods directory.

## [2.1.3] - 2025-05-05

### Fixed
- **Core**: Fixed broken download link for ModsUpdater self-update.

### Changed
- **Build**: Migrated from Nuitka to cx_Freeze for better compatibility.

## [2.1.2] - 2025-04-26

### Fixed
- **CLI**: `modspath` argument is now correctly used.
- **UI**: Warning for directories in Mods folder now specifies the directory name.
- **i18n**: Updated Korean (ko_KR) translation.

## [2.1.1] - 2025-04-09

### Fixed
- **Core**: Ensure mod icons are extracted even when PDF export is disabled (needed for HTML).

## [2.1.0] - 2025-04-08

### Added
- **Export**: Added HTML mod list export (`export_html.py`).
- **CLI**: Added `--no-html` argument.
- **UI**: Display of the maximum game version for mod updates.
- **i18n**: Added Korean (ko_KR) localization.

### Fixed
- **Core**: Fixed "No new version available" message not displaying.
- **Core**: Correct mod icon is now displayed in PDF even if update was skipped.
- **Core**: Fixed download links in `modlist.json` for manual mode.
- **Core**: `updated_mods_changelog.txt` population fix for manual mode.

### Improved
- **UI**: Progress bars for information retrieval, download, and PDF creation.
import sys
import os
from cx_Freeze import setup, Executable

# --- Icon Logic ---
# Define potential icon files by platform
icon_files = {
    "win32": "vintagestory.ico",
    "darwin": "vintagestory.icns",
    "linux": "vintagestory.png"
}

# Determine the icon for the current platform, if it exists
icon_path = None
platform_icon = icon_files.get(sys.platform)
if platform_icon and os.path.exists(platform_icon):
    icon_path = platform_icon

# --- Include Files Logic ---
# Start with the base files and directories
include_files = [
    "README.md", "changelog.txt", "LICENSE.md", "requirements.txt",
    "assets", "fonts", "lang"
]

# Add only the icon files that actually exist in the project
for icon_file in set(icon_files.values()):  # Use set to avoid duplicates
    if os.path.exists(icon_file):
        include_files.append(icon_file)

# Options for cx_Freeze
build_exe_options = {
    "include_files": include_files,
    "excludes": []
}

# Executable definition
exe = Executable(
    script="main.py",
    icon=icon_path,  # This will be None if the icon doesn't exist, which is fine
    target_name="VS_ModsUpdater",
    copyright="Laerinok",
)

setup(
    name="VS_ModsUpdater",
    version="2.4.0",
    description="ModsUpdater for Vintage Story",
    author="Laerinok",
    license="GNU GPLv3",
    options={"build_exe": build_exe_options},
    executables=[exe]
)

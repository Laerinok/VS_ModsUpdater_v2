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

# Determine the icon for the current platform executable, if it exists
icon_path = None
platform_icon_for_exe = icon_files.get(sys.platform)
if platform_icon_for_exe and os.path.exists(platform_icon_for_exe):
    icon_path = platform_icon_for_exe

# --- Include Files Logic ---
# Start with the base files and directories that are always needed
include_files = [
    "README.md", "changelog.txt", "LICENSE.md", "requirements.txt",
    "assets", "fonts", "lang"
]

# Add ONLY the icon for the CURRENT build platform to the list of included files
platform_icon_to_include = icon_files.get(sys.platform)
if platform_icon_to_include and os.path.exists(platform_icon_to_include):
    include_files.append(platform_icon_to_include)

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

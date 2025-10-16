import sys
import os
from cx_Freeze import setup, Executable

# Define the assets directory
assets_dir = "assets"

# --- Icon Logic ---
# Define potential icon files by platform, now looking inside the assets folder
icon_files = {
    "win32": os.path.join(assets_dir, "vintagestory.ico"),
    "darwin": os.path.join(assets_dir, "vintagestory.icns"),
    "linux": os.path.join(assets_dir, "vintagestory.png")
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
    assets_dir, "fonts", "lang"
]

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
    version="2.4.1",
    description="ModsUpdater for Vintage Story",
    author="Laerinok",
    license="GNU GPLv3",
    options={"build_exe": build_exe_options},
    executables=[exe]
)

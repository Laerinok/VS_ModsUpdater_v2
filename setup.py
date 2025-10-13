import sys
from cx_Freeze import setup, Executable

# Determine the icon based on the OS
icon_path = "vintagestory.ico"
if sys.platform == "darwin":  # macOS
    icon_path = "vintagestory.icns"
elif sys.platform.startswith("linux"):  # Linux
    icon_path = "vintagestory.png"

# Files to include
include_files = [
    "README.md", "changelog.txt", "LICENSE.md", "requirements.txt",
    "assets", "fonts", "lang",
    "vintagestory.ico", "vintagestory.png", "vintagestory.icns"
]

# Options to include necessary packages and files
build_exe_options = {
    "include_files": include_files,
    "excludes": []
}

# Executable definition
exe = Executable(
    script="main.py",
    icon=icon_path,
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

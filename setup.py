from cx_Freeze import setup, Executable

# Options pour inclure les packages et fichiers nécessaires
build_exe_options = {
    "include_files": ["README.md", "changelog.txt", "LICENSE.md", "requirements.txt", "assets", "fonts", "lang"],
    "excludes": []
}

# Définition de l'exécutable
exe = Executable(
    script="main.py",
    icon="vintagestory.ico",
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

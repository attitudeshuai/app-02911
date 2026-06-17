# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec for Rust Cargo DOS Commander.

Build (run from backend/build/):
    pyinstaller cargo_commander.spec --noconfirm --distpath ../dist

We use --onedir (COLLECT) because tkinter is more reliable in onedir mode
than onefile (no temp-extract resource races, faster startup). The resulting
cargo-commander/ directory is then zipped/tarred for distribution.

The spec is committed on purpose (it is source). PyInstaller cannot
cross-compile, so each target OS builds its own artifact via the release
workflow matrix.
"""
import os

from PyInstaller.utils.hooks import collect_all

datas = []
binaries = []
hiddenimports = []

# tkinter + Pillow are not always auto-detected; collect everything for them.
for pkg in ("tkinter", "PIL"):
    d, b, h = collect_all(pkg)
    datas += d
    binaries += b
    hiddenimports += h

# Explicitly collect our own package so submodules are bundled.
hiddenimports += [
    "app",
    "app.gui.main_window",
    "app.gui.tab_terminal",
    "app.gui.toolbar",
    "app.gui.statusbar",
    "app.gui.file_browser",
    "app.gui.dialogs",
    "app.gui.toml_editor",
    "app.gui.syntax_highlight",
    "app.gui.autocomplete",
    "app.gui.terminal_widget",
    "app.commands.command_router",
    "app.commands.dos_commands",
    "app.commands.cargo_executor",
    "app.commands.base",
    "app.config",
    "app.logger",
]

a = Analysis(
    ["../main.py"],
    pathex=[os.path.abspath("..")],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="cargo-commander",
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    name="cargo-commander",
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
)

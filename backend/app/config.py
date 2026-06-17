"""
Application configuration constants.
Centralized config to avoid hardcoded values scattered across modules.
"""

import os
import platform


class Theme:
    """DOS-style terminal color theme."""

    BG = "#0C0C0C"
    FG = "#00FF00"
    FG_DIM = "#008800"
    ERROR = "#FF5555"
    WARNING = "#FFFF55"
    INFO = "#55FFFF"
    SUCCESS = "#55FF55"
    PROMPT = "#00FF00"
    TOOLBAR_BG = "#1E1E1E"
    TOOLBAR_BTN = "#2D2D2D"
    TOOLBAR_BTN_HOVER = "#3D3D3D"
    TOOLBAR_BTN_TEXT = "#CCCCCC"
    STATUSBAR_BG = "#007ACC"
    STATUSBAR_FG = "#FFFFFF"
    BORDER = "#333333"
    SELECTION_BG = "#264F78"
    SCROLLBAR = "#444444"


class Font:
    """Font configuration."""

    FAMILY_CANDIDATES = ("Consolas", "Courier New", "Menlo", "DejaVu Sans Mono", "monospace")
    SIZE = 14
    SIZE_SMALL = 12
    SIZE_TOOLBAR = 12


class Window:
    """Window dimensions."""

    MIN_WIDTH = 1024
    MIN_HEIGHT = 700
    DEFAULT_WIDTH = 1200
    DEFAULT_HEIGHT = 800
    TITLE = "Rust Cargo DOS Commander v1.0"


class App:
    """Application settings."""

    MAX_HISTORY = 500
    MAX_SCROLLBACK = 10000
    DEFAULT_WORKSPACE = os.path.expanduser("~/rust_projects")
    COMMAND_TIMEOUT = 120  # seconds
    IS_WINDOWS = platform.system() == "Windows"
    SHELL = "cmd.exe" if IS_WINDOWS else "/bin/bash"

    # DOS prompt style
    PROMPT_TEMPLATE = "{path}>"

    # Supported cargo subcommands
    CARGO_COMMANDS = (
        "new",
        "build",
        "run",
        "test",
        "check",
        "clean",
        "doc",
        "bench",
        "update",
        "fmt",
        "clippy",
    )

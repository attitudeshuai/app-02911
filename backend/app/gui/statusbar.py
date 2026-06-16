"""
Status bar component showing current directory, Rust version, and process status.
"""
import tkinter as tk
from tkinter import font as tkfont

from app.config import Theme, Font
from app.commands.cargo_executor import CargoExecutor


class StatusBar(tk.Frame):
    """Bottom status bar with contextual information."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg=Theme.STATUSBAR_BG, padx=8, pady=3, **kwargs)

        self._font = tkfont.Font(family="Consolas", size=Font.SIZE_SMALL)

        # Left: current directory
        self._cwd_label = tk.Label(
            self, text="", bg=Theme.STATUSBAR_BG, fg=Theme.STATUSBAR_FG,
            font=self._font, anchor=tk.W,
        )
        self._cwd_label.pack(side=tk.LEFT)

        # Right: Rust version
        self._rust_label = tk.Label(
            self, text="", bg=Theme.STATUSBAR_BG, fg=Theme.STATUSBAR_FG,
            font=self._font, anchor=tk.E,
        )
        self._rust_label.pack(side=tk.RIGHT)

        # Center: status
        self._status_label = tk.Label(
            self, text="Ready", bg=Theme.STATUSBAR_BG, fg=Theme.STATUSBAR_FG,
            font=self._font,
        )
        self._status_label.pack(side=tk.RIGHT, padx=20)

        self._load_rust_info()

    def _load_rust_info(self):
        """Load Rust/Cargo version info."""
        cargo_ver = CargoExecutor.get_cargo_version()
        rustc_ver = CargoExecutor.get_rustc_version()

        if "not installed" in cargo_ver:
            self._rust_label.config(text="⚠ Rust not installed", fg="#FFCC00")
        else:
            self._rust_label.config(text=f"🦀 {cargo_ver} | {rustc_ver}")

    def update_cwd(self, cwd: str):
        """Update displayed current directory."""
        display = cwd
        if len(display) > 60:
            display = "..." + display[-57:]
        self._cwd_label.config(text=f"📁 {display}")

    def set_status(self, text: str, is_error: bool = False):
        """Update status text."""
        color = "#FF6666" if is_error else Theme.STATUSBAR_FG
        self._status_label.config(text=text, fg=color)

    def set_busy(self, busy: bool):
        """Update status for busy state."""
        if busy:
            self.set_status("⏳ Running...")
        else:
            self.set_status("✅ Ready")

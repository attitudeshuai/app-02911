"""
Toolbar component with quick-action buttons for common Cargo operations.
"""

import tkinter as tk
from collections.abc import Callable
from tkinter import font as tkfont

from app.config import Font, Theme
from app.logger import logger


class ToolbarButton(tk.Label):
    """A styled toolbar button with hover effects."""

    def __init__(
        self, parent, text: str, icon: str, command: Callable, tooltip: str = "", **kwargs
    ):
        self._command = command
        self._tooltip = tooltip

        super().__init__(
            parent,
            text=f" {icon} {text} ",
            bg=Theme.TOOLBAR_BTN,
            fg=Theme.TOOLBAR_BTN_TEXT,
            font=tkfont.Font(family="Consolas", size=Font.SIZE_TOOLBAR),
            padx=10,
            pady=4,
            cursor="hand2",
            relief=tk.FLAT,
            borderwidth=1,
        )

        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<Button-1>", self._on_click)

        # Tooltip
        self._tip_window = None

    def _on_enter(self, event):
        self.config(bg=Theme.TOOLBAR_BTN_HOVER, fg="#FFFFFF")
        if self._tooltip:
            self._show_tooltip(event)

    def _on_leave(self, event):
        self.config(bg=Theme.TOOLBAR_BTN, fg=Theme.TOOLBAR_BTN_TEXT)
        self._hide_tooltip()

    def _on_click(self, event):
        self.config(bg="#4D4D4D")
        self.after(100, lambda: self.config(bg=Theme.TOOLBAR_BTN_HOVER))
        logger.info("Toolbar button clicked: %s", self.cget("text").strip())
        self._command()

    def _show_tooltip(self, event):
        if self._tip_window:
            return
        x = self.winfo_rootx() + 10
        y = self.winfo_rooty() + self.winfo_height() + 5
        self._tip_window = tw = tk.Toplevel(self)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        label = tk.Label(
            tw,
            text=self._tooltip,
            bg="#333333",
            fg="#FFFFFF",
            font=("Consolas", 10),
            padx=8,
            pady=4,
            relief=tk.SOLID,
            borderwidth=1,
        )
        label.pack()

    def _hide_tooltip(self):
        if self._tip_window:
            self._tip_window.destroy()
            self._tip_window = None

    def set_enabled(self, enabled: bool):
        """Enable or disable the button."""
        if enabled:
            self.config(fg=Theme.TOOLBAR_BTN_TEXT, cursor="hand2")
            self.bind("<Button-1>", self._on_click)
        else:
            self.config(fg="#555555", cursor="arrow")
            self.unbind("<Button-1>")


class Toolbar(tk.Frame):
    """Application toolbar with cargo quick-action buttons."""

    def __init__(self, parent, on_action: Callable[[str], None], **kwargs):
        super().__init__(parent, bg=Theme.TOOLBAR_BG, padx=8, pady=6, **kwargs)
        self._on_action = on_action
        self._buttons: dict[str, ToolbarButton] = {}
        self._setup_buttons()

    def _setup_buttons(self):
        """Create toolbar buttons."""
        buttons_config = [
            ("New Project", "📦", "cargo new", "Create a new Rust project (cargo new)"),
            ("Build", "🔨", "cargo build", "Build the project (cargo build)"),
            ("Run", "▶", "cargo run", "Run the project (cargo run)"),
            ("Test", "🧪", "cargo test", "Run tests (cargo test)"),
            ("Check", "✓", "cargo check", "Check for errors (cargo check)"),
            ("Clean", "🗑", "cargo clean", "Clean build artifacts (cargo clean)"),
            ("Cancel", "⛔", "__CANCEL__", "Cancel running process (Ctrl+C)"),
        ]

        # Logo / title
        title = tk.Label(
            self,
            text=" 🦀 Cargo Commander ",
            bg=Theme.TOOLBAR_BG,
            fg="#E06C00",
            font=tkfont.Font(family="Consolas", size=Font.SIZE_TOOLBAR, weight="bold"),
        )
        title.pack(side=tk.LEFT, padx=(0, 16))

        # Separator
        sep = tk.Frame(self, bg=Theme.BORDER, width=1, height=24)
        sep.pack(side=tk.LEFT, padx=8, fill=tk.Y)

        for text, icon, cmd, tooltip in buttons_config:
            btn = ToolbarButton(self, text, icon, lambda c=cmd: self._on_action(c), tooltip)
            btn.pack(side=tk.LEFT, padx=3)
            self._buttons[cmd] = btn

    def set_busy(self, busy: bool):
        """Update button states based on busy status."""
        for cmd, btn in self._buttons.items():
            if cmd == "__CANCEL__":
                btn.set_enabled(busy)
            else:
                btn.set_enabled(not busy)

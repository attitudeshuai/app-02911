"""
Command autocomplete popup.
Provides Tab-completion for commands, cargo subcommands, and file paths.
"""

import os
import tkinter as tk
from tkinter import font as tkfont

from app.config import App, Font, Theme

# All known commands for autocomplete
BUILTIN_COMMANDS = [
    "cargo",
    "cd",
    "cls",
    "clear",
    "del",
    "dir",
    "echo",
    "exit",
    "help",
    "ls",
    "md",
    "mkdir",
    "pwd",
    "quit",
    "rd",
    "rm",
    "rmdir",
    "tree",
    "type",
    "ver",
]

CARGO_SUBCOMMANDS = list(App.CARGO_COMMANDS)

CARGO_OPTIONS = {
    "build": ["--release", "--verbose", "--target", "--jobs", "--features", "--all-features"],
    "run": ["--release", "--verbose", "--example", "--bin"],
    "test": ["--release", "--verbose", "--lib", "--doc", "--no-run"],
    "new": ["--bin", "--lib", "--name", "--vcs"],
    "check": ["--release", "--verbose", "--all-targets"],
    "clean": ["--release", "--verbose", "--target"],
    "doc": ["--open", "--no-deps", "--verbose"],
    "fmt": ["--check", "--verbose"],
    "clippy": ["--fix", "--verbose", "--all-targets"],
}


class AutocompletePopup(tk.Toplevel):
    """A floating popup window showing autocomplete suggestions."""

    MAX_VISIBLE = 8

    def __init__(self, parent_text: tk.Text, on_select):
        super().__init__(parent_text)
        self._parent_text = parent_text
        self._on_select = on_select
        self._items: list[str] = []
        self._selected_index: int = 0

        self.wm_overrideredirect(True)
        self.wm_attributes("-topmost", True)
        self.configure(bg=Theme.BORDER)

        self._font = tkfont.Font(family="Consolas", size=Font.SIZE_SMALL)

        # Listbox for suggestions
        self._listbox = tk.Listbox(
            self,
            bg="#1E1E1E",
            fg="#CCCCCC",
            selectbackground="#094771",
            selectforeground="#FFFFFF",
            font=self._font,
            borderwidth=1,
            relief=tk.SOLID,
            highlightthickness=0,
            activestyle="none",
            exportselection=False,
        )
        self._listbox.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)

        self._listbox.bind("<Button-1>", self._on_click)
        self._listbox.bind("<Double-Button-1>", self._on_double_click)

        self.withdraw()

    def show(self, items: list[str], x: int, y: int):
        """Show the popup with given items at screen position."""
        if not items:
            self.hide()
            return

        self._items = items
        self._selected_index = 0

        self._listbox.delete(0, tk.END)
        for item in items:
            self._listbox.insert(tk.END, f"  {item}")

        visible = min(len(items), self.MAX_VISIBLE)
        self._listbox.config(height=visible)

        # Calculate width based on longest item
        max_len = max(len(s) for s in items) + 4
        width = max_len * 9  # approximate char width

        self.geometry(f"{width}x{visible * 22}+{x}+{y}")
        self._listbox.selection_set(0)
        self.deiconify()
        self.lift()

    def hide(self):
        """Hide the popup."""
        self.withdraw()

    @property
    def is_visible(self) -> bool:
        return self.winfo_viewable()

    def select_next(self):
        """Move selection down."""
        if not self._items:
            return
        self._selected_index = min(self._selected_index + 1, len(self._items) - 1)
        self._update_selection()

    def select_prev(self):
        """Move selection up."""
        if not self._items:
            return
        self._selected_index = max(self._selected_index - 1, 0)
        self._update_selection()

    def get_selected(self) -> str | None:
        """Get the currently selected item."""
        if 0 <= self._selected_index < len(self._items):
            return self._items[self._selected_index]
        return None

    def _update_selection(self):
        self._listbox.selection_clear(0, tk.END)
        self._listbox.selection_set(self._selected_index)
        self._listbox.see(self._selected_index)

    def _on_click(self, event):
        idx = self._listbox.nearest(event.y)
        if 0 <= idx < len(self._items):
            self._selected_index = idx
            self._update_selection()

    def _on_double_click(self, event):
        self._on_click(event)
        selected = self.get_selected()
        if selected:
            self._on_select(selected)


class AutocompleteEngine:
    """Generates autocomplete suggestions based on current input context."""

    @staticmethod
    def get_suggestions(text: str, cwd: str) -> list[str]:
        """Get autocomplete suggestions for the given input text."""
        text = text.lstrip()
        if not text:
            return BUILTIN_COMMANDS[:12]

        parts = text.split()
        # Completing first word (command name)
        if len(parts) == 1 and not text.endswith(" "):
            prefix = parts[0].lower()
            matches = [c for c in BUILTIN_COMMANDS if c.startswith(prefix)]
            return matches

        # Completing cargo subcommand
        if parts[0].lower() == "cargo":
            if len(parts) == 2 and not text.endswith(" "):
                prefix = parts[1].lower()
                return [s for s in CARGO_SUBCOMMANDS if s.startswith(prefix)]
            elif len(parts) == 2 and text.endswith(" "):
                sub = parts[1].lower()
                return CARGO_OPTIONS.get(sub, []) + AutocompleteEngine._path_suggestions(cwd, "")
            elif len(parts) >= 3:
                sub = parts[1].lower()
                last = parts[-1]
                if last.startswith("-"):
                    opts = CARGO_OPTIONS.get(sub, [])
                    return [o for o in opts if o.startswith(last)]
                return AutocompleteEngine._path_suggestions(cwd, last)

        # File path completion for commands that take paths
        if parts[0].lower() in (
            "cd",
            "dir",
            "ls",
            "type",
            "cat",
            "mkdir",
            "rmdir",
            "del",
            "rm",
            "tree",
        ):
            partial = parts[-1] if len(parts) > 1 and not text.endswith(" ") else ""
            return AutocompleteEngine._path_suggestions(cwd, partial)

        return []

    @staticmethod
    def _path_suggestions(cwd: str, partial: str) -> list[str]:
        """Get file/directory path suggestions."""
        if os.path.isabs(partial):
            base_dir = os.path.dirname(partial)
            prefix = os.path.basename(partial)
        elif os.sep in partial or "/" in partial:
            base_dir = os.path.join(cwd, os.path.dirname(partial))
            prefix = os.path.basename(partial)
        else:
            base_dir = cwd
            prefix = partial

        if not os.path.isdir(base_dir):
            return []

        try:
            entries = os.listdir(base_dir)
        except PermissionError:
            return []

        matches = []
        prefix_lower = prefix.lower()
        for entry in sorted(entries):
            if entry.startswith("."):
                continue
            if entry.lower().startswith(prefix_lower):
                full = os.path.join(base_dir, entry)
                display = entry + ("/" if os.path.isdir(full) else "")
                matches.append(display)

        return matches[:15]

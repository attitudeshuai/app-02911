"""
Multi-tab terminal manager.
Allows multiple terminal sessions with independent command history,
working directories, and output buffers.
"""
import tkinter as tk
from tkinter import font as tkfont
from typing import Callable, Optional

from app.config import Theme, Font, App
from app.commands.base import OutputType
from app.gui.terminal_widget import TerminalWidget
from app.logger import logger


class TabButton(tk.Frame):
    """A single tab button in the tab bar."""

    def __init__(self, parent, tab_id: int, title: str, on_select, on_close, **kwargs):
        super().__init__(parent, bg=Theme.TOOLBAR_BG, **kwargs)
        self._tab_id = tab_id
        self._on_select = on_select
        self._on_close = on_close
        self._active = False

        self._font = tkfont.Font(family="Consolas", size=Font.SIZE_SMALL)

        self._label = tk.Label(
            self, text=f" {title} ", bg=Theme.TOOLBAR_BG, fg="#888888",
            font=self._font, cursor="hand2", padx=4, pady=2,
        )
        self._label.pack(side=tk.LEFT)

        self._close_btn = tk.Label(
            self, text="×", bg=Theme.TOOLBAR_BG, fg="#666666",
            font=self._font, cursor="hand2", padx=2,
        )
        self._close_btn.pack(side=tk.LEFT)

        # Separator
        tk.Frame(self, bg=Theme.BORDER, width=1).pack(side=tk.LEFT, fill=tk.Y, padx=1)

        # Bindings
        self._label.bind("<Button-1>", lambda e: self._on_select(self._tab_id))
        self._close_btn.bind("<Button-1>", lambda e: self._on_close(self._tab_id))
        self._close_btn.bind("<Enter>", lambda e: self._close_btn.config(fg="#FF6666"))
        self._close_btn.bind("<Leave>", lambda e: self._close_btn.config(
            fg="#CCCCCC" if self._active else "#666666"))

    def set_active(self, active: bool):
        """Update visual state."""
        self._active = active
        if active:
            self._label.config(bg="#1E1E1E", fg="#FFFFFF")
            self._close_btn.config(bg="#1E1E1E", fg="#CCCCCC")
            self.config(bg="#1E1E1E")
        else:
            self._label.config(bg=Theme.TOOLBAR_BG, fg="#888888")
            self._close_btn.config(bg=Theme.TOOLBAR_BG, fg="#666666")
            self.config(bg=Theme.TOOLBAR_BG)

    def set_title(self, title: str):
        self._label.config(text=f" {title} ")


class TabTerminalManager(tk.Frame):
    """Manages multiple terminal tabs, each with its own TerminalWidget."""

    MAX_TABS = 8

    def __init__(self, parent, on_command: Callable[[str], None], **kwargs):
        super().__init__(parent, bg=Theme.BG, **kwargs)
        self._on_command = on_command
        self._tabs: dict[int, dict] = {}  # tab_id -> {widget, cwd, button, title}
        self._active_tab: Optional[int] = None
        self._next_id: int = 0

        self._build_tab_bar()
        self._terminal_container = tk.Frame(self, bg=Theme.BG)
        self._terminal_container.pack(fill=tk.BOTH, expand=True)

    def _build_tab_bar(self):
        """Build the tab bar at the top."""
        self._tab_bar = tk.Frame(self, bg=Theme.TOOLBAR_BG, height=28)
        self._tab_bar.pack(fill=tk.X)
        self._tab_bar.pack_propagate(False)

        self._tabs_frame = tk.Frame(self._tab_bar, bg=Theme.TOOLBAR_BG)
        self._tabs_frame.pack(side=tk.LEFT, fill=tk.Y)

        # New tab button
        new_btn = tk.Label(
            self._tab_bar, text=" + ", bg=Theme.TOOLBAR_BG, fg="#888888",
            font=tkfont.Font(family="Consolas", size=Font.SIZE_SMALL),
            cursor="hand2", padx=4,
        )
        new_btn.pack(side=tk.LEFT, padx=2)
        new_btn.bind("<Button-1>", lambda e: self.add_tab())
        new_btn.bind("<Enter>", lambda e: new_btn.config(fg="#FFFFFF"))
        new_btn.bind("<Leave>", lambda e: new_btn.config(fg="#888888"))

        tk.Frame(self, bg=Theme.BORDER, height=1).pack(fill=tk.X)

    def add_tab(self, title: Optional[str] = None, cwd: Optional[str] = None) -> int:
        """Create a new terminal tab. Returns the tab ID."""
        if len(self._tabs) >= self.MAX_TABS:
            logger.warning("Maximum tab limit reached (%d)", self.MAX_TABS)
            return -1

        tab_id = self._next_id
        self._next_id += 1

        if title is None:
            title = f"Terminal {tab_id + 1}"
        if cwd is None:
            cwd = App.DEFAULT_WORKSPACE

        # Create terminal widget
        terminal = TerminalWidget(self._terminal_container, self._on_command)

        # Create tab button
        btn = TabButton(self._tabs_frame, tab_id, title, self._select_tab, self._close_tab)
        btn.pack(side=tk.LEFT)

        self._tabs[tab_id] = {
            "widget": terminal,
            "cwd": cwd,
            "button": btn,
            "title": title,
        }

        self._select_tab(tab_id)
        terminal.initialize(cwd)

        logger.info("New tab created: %d (%s)", tab_id, title)
        return tab_id

    def _select_tab(self, tab_id: int):
        """Switch to the specified tab."""
        if tab_id not in self._tabs:
            return

        # Hide current
        if self._active_tab is not None and self._active_tab in self._tabs:
            self._tabs[self._active_tab]["widget"].pack_forget()
            self._tabs[self._active_tab]["button"].set_active(False)

        # Show new
        self._active_tab = tab_id
        tab = self._tabs[tab_id]
        tab["widget"].pack(in_=self._terminal_container, fill=tk.BOTH, expand=True)
        tab["button"].set_active(True)
        tab["widget"].focus_set()

    def _close_tab(self, tab_id: int):
        """Close a tab. Won't close the last remaining tab."""
        if tab_id not in self._tabs:
            return
        if len(self._tabs) <= 1:
            return  # Keep at least one tab

        tab = self._tabs.pop(tab_id)
        tab["widget"].destroy()
        tab["button"].destroy()

        # Switch to another tab
        if self._active_tab == tab_id:
            remaining = list(self._tabs.keys())
            if remaining:
                self._select_tab(remaining[-1])

        logger.info("Tab closed: %d", tab_id)

    @property
    def active_terminal(self) -> Optional[TerminalWidget]:
        """Get the currently active terminal widget."""
        if self._active_tab is not None and self._active_tab in self._tabs:
            return self._tabs[self._active_tab]["widget"]
        return None

    @property
    def active_cwd(self) -> Optional[str]:
        """Get the cwd of the active tab."""
        if self._active_tab is not None and self._active_tab in self._tabs:
            return self._tabs[self._active_tab]["cwd"]
        return None

    def update_active_cwd(self, cwd: str):
        """Update the cwd of the active tab."""
        if self._active_tab is not None and self._active_tab in self._tabs:
            self._tabs[self._active_tab]["cwd"] = cwd
            terminal = self._tabs[self._active_tab]["widget"]
            terminal.update_cwd(cwd)
            # Update tab title to show directory name
            dir_name = os.path.basename(cwd) or cwd
            self._tabs[self._active_tab]["button"].set_title(dir_name)

    def set_busy(self, busy: bool):
        """Set busy state on the active terminal."""
        terminal = self.active_terminal
        if terminal:
            terminal.set_busy(busy)

    def write_line(self, text: str, output_type: OutputType = OutputType.NORMAL):
        terminal = self.active_terminal
        if terminal:
            terminal.write_line(text, output_type)

    def write_text(self, text: str, output_type: OutputType = OutputType.NORMAL):
        terminal = self.active_terminal
        if terminal:
            terminal.write_text(text, output_type)

    def show_result(self, result):
        terminal = self.active_terminal
        if terminal:
            terminal.show_result(result)

    def finish_command(self):
        terminal = self.active_terminal
        if terminal:
            terminal.finish_command()


# Need os for update_active_cwd
import os

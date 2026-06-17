"""
Terminal emulator widget.
DOS-style terminal with command input, history, and colored output.
"""

import tkinter as tk
from collections.abc import Callable
from tkinter import font as tkfont

from app.commands.base import OutputType
from app.config import App, Font, Theme
from app.gui.autocomplete import AutocompleteEngine, AutocompletePopup


class TerminalWidget(tk.Frame):
    """A DOS-style terminal emulator widget built on tkinter Text."""

    # Map OutputType to tag names
    TYPE_TAG_MAP = {
        OutputType.NORMAL: "normal",
        OutputType.ERROR: "error",
        OutputType.WARNING: "warning",
        OutputType.INFO: "info",
        OutputType.SUCCESS: "success",
        OutputType.SYSTEM: "system",
    }

    def __init__(self, parent, on_command: Callable[[str], None], **kwargs):
        super().__init__(parent, bg=Theme.BG, **kwargs)
        self._on_command = on_command
        self._history: list[str] = []
        self._history_index: int = -1
        self._current_input: str = ""
        self._prompt_end: str = "1.0"
        self._cwd: str = App.DEFAULT_WORKSPACE
        self._is_busy: bool = False

        self._autocomplete: AutocompletePopup | None = None

        self._setup_font()
        self._setup_widgets()
        self._setup_tags()
        self._setup_bindings()
        self._setup_autocomplete()

    def _setup_font(self):
        """Find and configure the best available monospace font."""
        available = tkfont.families()
        self._font_family = "TkFixedFont"
        for candidate in Font.FAMILY_CANDIDATES:
            if candidate in available:
                self._font_family = candidate
                break
        self._term_font = tkfont.Font(family=self._font_family, size=Font.SIZE)

    def _setup_widgets(self):
        """Create the text widget and scrollbar."""
        # Scrollbar
        self._scrollbar = tk.Scrollbar(
            self,
            bg=Theme.SCROLLBAR,
            troughcolor=Theme.BG,
            activebackground=Theme.TOOLBAR_BTN_HOVER,
            highlightthickness=0,
            bd=0,
        )
        self._scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Main text area
        self._text = tk.Text(
            self,
            bg=Theme.BG,
            fg=Theme.FG,
            insertbackground=Theme.FG,
            selectbackground=Theme.SELECTION_BG,
            selectforeground=Theme.FG,
            font=self._term_font,
            wrap=tk.WORD,
            padx=8,
            pady=8,
            spacing1=1,
            spacing3=1,
            undo=False,
            borderwidth=0,
            highlightthickness=0,
            cursor="xterm",
        )
        self._text.pack(fill=tk.BOTH, expand=True)

        # Link scrollbar
        self._text.config(yscrollcommand=self._scrollbar.set)
        self._scrollbar.config(command=self._text.yview)

    def _setup_tags(self):
        """Configure text tags for colored output."""
        self._text.tag_configure("normal", foreground=Theme.FG)
        self._text.tag_configure("error", foreground=Theme.ERROR)
        self._text.tag_configure("warning", foreground=Theme.WARNING)
        self._text.tag_configure("info", foreground=Theme.INFO)
        self._text.tag_configure("success", foreground=Theme.SUCCESS)
        self._text.tag_configure("system", foreground=Theme.FG_DIM)
        self._text.tag_configure("prompt", foreground=Theme.PROMPT)
        self._text.tag_configure("input", foreground=Theme.FG)

    def _setup_bindings(self):
        """Set up keyboard bindings."""
        self._text.bind("<Return>", self._on_enter)
        self._text.bind("<Tab>", self._on_tab)
        self._text.bind("<Up>", self._on_history_up)
        self._text.bind("<Down>", self._on_history_down)
        self._text.bind("<Home>", self._on_home)
        self._text.bind("<BackSpace>", self._on_backspace)
        self._text.bind("<Key>", self._on_key)
        self._text.bind("<Control-c>", self._on_ctrl_c)
        self._text.bind("<Control-l>", self._on_ctrl_l)
        self._text.bind("<Escape>", self._on_escape)
        # Prevent mouse from moving cursor before prompt
        self._text.bind("<Button-1>", self._on_click)

    def _setup_autocomplete(self):
        """Initialize the autocomplete popup."""
        self._autocomplete = AutocompletePopup(self._text, self._accept_autocomplete)

    def _on_tab(self, event) -> str:
        """Handle Tab key - trigger or navigate autocomplete."""
        if self._is_busy:
            return "break"

        if self._autocomplete and self._autocomplete.is_visible:
            # Accept current selection
            selected = self._autocomplete.get_selected()
            if selected:
                self._accept_autocomplete(selected)
            return "break"

        # Generate suggestions
        current_input = self._get_current_input()
        suggestions = AutocompleteEngine.get_suggestions(current_input, self._cwd)

        if len(suggestions) == 1:
            # Single match - auto-complete immediately
            self._accept_autocomplete(suggestions[0])
        elif suggestions:
            # Show popup
            self._show_autocomplete_popup(suggestions)

        return "break"

    def _show_autocomplete_popup(self, suggestions: list[str]):
        """Show the autocomplete popup near the cursor."""
        if not self._autocomplete:
            return
        try:
            bbox = self._text.bbox(tk.INSERT)
            if bbox:
                x = self._text.winfo_rootx() + bbox[0]
                y = self._text.winfo_rooty() + bbox[1] + bbox[3] + 4
                self._autocomplete.show(suggestions, x, y)
        except tk.TclError:
            pass

    def _accept_autocomplete(self, selected: str):
        """Accept an autocomplete suggestion."""
        if self._autocomplete:
            self._autocomplete.hide()

        current_input = self._get_current_input()
        parts = current_input.split()

        if not parts or not current_input.endswith(" ") and len(parts) >= 1:
            # Replace the last partial word
            if parts:
                parts[-1] = selected
            else:
                parts = [selected]
        else:
            parts.append(selected)

        new_input = " ".join(parts)
        if selected.endswith("/"):
            pass  # Don't add trailing space for directories
        else:
            new_input += " "

        self._replace_input(new_input)

    def _on_escape(self, event) -> str:
        """Handle Escape - hide autocomplete."""
        if self._autocomplete and self._autocomplete.is_visible:
            self._autocomplete.hide()
            return "break"
        return "break"

    def _on_enter(self, event) -> str:
        """Handle Enter key - submit command."""
        if self._is_busy:
            return "break"

        # Hide autocomplete if visible
        if self._autocomplete and self._autocomplete.is_visible:
            self._autocomplete.hide()

        # Get the current input
        user_input = self._get_current_input()
        self._text.insert(tk.END, "\n")

        if user_input.strip():
            self._history.append(user_input.strip())
            if len(self._history) > App.MAX_HISTORY:
                self._history.pop(0)

        self._history_index = -1
        self._current_input = ""

        # Callback
        if user_input.strip():
            self._on_command(user_input.strip())
        else:
            self._show_prompt()

        return "break"

    def _on_history_up(self, event) -> str:
        """Navigate command history up."""
        if self._is_busy or not self._history:
            return "break"

        if self._history_index == -1:
            self._current_input = self._get_current_input()
            self._history_index = len(self._history) - 1
        elif self._history_index > 0:
            self._history_index -= 1

        self._replace_input(self._history[self._history_index])
        return "break"

    def _on_history_down(self, event) -> str:
        """Navigate command history down."""
        if self._is_busy:
            return "break"

        if self._history_index == -1:
            return "break"

        if self._history_index < len(self._history) - 1:
            self._history_index += 1
            self._replace_input(self._history[self._history_index])
        else:
            self._history_index = -1
            self._replace_input(self._current_input)

        return "break"

    def _on_home(self, event) -> str:
        """Move cursor to start of input (after prompt)."""
        self._text.mark_set(tk.INSERT, self._prompt_end)
        return "break"

    def _on_backspace(self, event) -> str:
        """Prevent backspace past prompt."""
        if self._is_busy:
            return "break"
        cursor = self._text.index(tk.INSERT)
        if self._text.compare(cursor, "<=", self._prompt_end):
            return "break"
        return None  # Allow default behavior

    def _on_key(self, event) -> str | None:
        """Handle general key presses - prevent editing before prompt."""
        if self._is_busy and event.char:
            return "break"

        # Allow control keys
        if event.state & 0x4 or not event.char:  # Ctrl or non-char
            return None

        cursor = self._text.index(tk.INSERT)
        if self._text.compare(cursor, "<", self._prompt_end):
            self._text.mark_set(tk.INSERT, tk.END)

        return None

    def _on_ctrl_c(self, event) -> str:
        """Handle Ctrl+C - cancel running process or clear input."""
        if self._is_busy:
            self._on_command("__CANCEL__")
        else:
            self._text.insert(tk.END, "^C\n")
            self._show_prompt()
        return "break"

    def _on_ctrl_l(self, event) -> str:
        """Handle Ctrl+L - clear screen."""
        self.clear()
        self._show_prompt()
        return "break"

    def _on_click(self, event) -> str | None:
        """Ensure cursor stays in editable area after click."""
        self._text.after(10, self._ensure_cursor_position)
        return None

    def _ensure_cursor_position(self):
        """Move cursor to end if it's before the prompt."""
        cursor = self._text.index(tk.INSERT)
        if self._text.compare(cursor, "<", self._prompt_end):
            self._text.mark_set(tk.INSERT, tk.END)

    def _get_current_input(self) -> str:
        """Get the text after the prompt on the current line."""
        try:
            return self._text.get(self._prompt_end, f"{tk.END}-1c")
        except tk.TclError:
            return ""

    def _replace_input(self, new_text: str):
        """Replace current input with new text."""
        self._text.delete(self._prompt_end, tk.END)
        self._text.insert(self._prompt_end, new_text, "input")
        self._text.mark_set(tk.INSERT, tk.END)

    def _show_prompt(self):
        """Display the command prompt."""
        prompt = App.PROMPT_TEMPLATE.format(path=self._cwd)
        self._text.insert(tk.END, prompt, "prompt")
        self._prompt_end = self._text.index(tk.INSERT)
        self._text.mark_set(tk.INSERT, tk.END)
        self._text.see(tk.END)

    # --- Public API ---

    def initialize(self, cwd: str):
        """Initialize terminal with welcome message."""
        self._cwd = cwd
        self.write_line("", OutputType.NORMAL)
        self.write_line(
            "  ╔══════════════════════════════════════════════════════╗", OutputType.SYSTEM
        )
        self.write_line(
            "  ║       Rust Cargo DOS Commander [Version 1.0]        ║", OutputType.SYSTEM
        )
        self.write_line(
            "  ║                                                      ║", OutputType.SYSTEM
        )
        self.write_line(
            "  ║  A DOS-style terminal for Rust/Cargo development.   ║", OutputType.SYSTEM
        )
        self.write_line(
            "  ║  Type 'help' for available commands.                ║", OutputType.SYSTEM
        )
        self.write_line(
            "  ╚══════════════════════════════════════════════════════╝", OutputType.SYSTEM
        )
        self.write_line("", OutputType.NORMAL)
        self._show_prompt()
        self._text.focus_set()

    def write_line(self, text: str, output_type: OutputType = OutputType.NORMAL):
        """Write a line of text with the specified type."""
        tag = self.TYPE_TAG_MAP.get(output_type, "normal")
        self._text.insert(tk.END, text + "\n", tag)
        self._text.see(tk.END)
        self._trim_scrollback()

    def write_text(self, text: str, output_type: OutputType = OutputType.NORMAL):
        """Write text without newline."""
        tag = self.TYPE_TAG_MAP.get(output_type, "normal")
        self._text.insert(tk.END, text, tag)
        self._text.see(tk.END)

    def show_result(self, result):
        """Display a CommandResult."""
        if result.clear_screen:
            self.clear()

        if result.lines:
            for text, otype in result.lines:
                self.write_line(text, otype)
        elif result.output and result.output != "__EXIT__":
            self.write_line(
                result.output, OutputType.ERROR if not result.success else OutputType.NORMAL
            )

        if result.new_cwd:
            self._cwd = result.new_cwd

    def finish_command(self):
        """Called when a command finishes - show prompt again."""
        self._is_busy = False
        self._show_prompt()

    def set_busy(self, busy: bool):
        """Set terminal busy state."""
        self._is_busy = busy

    def clear(self):
        """Clear the terminal."""
        self._text.delete("1.0", tk.END)

    def update_cwd(self, cwd: str):
        """Update the current working directory."""
        self._cwd = cwd

    @property
    def cwd(self) -> str:
        return self._cwd

    def _trim_scrollback(self):
        """Trim scrollback buffer if too large."""
        line_count = int(self._text.index("end-1c").split(".")[0])
        if line_count > App.MAX_SCROLLBACK:
            excess = line_count - App.MAX_SCROLLBACK
            self._text.delete("1.0", f"{excess}.0")

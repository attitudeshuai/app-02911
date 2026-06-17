"""
Main application window.
Orchestrates all GUI components and command execution.
Integrates: file browser, multi-tab terminal, autocomplete, syntax highlighting,
and Cargo.toml visual editor.
"""

import os
import tkinter as tk
from tkinter import messagebox

from app.commands.base import OutputType
from app.commands.command_router import CommandRouter
from app.config import App, Theme, Window
from app.gui.dialogs import NewProjectDialog
from app.gui.file_browser import FileBrowser
from app.gui.statusbar import StatusBar
from app.gui.syntax_highlight import SyntaxHighlighter
from app.gui.tab_terminal import TabTerminalManager
from app.gui.toml_editor import TomlEditorDialog
from app.gui.toolbar import Toolbar
from app.logger import logger


class MainWindow:
    """Main application window controller."""

    def __init__(self):
        self._root = tk.Tk()
        self._root.title(Window.TITLE)
        self._root.geometry(f"{Window.DEFAULT_WIDTH}x{Window.DEFAULT_HEIGHT}")
        self._root.minsize(Window.MIN_WIDTH, Window.MIN_HEIGHT)
        self._root.configure(bg=Theme.BG)

        try:
            self._root.iconname("Cargo Commander")
        except Exception:
            pass

        # State
        self._cwd = App.DEFAULT_WORKSPACE
        os.makedirs(self._cwd, exist_ok=True)
        self._router = CommandRouter()
        self._is_busy = False
        self._file_browser_visible = True

        # Build UI
        self._build_layout()

        # Initialize first terminal tab
        self._tab_manager.add_tab("Terminal 1", self._cwd)
        self._statusbar.update_cwd(self._cwd)

        # Window close handler
        self._root.protocol("WM_DELETE_WINDOW", self._on_close)

        # Keyboard shortcuts
        self._root.bind("<Control-t>", lambda e: self._tab_manager.add_tab(cwd=self._cwd))
        self._root.bind("<Control-b>", lambda e: self._toggle_file_browser())
        self._root.bind("<Control-e>", lambda e: self._open_toml_editor())

        logger.info("Application started. Workspace: %s", self._cwd)

    def _build_layout(self):
        """Build the main window layout with file browser sidebar."""
        # Toolbar at top
        self._toolbar = Toolbar(self._root, self._on_toolbar_action)
        self._toolbar.pack(fill=tk.X)

        tk.Frame(self._root, bg=Theme.BORDER, height=1).pack(fill=tk.X)

        # Main content area (horizontal split: file browser | terminal)
        self._main_pane = tk.PanedWindow(
            self._root,
            orient=tk.HORIZONTAL,
            bg=Theme.BORDER,
            sashwidth=3,
            sashrelief=tk.FLAT,
            borderwidth=0,
        )
        self._main_pane.pack(fill=tk.BOTH, expand=True)

        # File browser panel (left)
        self._browser_frame = tk.Frame(self._main_pane, bg=Theme.TOOLBAR_BG, width=250)
        self._file_browser = FileBrowser(
            self._browser_frame, self._cwd, self._on_file_browser_action
        )
        self._file_browser.pack(fill=tk.BOTH, expand=True)
        self._main_pane.add(self._browser_frame, minsize=180, width=250)

        # Terminal area (right) - multi-tab
        self._terminal_frame = tk.Frame(self._main_pane, bg=Theme.BG)
        self._tab_manager = TabTerminalManager(self._terminal_frame, self._on_command)
        self._tab_manager.pack(fill=tk.BOTH, expand=True)
        self._main_pane.add(self._terminal_frame, minsize=400)

        # Separator
        tk.Frame(self._root, bg=Theme.BORDER, height=1).pack(fill=tk.X)

        # Status bar at bottom
        self._statusbar = StatusBar(self._root)
        self._statusbar.pack(fill=tk.X)

    def _on_command(self, raw_input: str):
        """Handle command input from terminal."""
        if raw_input == "__CANCEL__":
            self._cancel_process()
            return

        command_lower = raw_input.strip().split()[0].lower() if raw_input.strip() else ""

        # Intercept 'toml' command to open editor
        if command_lower == "toml":
            self._open_toml_editor()
            self._tab_manager.finish_command()
            return

        if command_lower == "cargo" and len(raw_input.strip().split()) > 1:
            self._execute_async(raw_input)
        else:
            self._execute_sync(raw_input)

    def _execute_sync(self, raw_input: str):
        """Execute a command synchronously."""
        result = self._router.execute(raw_input, self._cwd)

        # Handle exit
        if result.output == "__EXIT__":
            self._tab_manager.show_result(result)
            self._root.after(500, self._on_close)
            return

        # Handle directory change
        if result.new_cwd:
            self._cwd = result.new_cwd
            self._tab_manager.update_active_cwd(self._cwd)
            self._statusbar.update_cwd(self._cwd)
            self._file_browser.set_root(self._cwd)

        # Check if output is a Rust file for syntax highlighting
        parts = raw_input.strip().split()
        if len(parts) >= 2 and parts[0].lower() in ("type", "cat"):
            filepath = parts[1]
            if filepath.endswith(".rs"):
                self._show_highlighted_file(filepath, result)
                self._tab_manager.finish_command()
                return

        self._tab_manager.show_result(result)
        self._tab_manager.finish_command()

    def _execute_async(self, raw_input: str):
        """Execute a command asynchronously with streaming output."""
        self._set_busy(True)

        def on_output(text: str, output_type: OutputType):
            self._root.after(0, lambda: self._tab_manager.write_text(text, output_type))

        def on_complete(exit_code: int):
            self._root.after(0, lambda: self._on_async_complete(exit_code))

        started = self._router.execute_async(raw_input, self._cwd, on_output, on_complete)

        if not started:
            self._set_busy(False)
            self._execute_sync(raw_input)

    def _on_async_complete(self, exit_code: int):
        """Handle async command completion."""
        self._set_busy(False)
        self._tab_manager.finish_command()
        # Refresh file browser after cargo commands (new files may exist)
        self._file_browser.refresh()

        if exit_code == 0:
            self._statusbar.set_status("✅ Command completed successfully")
        elif exit_code == -1:
            self._statusbar.set_status("⚠ Command cancelled", is_error=True)
        else:
            self._statusbar.set_status(f"❌ Command failed (exit code {exit_code})", is_error=True)

    def _on_toolbar_action(self, action: str):
        """Handle toolbar button clicks."""
        if action == "__CANCEL__":
            self._cancel_process()
            return

        if action == "cargo new":
            NewProjectDialog(self._root, self._cwd, self._on_command)
            return

        if self._is_busy:
            return

        self._tab_manager.write_line("", OutputType.NORMAL)
        self._on_command(action)

    def _on_file_browser_action(self, action: str, path: str):
        """Handle file browser interactions."""
        if action == "cd":
            self._cwd = path
            self._tab_manager.update_active_cwd(self._cwd)
            self._statusbar.update_cwd(self._cwd)
            self._file_browser.set_root(self._cwd)
        elif action == "open":
            if path.endswith("Cargo.toml"):
                self._open_toml_editor_for(path)
            elif path.endswith(".rs"):
                # Show with syntax highlighting
                self._on_command(f"type {path}")
            else:
                self._on_command(f"type {path}")

    def _show_highlighted_file(self, filepath: str, result):
        """Display a Rust file with syntax highlighting."""
        terminal = self._tab_manager.active_terminal
        if not terminal:
            return

        # Get the raw file content from the result
        content = ""
        if result.lines:
            content = "\n".join(text for text, _ in result.lines)
        elif result.output:
            content = result.output

        if not content.strip():
            self._tab_manager.show_result(result)
            return

        # Setup syntax tags on the terminal text widget
        SyntaxHighlighter.setup_tags(terminal._text)

        # Write with line numbers
        formatted = SyntaxHighlighter.format_with_line_numbers(content)
        for text, tag in formatted:
            terminal._text.insert(tk.END, text, tag)

        # Apply syntax highlighting over the inserted code
        start_line = terminal._text.index(tk.END).split(".")[0]
        code_start_line = int(start_line) - content.count("\n") - 1
        SyntaxHighlighter.highlight_rust_code(terminal._text, content, f"{code_start_line}.0")
        terminal._text.see(tk.END)

    def _toggle_file_browser(self):
        """Toggle file browser panel visibility."""
        if self._file_browser_visible:
            self._main_pane.forget(self._browser_frame)
            self._file_browser_visible = False
        else:
            self._main_pane.add(
                self._browser_frame, before=self._terminal_frame, minsize=180, width=250
            )
            self._file_browser_visible = True

    def _open_toml_editor(self):
        """Open Cargo.toml editor for the current workspace."""
        toml_path = os.path.join(self._cwd, "Cargo.toml")
        if not os.path.isfile(toml_path):
            # Search subdirectories
            for entry in os.listdir(self._cwd):
                candidate = os.path.join(self._cwd, entry, "Cargo.toml")
                if os.path.isfile(candidate):
                    toml_path = candidate
                    break
            else:
                self._tab_manager.write_line(
                    "No Cargo.toml found in current directory.", OutputType.WARNING
                )
                self._tab_manager.finish_command()
                return

        self._open_toml_editor_for(toml_path)

    def _open_toml_editor_for(self, toml_path: str):
        """Open the TOML editor for a specific file."""

        def on_save():
            self._tab_manager.write_line(f"Cargo.toml saved: {toml_path}", OutputType.SUCCESS)
            self._file_browser.refresh()

        TomlEditorDialog(self._root, toml_path, on_save)

    def _cancel_process(self):
        """Cancel the running process."""
        if self._is_busy:
            self._router.cancel_running()
            logger.info("Process cancellation requested")

    def _set_busy(self, busy: bool):
        """Update busy state across all components."""
        self._is_busy = busy
        self._tab_manager.set_busy(busy)
        self._toolbar.set_busy(busy)
        self._statusbar.set_busy(busy)

    def _on_close(self):
        """Handle window close."""
        if self._is_busy:
            if not messagebox.askyesno("Confirm Exit", "A process is still running. Exit anyway?"):
                return
            self._router.cancel_running()

        logger.info("Application closing")
        self._root.destroy()

    def run(self):
        """Start the application main loop."""
        self._root.mainloop()

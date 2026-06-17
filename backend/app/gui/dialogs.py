"""
Custom dialog windows for the application.
"""

import os
import tkinter as tk
from collections.abc import Callable
from tkinter import font as tkfont

from app.config import Font, Theme


class NewProjectDialog(tk.Toplevel):
    """Dialog for creating a new Rust project with options."""

    def __init__(self, parent, cwd: str, on_create: Callable[[str], None]):
        super().__init__(parent)
        self._on_create = on_create
        self._cwd = cwd

        self.title("New Rust Project")
        self.configure(bg=Theme.TOOLBAR_BG)
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        # Center on parent
        self.geometry("450x320")
        self.update_idletasks()
        x = parent.winfo_rootx() + (parent.winfo_width() - 450) // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - 320) // 2
        self.geometry(f"+{x}+{y}")

        self._font = tkfont.Font(family="Consolas", size=Font.SIZE_SMALL)
        self._font_title = tkfont.Font(family="Consolas", size=14, weight="bold")

        self._build_ui()

    def _build_ui(self):
        """Build dialog UI."""
        # Title
        tk.Label(
            self,
            text="🦀 Create New Rust Project",
            bg=Theme.TOOLBAR_BG,
            fg="#E06C00",
            font=self._font_title,
            pady=12,
        ).pack(fill=tk.X)

        # Form frame
        form = tk.Frame(self, bg=Theme.TOOLBAR_BG, padx=24, pady=8)
        form.pack(fill=tk.BOTH, expand=True)

        # Project name
        tk.Label(
            form,
            text="Project Name:",
            bg=Theme.TOOLBAR_BG,
            fg=Theme.TOOLBAR_BTN_TEXT,
            font=self._font,
            anchor=tk.W,
        ).pack(fill=tk.X, pady=(8, 2))
        self._name_entry = tk.Entry(
            form,
            bg="#1A1A1A",
            fg=Theme.FG,
            insertbackground=Theme.FG,
            font=self._font,
            relief=tk.FLAT,
            borderwidth=4,
        )
        self._name_entry.pack(fill=tk.X, pady=(0, 8))
        self._name_entry.focus_set()

        # Project type
        tk.Label(
            form,
            text="Project Type:",
            bg=Theme.TOOLBAR_BG,
            fg=Theme.TOOLBAR_BTN_TEXT,
            font=self._font,
            anchor=tk.W,
        ).pack(fill=tk.X, pady=(8, 2))

        self._project_type = tk.StringVar(value="bin")
        type_frame = tk.Frame(form, bg=Theme.TOOLBAR_BG)
        type_frame.pack(fill=tk.X, pady=(0, 8))

        for text, value in [("Binary (--bin)", "bin"), ("Library (--lib)", "lib")]:
            tk.Radiobutton(
                type_frame,
                text=text,
                variable=self._project_type,
                value=value,
                bg=Theme.TOOLBAR_BG,
                fg=Theme.TOOLBAR_BTN_TEXT,
                selectcolor=Theme.BG,
                activebackground=Theme.TOOLBAR_BG,
                activeforeground=Theme.FG,
                font=self._font,
            ).pack(side=tk.LEFT, padx=(0, 16))

        # Location display
        tk.Label(
            form,
            text="Location:",
            bg=Theme.TOOLBAR_BG,
            fg=Theme.TOOLBAR_BTN_TEXT,
            font=self._font,
            anchor=tk.W,
        ).pack(fill=tk.X, pady=(8, 2))
        self._location_label = tk.Label(
            form,
            text=self._cwd,
            bg="#1A1A1A",
            fg=Theme.FG_DIM,
            font=self._font,
            anchor=tk.W,
            padx=4,
            pady=4,
        )
        self._location_label.pack(fill=tk.X, pady=(0, 8))

        # Error label
        self._error_label = tk.Label(
            form,
            text="",
            bg=Theme.TOOLBAR_BG,
            fg=Theme.ERROR,
            font=self._font,
        )
        self._error_label.pack(fill=tk.X)

        # Buttons
        btn_frame = tk.Frame(self, bg=Theme.TOOLBAR_BG, pady=12, padx=24)
        btn_frame.pack(fill=tk.X)

        cancel_btn = tk.Label(
            btn_frame,
            text=" Cancel ",
            bg=Theme.TOOLBAR_BTN,
            fg=Theme.TOOLBAR_BTN_TEXT,
            font=self._font,
            padx=16,
            pady=6,
            cursor="hand2",
        )
        cancel_btn.pack(side=tk.RIGHT, padx=4)
        cancel_btn.bind("<Button-1>", lambda e: self.destroy())
        cancel_btn.bind("<Enter>", lambda e: cancel_btn.config(bg=Theme.TOOLBAR_BTN_HOVER))
        cancel_btn.bind("<Leave>", lambda e: cancel_btn.config(bg=Theme.TOOLBAR_BTN))

        create_btn = tk.Label(
            btn_frame,
            text=" Create ",
            bg="#007ACC",
            fg="#FFFFFF",
            font=self._font,
            padx=16,
            pady=6,
            cursor="hand2",
        )
        create_btn.pack(side=tk.RIGHT, padx=4)
        create_btn.bind("<Button-1>", lambda e: self._on_submit())
        create_btn.bind("<Enter>", lambda e: create_btn.config(bg="#0098FF"))
        create_btn.bind("<Leave>", lambda e: create_btn.config(bg="#007ACC"))

        # Enter key
        self.bind("<Return>", lambda e: self._on_submit())
        self.bind("<Escape>", lambda e: self.destroy())

    def _on_submit(self):
        """Validate and submit."""
        name = self._name_entry.get().strip()

        if not name:
            self._error_label.config(text="Project name is required.")
            return

        if not all(c.isalnum() or c in "-_" for c in name):
            self._error_label.config(text="Invalid name. Use alphanumeric, '-', or '_'.")
            return

        if os.path.exists(os.path.join(self._cwd, name)):
            self._error_label.config(text=f"Directory '{name}' already exists.")
            return

        ptype = self._project_type.get()
        cmd = f"cargo new {name} --{ptype}"
        self.destroy()
        self._on_create(cmd)

"""
Cargo.toml visual editor dialog.
Provides a form-based UI for editing common Cargo.toml fields:
package name, version, edition, authors, dependencies, and features.
"""
import os
import tkinter as tk
from tkinter import font as tkfont, messagebox
from typing import Optional

from app.config import Theme, Font
from app.logger import logger


class TomlParser:
    """Minimal TOML parser/writer for Cargo.toml files.
    Handles the subset of TOML used in typical Cargo.toml files.
    """

    @staticmethod
    def parse(content: str) -> dict:
        """Parse a Cargo.toml string into a nested dict."""
        result = {}
        current_section = result
        current_key = ""

        for raw_line in content.split("\n"):
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue

            # Section header [section]
            if line.startswith("[") and line.endswith("]"):
                section_name = line[1:-1].strip()
                parts = section_name.split(".")
                current = result
                for part in parts:
                    if part not in current:
                        current[part] = {}
                    current = current[part]
                current_section = current
                current_key = section_name
                continue

            # Key = value
            if "=" in line:
                key, _, value = line.partition("=")
                key = key.strip()
                value = value.strip()

                # Remove quotes from string values
                if value.startswith('"') and value.endswith('"'):
                    value = value[1:-1]
                elif value.startswith('[') and value.endswith(']'):
                    # Simple array parsing
                    inner = value[1:-1].strip()
                    if inner:
                        items = [v.strip().strip('"').strip("'") for v in inner.split(",") if v.strip()]
                        value = items
                    else:
                        value = []

                current_section[key] = value

        return result

    @staticmethod
    def serialize(data: dict, indent: int = 0) -> str:
        """Serialize a dict back to TOML format."""
        lines = []
        prefix = ""

        # Write top-level key-value pairs first
        for key, value in data.items():
            if not isinstance(value, dict):
                lines.append(f"{key} = {TomlParser._format_value(value)}")

        if lines:
            lines.append("")

        # Write sections
        for key, value in data.items():
            if isinstance(value, dict):
                TomlParser._write_section(lines, key, value)

        return "\n".join(lines) + "\n"

    @staticmethod
    def _write_section(lines: list, section: str, data: dict):
        """Write a TOML section."""
        # Check for nested sections
        simple_keys = {k: v for k, v in data.items() if not isinstance(v, dict)}
        nested_keys = {k: v for k, v in data.items() if isinstance(v, dict)}

        if simple_keys:
            lines.append(f"[{section}]")
            for key, value in simple_keys.items():
                lines.append(f"{key} = {TomlParser._format_value(value)}")
            lines.append("")

        for key, value in nested_keys.items():
            TomlParser._write_section(lines, f"{section}.{key}", value)

    @staticmethod
    def _format_value(value) -> str:
        """Format a value for TOML output."""
        if isinstance(value, list):
            items = ", ".join(f'"{v}"' for v in value)
            return f"[{items}]"
        elif isinstance(value, bool):
            return "true" if value else "false"
        elif isinstance(value, (int, float)):
            return str(value)
        else:
            return f'"{value}"'


class TomlEditorDialog(tk.Toplevel):
    """Visual editor for Cargo.toml files."""

    def __init__(self, parent, toml_path: str, on_save: Optional[callable] = None):
        super().__init__(parent)
        self._toml_path = toml_path
        self._on_save = on_save
        self._data: dict = {}
        self._dep_entries: list[tuple[tk.Entry, tk.Entry]] = []

        self.title(f"Cargo.toml Editor - {os.path.basename(os.path.dirname(toml_path))}")
        self.configure(bg=Theme.TOOLBAR_BG)
        self.transient(parent)
        self.grab_set()
        self.geometry("600x580")
        self.resizable(True, True)

        # Center on parent
        self.update_idletasks()
        x = parent.winfo_rootx() + (parent.winfo_width() - 600) // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - 580) // 2
        self.geometry(f"+{x}+{y}")

        self._font = tkfont.Font(family="Consolas", size=Font.SIZE_SMALL)
        self._font_title = tkfont.Font(family="Consolas", size=13, weight="bold")
        self._font_section = tkfont.Font(family="Consolas", size=Font.SIZE_SMALL, weight="bold")

        self._load_toml()
        self._build_ui()

    def _load_toml(self):
        """Load and parse the Cargo.toml file."""
        try:
            with open(self._toml_path, "r", encoding="utf-8") as f:
                content = f.read()
            self._data = TomlParser.parse(content)
            logger.info("Loaded Cargo.toml: %s", self._toml_path)
        except Exception as e:
            self._data = {}
            logger.error("Failed to load Cargo.toml: %s", e)

    def _build_ui(self):
        """Build the editor UI."""
        # Title bar
        title_frame = tk.Frame(self, bg="#1A5276", padx=12, pady=8)
        title_frame.pack(fill=tk.X)
        tk.Label(title_frame, text="📋 Cargo.toml Editor", bg="#1A5276", fg="#FFFFFF",
                 font=self._font_title).pack(side=tk.LEFT)

        # Scrollable content
        canvas = tk.Canvas(self, bg=Theme.TOOLBAR_BG, highlightthickness=0)
        scrollbar = tk.Scrollbar(self, orient=tk.VERTICAL, command=canvas.yview)
        self._content = tk.Frame(canvas, bg=Theme.TOOLBAR_BG, padx=16, pady=8)

        self._content.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self._content, anchor=tk.NW)
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # [package] section
        self._add_section_header("[package]")
        pkg = self._data.get("package", {})

        self._name_var = self._add_field("Name", pkg.get("name", ""))
        self._version_var = self._add_field("Version", pkg.get("version", "0.1.0"))
        self._edition_var = self._add_field("Edition", pkg.get("edition", "2021"))
        self._authors_var = self._add_field("Authors", ", ".join(pkg.get("authors", [])) if isinstance(pkg.get("authors"), list) else pkg.get("authors", ""))
        self._description_var = self._add_field("Description", pkg.get("description", ""))
        self._license_var = self._add_field("License", pkg.get("license", ""))

        # [dependencies] section
        self._add_section_header("[dependencies]")
        deps = self._data.get("dependencies", {})

        self._deps_frame = tk.Frame(self._content, bg=Theme.TOOLBAR_BG)
        self._deps_frame.pack(fill=tk.X, pady=(0, 4))

        # Header row
        dep_header = tk.Frame(self._deps_frame, bg=Theme.TOOLBAR_BG)
        dep_header.pack(fill=tk.X)
        tk.Label(dep_header, text="Crate", bg=Theme.TOOLBAR_BG, fg="#AAAAAA",
                 font=self._font, width=20, anchor=tk.W).pack(side=tk.LEFT, padx=(0, 8))
        tk.Label(dep_header, text="Version", bg=Theme.TOOLBAR_BG, fg="#AAAAAA",
                 font=self._font, width=15, anchor=tk.W).pack(side=tk.LEFT)

        for dep_name, dep_version in deps.items():
            if isinstance(dep_version, dict):
                ver_str = dep_version.get("version", "")
            else:
                ver_str = str(dep_version)
            self._add_dependency_row(dep_name, ver_str)

        # Add dependency button
        add_btn = tk.Label(
            self._content, text=" + Add Dependency ", bg="#2D5F2D", fg="#AAFFAA",
            font=self._font, cursor="hand2", padx=8, pady=3,
        )
        add_btn.pack(anchor=tk.W, pady=(4, 12))
        add_btn.bind("<Button-1>", lambda e: self._add_dependency_row("", ""))
        add_btn.bind("<Enter>", lambda e: add_btn.config(bg="#3D7F3D"))
        add_btn.bind("<Leave>", lambda e: add_btn.config(bg="#2D5F2D"))

        # [features] section (read-only display)
        features = self._data.get("features", {})
        if features:
            self._add_section_header("[features]")
            for feat_name, feat_deps in features.items():
                deps_str = ", ".join(feat_deps) if isinstance(feat_deps, list) else str(feat_deps)
                row = tk.Frame(self._content, bg=Theme.TOOLBAR_BG)
                row.pack(fill=tk.X, pady=1)
                tk.Label(row, text=f"  {feat_name}", bg=Theme.TOOLBAR_BG, fg="#E8C36A",
                         font=self._font, anchor=tk.W).pack(side=tk.LEFT)
                tk.Label(row, text=f" = [{deps_str}]", bg=Theme.TOOLBAR_BG, fg="#888888",
                         font=self._font, anchor=tk.W).pack(side=tk.LEFT)

        # Buttons
        btn_frame = tk.Frame(self, bg=Theme.TOOLBAR_BG, pady=10, padx=16)
        btn_frame.pack(fill=tk.X, side=tk.BOTTOM)

        tk.Frame(self, bg=Theme.BORDER, height=1).pack(fill=tk.X, side=tk.BOTTOM)

        cancel_btn = tk.Label(
            btn_frame, text=" Cancel ", bg=Theme.TOOLBAR_BTN, fg=Theme.TOOLBAR_BTN_TEXT,
            font=self._font, padx=16, pady=6, cursor="hand2",
        )
        cancel_btn.pack(side=tk.RIGHT, padx=4)
        cancel_btn.bind("<Button-1>", lambda e: self.destroy())
        cancel_btn.bind("<Enter>", lambda e: cancel_btn.config(bg=Theme.TOOLBAR_BTN_HOVER))
        cancel_btn.bind("<Leave>", lambda e: cancel_btn.config(bg=Theme.TOOLBAR_BTN))

        save_btn = tk.Label(
            btn_frame, text=" 💾 Save ", bg="#007ACC", fg="#FFFFFF",
            font=self._font, padx=16, pady=6, cursor="hand2",
        )
        save_btn.pack(side=tk.RIGHT, padx=4)
        save_btn.bind("<Button-1>", lambda e: self._save())
        save_btn.bind("<Enter>", lambda e: save_btn.config(bg="#0098FF"))
        save_btn.bind("<Leave>", lambda e: save_btn.config(bg="#007ACC"))

        self.bind("<Escape>", lambda e: self.destroy())

    def _add_section_header(self, text: str):
        """Add a section header label."""
        tk.Label(
            self._content, text=text, bg=Theme.TOOLBAR_BG, fg="#569CD6",
            font=self._font_section, anchor=tk.W, pady=(8, 2),
        ).pack(fill=tk.X, pady=(12, 4))
        tk.Frame(self._content, bg="#333333", height=1).pack(fill=tk.X, pady=(0, 6))

    def _add_field(self, label: str, value: str) -> tk.StringVar:
        """Add a labeled text field and return its StringVar."""
        row = tk.Frame(self._content, bg=Theme.TOOLBAR_BG)
        row.pack(fill=tk.X, pady=3)

        tk.Label(row, text=f"{label}:", bg=Theme.TOOLBAR_BG, fg=Theme.TOOLBAR_BTN_TEXT,
                 font=self._font, width=12, anchor=tk.W).pack(side=tk.LEFT)

        var = tk.StringVar(value=value)
        entry = tk.Entry(
            row, textvariable=var, bg="#1A1A1A", fg=Theme.FG,
            insertbackground=Theme.FG, font=self._font, relief=tk.FLAT, borderwidth=4,
        )
        entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        return var

    def _add_dependency_row(self, name: str, version: str):
        """Add a dependency name/version row."""
        row = tk.Frame(self._deps_frame, bg=Theme.TOOLBAR_BG)
        row.pack(fill=tk.X, pady=1)

        name_entry = tk.Entry(
            row, bg="#1A1A1A", fg="#E8C36A", insertbackground=Theme.FG,
            font=self._font, relief=tk.FLAT, borderwidth=3, width=20,
        )
        name_entry.pack(side=tk.LEFT, padx=(0, 8))
        name_entry.insert(0, name)

        ver_entry = tk.Entry(
            row, bg="#1A1A1A", fg="#B5CEA8", insertbackground=Theme.FG,
            font=self._font, relief=tk.FLAT, borderwidth=3, width=15,
        )
        ver_entry.pack(side=tk.LEFT)
        ver_entry.insert(0, version)

        # Remove button
        rm_btn = tk.Label(
            row, text=" ✕ ", bg=Theme.TOOLBAR_BG, fg="#AA4444",
            font=self._font, cursor="hand2",
        )
        rm_btn.pack(side=tk.LEFT, padx=4)
        rm_btn.bind("<Button-1>", lambda e, r=row, pair=(name_entry, ver_entry): self._remove_dep(r, pair))
        rm_btn.bind("<Enter>", lambda e: rm_btn.config(fg="#FF6666"))
        rm_btn.bind("<Leave>", lambda e: rm_btn.config(fg="#AA4444"))

        self._dep_entries.append((name_entry, ver_entry))

    def _remove_dep(self, row: tk.Frame, pair: tuple):
        """Remove a dependency row."""
        if pair in self._dep_entries:
            self._dep_entries.remove(pair)
        row.destroy()

    def _save(self):
        """Save changes back to Cargo.toml."""
        # Build updated data
        data = {}

        # Package section
        pkg = {}
        if self._name_var.get().strip():
            pkg["name"] = self._name_var.get().strip()
        if self._version_var.get().strip():
            pkg["version"] = self._version_var.get().strip()
        if self._edition_var.get().strip():
            pkg["edition"] = self._edition_var.get().strip()
        authors = self._authors_var.get().strip()
        if authors:
            pkg["authors"] = [a.strip() for a in authors.split(",")]
        if self._description_var.get().strip():
            pkg["description"] = self._description_var.get().strip()
        if self._license_var.get().strip():
            pkg["license"] = self._license_var.get().strip()
        data["package"] = pkg

        # Dependencies
        deps = {}
        for name_entry, ver_entry in self._dep_entries:
            name = name_entry.get().strip()
            version = ver_entry.get().strip()
            if name:
                deps[name] = version if version else "*"
        if deps:
            data["dependencies"] = deps

        # Preserve features if they existed
        if "features" in self._data:
            data["features"] = self._data["features"]

        try:
            content = TomlParser.serialize(data)
            with open(self._toml_path, "w", encoding="utf-8") as f:
                f.write(content)
            logger.info("Saved Cargo.toml: %s", self._toml_path)
            if self._on_save:
                self._on_save()
            self.destroy()
        except Exception as e:
            messagebox.showerror("Save Error", f"Failed to save: {e}", parent=self)
            logger.error("Failed to save Cargo.toml: %s", e)

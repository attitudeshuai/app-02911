"""
File browser panel.
Displays the project directory tree with expand/collapse, file icons,
and double-click to open files in the terminal via 'type' command.
"""
import os
import tkinter as tk
from tkinter import font as tkfont
from typing import Callable, Optional

from app.config import Theme, Font
from app.logger import logger


# File type icon mapping
FILE_ICONS = {
    ".rs": "🦀",
    ".toml": "📋",
    ".lock": "🔒",
    ".md": "📝",
    ".txt": "📄",
    ".json": "📦",
    ".yaml": "📦",
    ".yml": "📦",
    ".gitignore": "🙈",
}

FOLDER_OPEN = "📂"
FOLDER_CLOSED = "📁"


class FileTreeNode:
    """Represents a node in the file tree."""

    __slots__ = ("path", "name", "is_dir", "depth", "expanded", "children_loaded")

    def __init__(self, path: str, name: str, is_dir: bool, depth: int):
        self.path = path
        self.name = name
        self.is_dir = is_dir
        self.depth = depth
        self.expanded = False
        self.children_loaded = False


class FileBrowser(tk.Frame):
    """A tree-style file browser panel with expand/collapse support."""

    def __init__(self, parent, root_path: str, on_file_action: Callable[[str, str], None], **kwargs):
        """
        Args:
            parent: Parent widget.
            root_path: Root directory to browse.
            on_file_action: Callback(action, path) - action is 'open' or 'cd'.
        """
        super().__init__(parent, bg=Theme.TOOLBAR_BG, **kwargs)
        self._root_path = root_path
        self._on_file_action = on_file_action
        self._nodes: list[FileTreeNode] = []
        self._selected_index: Optional[int] = -1

        self._setup_ui()
        self.refresh()

    def _setup_ui(self):
        """Build the file browser UI."""
        # Header
        header = tk.Frame(self, bg=Theme.TOOLBAR_BG)
        header.pack(fill=tk.X)

        self._title = tk.Label(
            header, text=" 📁 FILE EXPLORER", bg=Theme.TOOLBAR_BG,
            fg="#CCCCCC", font=tkfont.Font(family="Consolas", size=Font.SIZE_SMALL, weight="bold"),
            anchor=tk.W, padx=6, pady=4,
        )
        self._title.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Refresh button
        refresh_btn = tk.Label(
            header, text=" ↻ ", bg=Theme.TOOLBAR_BG, fg="#AAAAAA",
            font=tkfont.Font(family="Consolas", size=Font.SIZE_SMALL),
            cursor="hand2", padx=4,
        )
        refresh_btn.pack(side=tk.RIGHT, padx=4)
        refresh_btn.bind("<Button-1>", lambda e: self.refresh())
        refresh_btn.bind("<Enter>", lambda e: refresh_btn.config(fg="#FFFFFF"))
        refresh_btn.bind("<Leave>", lambda e: refresh_btn.config(fg="#AAAAAA"))

        # Collapse all button
        collapse_btn = tk.Label(
            header, text=" ⊟ ", bg=Theme.TOOLBAR_BG, fg="#AAAAAA",
            font=tkfont.Font(family="Consolas", size=Font.SIZE_SMALL),
            cursor="hand2", padx=4,
        )
        collapse_btn.pack(side=tk.RIGHT)
        collapse_btn.bind("<Button-1>", lambda e: self._collapse_all())
        collapse_btn.bind("<Enter>", lambda e: collapse_btn.config(fg="#FFFFFF"))
        collapse_btn.bind("<Leave>", lambda e: collapse_btn.config(fg="#AAAAAA"))

        tk.Frame(self, bg=Theme.BORDER, height=1).pack(fill=tk.X)

        # Tree area with scrollbar
        tree_frame = tk.Frame(self, bg=Theme.TOOLBAR_BG)
        tree_frame.pack(fill=tk.BOTH, expand=True)

        self._scrollbar = tk.Scrollbar(tree_frame, bg=Theme.SCROLLBAR,
                                       troughcolor=Theme.TOOLBAR_BG, highlightthickness=0, bd=0)
        self._scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self._canvas = tk.Canvas(
            tree_frame, bg=Theme.TOOLBAR_BG, highlightthickness=0,
            yscrollcommand=self._scrollbar.set,
        )
        self._canvas.pack(fill=tk.BOTH, expand=True)
        self._scrollbar.config(command=self._canvas.yview)

        self._inner_frame = tk.Frame(self._canvas, bg=Theme.TOOLBAR_BG)
        self._canvas_window = self._canvas.create_window((0, 0), window=self._inner_frame, anchor=tk.NW)

        self._inner_frame.bind("<Configure>", self._on_frame_configure)
        self._canvas.bind("<Configure>", self._on_canvas_configure)
        self._canvas.bind_all("<MouseWheel>", self._on_mousewheel, add="+")

    def _on_frame_configure(self, event):
        self._canvas.configure(scrollregion=self._canvas.bbox("all"))

    def _on_canvas_configure(self, event):
        self._canvas.itemconfig(self._canvas_window, width=event.width)

    def _on_mousewheel(self, event):
        """Handle mouse wheel scrolling."""
        if self.winfo_containing(event.x_root, event.y_root):
            self._canvas.yview_scroll(-1 * (event.delta // 120 or (1 if event.delta > 0 else -1)), "units")

    def set_root(self, path: str):
        """Change the root directory."""
        self._root_path = path
        self.refresh()

    def refresh(self):
        """Reload the file tree from disk."""
        self._nodes.clear()
        for widget in self._inner_frame.winfo_children():
            widget.destroy()

        if not os.path.isdir(self._root_path):
            tk.Label(self._inner_frame, text="  (no directory)", bg=Theme.TOOLBAR_BG,
                     fg="#666666", font=("Consolas", Font.SIZE_SMALL)).pack(anchor=tk.W)
            return

        # Add root node expanded
        root_node = FileTreeNode(self._root_path, os.path.basename(self._root_path) or self._root_path,
                                 True, 0)
        root_node.expanded = True
        root_node.children_loaded = True
        self._nodes.append(root_node)

        self._load_children(self._root_path, 1)
        self._render_tree()
        logger.debug("File browser refreshed: %s", self._root_path)

    def _load_children(self, parent_path: str, depth: int, max_depth: int = 6):
        """Load child entries for a directory."""
        if depth > max_depth:
            return
        try:
            entries = sorted(os.listdir(parent_path), key=lambda e: (not os.path.isdir(os.path.join(parent_path, e)), e.lower()))
        except PermissionError:
            return

        for entry in entries:
            if entry.startswith(".") and entry not in (".gitignore",):
                continue
            full = os.path.join(parent_path, entry)
            is_dir = os.path.isdir(full)
            node = FileTreeNode(full, entry, is_dir, depth)
            self._nodes.append(node)

    def _render_tree(self):
        """Render the visible tree nodes."""
        for widget in self._inner_frame.winfo_children():
            widget.destroy()

        visible = self._get_visible_nodes()
        for i, node in enumerate(visible):
            self._render_node(node, i)

    def _get_visible_nodes(self) -> list[FileTreeNode]:
        """Get list of nodes that should be visible based on expand state."""
        visible = []
        skip_depth = -1

        for node in self._nodes:
            if skip_depth >= 0 and node.depth > skip_depth:
                continue
            skip_depth = -1

            visible.append(node)

            if node.is_dir and not node.expanded:
                skip_depth = node.depth

        return visible

    def _render_node(self, node: FileTreeNode, index: int):
        """Render a single tree node."""
        indent = "  " * node.depth

        if node.is_dir:
            icon = FOLDER_OPEN if node.expanded else FOLDER_CLOSED
        else:
            ext = os.path.splitext(node.name)[1].lower()
            icon = FILE_ICONS.get(ext, "📄")

        text = f"{indent}{icon} {node.name}"
        fg = "#E8C36A" if node.is_dir else "#CCCCCC"

        row = tk.Label(
            self._inner_frame, text=text, bg=Theme.TOOLBAR_BG, fg=fg,
            font=("Consolas", Font.SIZE_SMALL), anchor=tk.W, padx=4, pady=1,
            cursor="hand2",
        )
        row.pack(fill=tk.X)
        row.bind("<Enter>", lambda e, r=row: r.config(bg="#2A2D2E"))
        row.bind("<Leave>", lambda e, r=row: r.config(bg=Theme.TOOLBAR_BG))
        row.bind("<Button-1>", lambda e, n=node: self._on_node_click(n))
        row.bind("<Double-Button-1>", lambda e, n=node: self._on_node_double_click(n))

    def _on_node_click(self, node: FileTreeNode):
        """Handle single click - toggle expand for dirs."""
        if node.is_dir:
            node.expanded = not node.expanded
            if node.expanded and not node.children_loaded:
                # Insert children after this node
                idx = self._nodes.index(node)
                children_before = len(self._nodes)
                temp_nodes = []
                self._nodes_temp = temp_nodes
                try:
                    entries = sorted(os.listdir(node.path),
                                     key=lambda e: (not os.path.isdir(os.path.join(node.path, e)), e.lower()))
                except PermissionError:
                    entries = []

                insert_pos = idx + 1
                for entry in entries:
                    if entry.startswith(".") and entry not in (".gitignore",):
                        continue
                    full = os.path.join(node.path, entry)
                    is_dir = os.path.isdir(full)
                    child = FileTreeNode(full, entry, is_dir, node.depth + 1)
                    self._nodes.insert(insert_pos, child)
                    insert_pos += 1

                node.children_loaded = True

            self._render_tree()

    def _on_node_double_click(self, node: FileTreeNode):
        """Handle double click - open file or cd into directory."""
        if node.is_dir:
            self._on_file_action("cd", node.path)
        else:
            self._on_file_action("open", node.path)

    def _collapse_all(self):
        """Collapse all directories."""
        for node in self._nodes:
            if node.is_dir and node.depth > 0:
                node.expanded = False
        self._render_tree()

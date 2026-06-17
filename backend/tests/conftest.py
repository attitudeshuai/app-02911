"""
Shared pytest fixtures and helpers.

The command layer (app.commands.*) is GUI-free and can be tested without a
display. GUI smoke tests are gated behind the `gui` marker and a display probe
so they skip cleanly on headless machines.
"""

import os
import sys

import pytest

# Ensure the backend package is importable when tests run from the repo root.
_BACKEND = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _BACKEND not in sys.path:
    sys.path.insert(0, _BACKEND)


def _has_display() -> bool:
    """Return True if a Tk display is available on this machine."""
    try:
        import tkinter as tk
    except ImportError:
        return False
    try:
        root = tk.Tk()
        root.destroy()
        return True
    except Exception:
        return False


@pytest.fixture(scope="session")
def has_display():
    """Session-cached display availability probe."""
    return _has_display()


def require_display():
    """Skip the calling test if no display is available."""
    if not _has_display():
        pytest.skip("no display available (set DISPLAY or run under xvfb-run)")

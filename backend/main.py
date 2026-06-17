#!/usr/bin/env python3
"""
Rust Cargo DOS Commander
========================
A DOS-style terminal GUI for managing Rust/Cargo projects.
Supports project creation, building, running, and common DOS commands.

Usage:
    python main.py
"""

import os
import sys

# Ensure app package is importable
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.gui.main_window import MainWindow
from app.logger import logger


def main():
    """Application entry point.

    Pass ``--smoke`` to build the window, run the main loop briefly, then
    auto-close. Used by CI / pre-push to verify the app actually launches
    without requiring a human to click around.
    """
    smoke = "--smoke" in sys.argv
    logger.info("=" * 60)
    logger.info("Rust Cargo DOS Commander starting...%s", " [smoke]" if smoke else "")
    logger.info("=" * 60)

    try:
        window = MainWindow()
        if smoke:
            logger.info("Smoke mode: scheduling auto-close in 800ms")
            window._root.after(800, window._root.destroy)
        window.run()
    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
    except Exception as e:
        logger.critical("Fatal error: %s", e, exc_info=True)
        print(f"\nFatal error: {e}", file=sys.stderr)
        sys.exit(1)

    logger.info("Application exited normally")


if __name__ == "__main__":
    main()

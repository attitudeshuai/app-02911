#!/usr/bin/env python3
"""
Rust Cargo DOS Commander
========================
A DOS-style terminal GUI for managing Rust/Cargo projects.
Supports project creation, building, running, and common DOS commands.

Usage:
    python main.py
"""
import sys
import os

# Ensure app package is importable
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.logger import logger
from app.gui.main_window import MainWindow


def main():
    """Application entry point."""
    logger.info("=" * 60)
    logger.info("Rust Cargo DOS Commander starting...")
    logger.info("=" * 60)

    try:
        window = MainWindow()
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

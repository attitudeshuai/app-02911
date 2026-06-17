#!/usr/bin/env python3
"""
Rust Cargo DOS Commander
========================
A DOS-style terminal GUI for managing Rust/Cargo projects.
Supports project creation, building, running, and common DOS commands.

Usage:
    python main.py                  # Start GUI (default)
    python main.py --headless       # Start interactive headless CLI
    python main.py --check          # Run smoke test and exit
    python main.py --version        # Show version
"""
import sys
import os
import argparse
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import app
from app.logger import logger
from app.commands.command_router import CommandRouter
from app.commands.base import OutputType


def _print_result(result):
    """Print a CommandResult to stdout with basic color cues."""
    for text, otype in result.lines:
        if otype == OutputType.ERROR:
            print(f"\033[91m{text}\033[0m")
        elif otype == OutputType.WARNING:
            print(f"\033[93m{text}\033[0m")
        elif otype == OutputType.INFO:
            print(f"\033[96m{text}\033[0m")
        elif otype == OutputType.SUCCESS:
            print(f"\033[92m{text}\033[0m")
        elif otype == OutputType.SYSTEM:
            print(f"\033[90m{text}\033[0m")
        else:
            print(text)


def run_smoke_check() -> int:
    """Run a quick smoke test: verify imports, basic commands, and exit.

    Returns exit code 0 on success, non-zero on failure.
    """
    print("=" * 60)
    print(f"  Rust Cargo DOS Commander v{app.__version__} - Smoke Check")
    print("=" * 60)
    print()

    checks_passed = 0
    checks_total = 0

    def check(name, condition):
        nonlocal checks_passed, checks_total
        checks_total += 1
        status = "\033[92mPASS\033[0m" if condition else "\033[91mFAIL\033[0m"
        print(f"  [{status}] {name}")
        if condition:
            checks_passed += 1

    print("[1/5] Core module imports...")
    try:
        from app.config import Theme, Window, App
        from app.commands.base import CommandResult, OutputType
        from app.commands.command_router import CommandRouter
        from app.commands.dos_commands import DosCommands
        from app.commands.cargo_executor import CargoExecutor
        check("config module importable", True)
        check("command modules importable", True)
    except Exception as e:
        check(f"module import failed: {e}", False)
        return 1

    print()
    print("[2/5] GUI module imports (proves app.gui is bundled)...")
    gui_ok = True
    try:
        import tkinter
        check("tkinter module importable", True)
    except Exception as e:
        check(f"tkinter import failed: {e}", False)
        gui_ok = False

    try:
        from app.gui.main_window import MainWindow
        from app.gui.tab_terminal import TabTerminalManager
        from app.gui.terminal_widget import TerminalWidget
        from app.gui.toolbar import Toolbar
        from app.gui.statusbar import StatusBar
        from app.gui.file_browser import FileBrowser
        from app.gui.dialogs import NewProjectDialog
        from app.gui.toml_editor import TomlEditorDialog
        from app.gui.syntax_highlight import SyntaxHighlighter
        from app.gui.autocomplete import AutocompletePopup, AutocompleteEngine
        check("all app.gui modules importable", True)
    except Exception as e:
        check(f"app.gui import failed: {e}", False)
        gui_ok = False

    print()
    print("[3/5] CommandRouter instantiation...")
    try:
        router = CommandRouter()
        check("router created", True)
    except Exception as e:
        check(f"router creation failed: {e}", False)
        return 1

    print()
    print("[4/5] Basic DOS commands...")
    with tempfile.TemporaryDirectory() as tmpdir:
        cwd = tmpdir

        result = router.execute("echo smoke_test_ok", cwd)
        check("echo command works", result.success and "smoke_test_ok" in str(result.lines))

        result = router.execute("ver", cwd)
        check("ver command works", result.success and "Version" in str(result.lines))

        result = router.execute("help", cwd)
        check("help command works", result.success and "Command Reference" in str(result.lines))

        result = router.execute("mkdir test_smoke_dir", cwd)
        check("mkdir command works", result.success and os.path.isdir(os.path.join(cwd, "test_smoke_dir")))

        result = router.execute("cd test_smoke_dir", cwd)
        check("cd command works", result.success and result.new_cwd is not None)

        result = router.execute("pwd", result.new_cwd or cwd)
        check("pwd command works", result.success)

        result = router.execute("cd ..", result.new_cwd or cwd)
        result = router.execute("rmdir test_smoke_dir", cwd)
        check("rmdir command works", result.success and not os.path.isdir(os.path.join(cwd, "test_smoke_dir")))

        result = router.execute("nonexistent_cmd_xyz", cwd)
        check("unknown command returns error", not result.success and "not recognized" in str(result.lines))

    print()
    print("[5/5] Cargo availability (optional)...")
    try:
        from app.commands.cargo_executor import CargoExecutor
        cargo_available = CargoExecutor.check_cargo_installed()
        version = CargoExecutor.get_cargo_version()
        if cargo_available:
            check(f"cargo installed: {version}", True)
        else:
            print(f"  [\033[93mWARN\033[0m] cargo not found - Rust commands will be unavailable")
            print(f"         Install from: https://rustup.rs/")
    except Exception as e:
        print(f"  [\033[93mWARN\033[0m] cargo check error: {e}")

    print()
    print("=" * 60)
    print(f"  Result: {checks_passed}/{checks_total} checks passed")
    print("=" * 60)

    if checks_passed == checks_total:
        print("\n\033[92mAll checks passed! Application is ready to run.\033[0m")
        return 0
    else:
        print(f"\n\033[91m{checks_total - checks_passed} check(s) failed.\033[0m")
        return 1


def run_headless_repl():
    """Run an interactive headless CLI session (no GUI)."""
    import os
    cwd = os.path.expanduser("~/rust_projects")
    os.makedirs(cwd, exist_ok=True)

    router = CommandRouter()

    print()
    print("=" * 60)
    print(f"  Rust Cargo DOS Commander v{app.__version__} - Headless Mode")
    print("=" * 60)
    print("  Type 'help' for commands, 'exit' to quit.")
    print("=" * 60)
    print()

    try:
        while True:
            try:
                prompt = f"{cwd}> "
                line = input(prompt)
            except EOFError:
                print()
                break

            if not line.strip():
                continue

            result = router.execute(line, cwd)

            if result.output == "__EXIT__":
                _print_result(result)
                print("Goodbye!")
                break

            if result.new_cwd:
                cwd = result.new_cwd

            _print_result(result)

    except KeyboardInterrupt:
        print("\nInterrupted by user.")

    logger.info("Headless session ended")


def run_gui():
    """Start the full GUI application."""
    from app.gui.main_window import MainWindow

    logger.info("=" * 60)
    logger.info("Rust Cargo DOS Commander starting (GUI mode)...")
    logger.info("=" * 60)

    window = MainWindow()
    window.run()
    logger.info("Application exited normally")


def main():
    parser = argparse.ArgumentParser(
        prog="cargo-commander",
        description="Rust Cargo DOS Commander - A DOS-style terminal GUI for Rust projects",
    )
    parser.add_argument(
        "--version", "-V",
        action="store_true",
        help="Show version and exit"
    )
    parser.add_argument(
        "--check", "--smoke-test",
        action="store_true",
        help="Run smoke test (imports + basic commands) and exit"
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run in headless CLI mode (no GUI window)"
    )
    parser.add_argument(
        "--command", "-c",
        type=str,
        default=None,
        help="Execute a single command and exit (implies --headless)"
    )

    args = parser.parse_args()

    if args.version:
        print(f"Rust Cargo DOS Commander v{app.__version__}")
        print(f"Python {sys.version.split()[0]} on {sys.platform}")
        return 0

    if args.command:
        args.headless = True

    if args.check:
        return run_smoke_check()

    if args.headless:
        if args.command:
            router = CommandRouter()
            cwd = os.getcwd()
            result = router.execute(args.command, cwd)
            _print_result(result)
            return 0 if result.success else 1
        else:
            run_headless_repl()
            return 0

    try:
        run_gui()
    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
    except Exception as e:
        logger.critical("Fatal error: %s", e, exc_info=True)
        print(f"\nFatal error: {e}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())

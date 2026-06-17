#!/usr/bin/env python3
"""
Rust Cargo DOS Commander
========================
A DOS-style terminal GUI for managing Rust/Cargo projects.
Supports project creation, building, running, and common DOS commands.

Usage:
    python main.py
    python main.py --smoke-test       # Headless smoke test (no GUI)
    python main.py --version          # Print version and exit
"""
import sys
import os
import argparse

# Ensure app package is importable
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def run_smoke_test(output_file=None):
    """Headless smoke test - verify app loads and basic commands work.

    Args:
        output_file: Optional path to write JSON result. Useful for GUI-mode
                     executables where stdout is not visible.

    Returns exit code: 0 = pass, 1 = fail.
    Used by CI and post-build validation to verify the executable works
    without launching the GUI.
    """
    import json
    import time

    result = {
        "success": False,
        "version": None,
        "checks": [],
        "timestamp": time.time(),
        "platform": {
            "system": __import__("platform").system(),
            "python": __import__("platform").python_version(),
        },
        "error": None,
    }

    def record(name, passed, detail=""):
        status = "PASS" if passed else "FAIL"
        print(f"[{status}] {name}")
        if detail:
            print(f"       {detail}")
        result["checks"].append({"name": name, "passed": passed, "detail": detail})

    try:
        import app
        from app.commands.command_router import CommandRouter
        from app.config import App, Theme, Window
        from app.commands.base import CommandResult, OutputType
        from app.commands.dos_commands import DosCommands
    except Exception as e:
        record("Import all modules", False, str(e))
        result["error"] = f"Import failed: {e}"
        if output_file:
            with open(output_file, "w") as f:
                json.dump(result, f, indent=2)
        return 1

    result["version"] = app.__version__
    record("App version", True, app.__version__)
    record("All modules imported", True)
    record("Theme loaded", True, f"bg={Theme.BG}")
    record("Window config", True, f"{Window.DEFAULT_WIDTH}x{Window.DEFAULT_HEIGHT}")

    try:
        router = CommandRouter()
        record("CommandRouter created", True)
    except Exception as e:
        record("CommandRouter created", False, str(e))
        result["error"] = f"CommandRouter init failed: {e}"
        if output_file:
            with open(output_file, "w") as f:
                json.dump(result, f, indent=2)
        return 1

    workspace = os.path.expanduser("~/rust_projects")
    os.makedirs(workspace, exist_ok=True)

    checks = [
        ("ver command", "ver"),
        ("help command", "help"),
        ("echo command", "echo smoke test ok"),
        ("pwd command", "pwd"),
        ("cls command", "cls"),
    ]

    all_passed = True
    for name, cmd in checks:
        try:
            cmd_result = router.execute(cmd, workspace)
            if cmd_result.success:
                record(name, True)
            else:
                record(name, False, "command returned error")
                all_passed = False
        except Exception as e:
            record(name, False, str(e))
            all_passed = False

    result["success"] = all_passed

    print()
    print("=" * 50)
    if all_passed:
        print("  SMOKE TEST PASSED - all checks OK")
    else:
        print("  SMOKE TEST FAILED")
    print("=" * 50)

    if output_file:
        try:
            with open(output_file, "w") as f:
                json.dump(result, f, indent=2)
        except Exception as e:
            print(f"[WARN] Could not write result file: {e}")

    return 0 if all_passed else 1


def main():
    """Application entry point."""
    parser = argparse.ArgumentParser(description="Rust Cargo DOS Commander")
    parser.add_argument("--smoke-test", action="store_true",
                        help="Run headless smoke test and exit")
    parser.add_argument("--smoke-output", type=str, default=None,
                        help="Path to write JSON smoke test result (use with --smoke-test)")
    parser.add_argument("--version", action="store_true",
                        help="Print version and exit")
    args = parser.parse_args()

    if args.version:
        import app
        print(f"Cargo Commander v{app.__version__}")
        return

    if args.smoke_test:
        sys.exit(run_smoke_test(output_file=args.smoke_output))

    from app.logger import logger
    from app.gui.main_window import MainWindow

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

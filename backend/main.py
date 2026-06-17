#!/usr/bin/env python3
"""
Rust Cargo DOS Commander
========================
A DOS-style terminal GUI for managing Rust/Cargo projects.
Supports project creation, building, running, and common DOS commands.

Usage:
    python main.py                  # Launch GUI
    python main.py --selftest       # Run self-test (no GUI required)
    python main.py --version        # Show version
    python main.py --check-imports  # Verify all imports work
"""
import sys
import os
import argparse
import tempfile

# Ensure app package is importable
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.logger import logger
import app


def run_selftest():
    """Run self-test suite without GUI. Returns exit code."""
    print("=" * 60)
    print(f"  Cargo Commander Self-Test v{app.__version__}")
    print("=" * 60)
    print()

    from app.commands.command_router import CommandRouter
    from app.commands.base import CommandResult, OutputType
    from app.commands.dos_commands import DosCommands
    from app.config import Theme, Window, App

    passed = 0
    failed = 0
    errors = []

    def check(name, fn):
        nonlocal passed, failed
        try:
            fn()
            passed += 1
            print(f"  [PASS] {name}")
        except Exception as e:
            failed += 1
            errors.append((name, str(e)))
            print(f"  [FAIL] {name}: {e}")

    # Test 1: Core imports
    def test_imports():
        _ = CommandRouter
        _ = CommandResult
        _ = DosCommands
        _ = Theme
    check("Core imports", test_imports)

    # Test 2: CommandRouter instantiation
    router = CommandRouter()
    def test_router_init():
        assert router is not None
    check("CommandRouter init", test_router_init)

    # Test 3: DOS commands - ver / help
    def test_dos_ver():
        result = router.execute("ver", os.getcwd())
        assert result.success
        assert len(result.lines) > 0
    check("DOS command: ver", test_dos_ver)

    def test_dos_help():
        result = router.execute("help", os.getcwd())
        assert result.success
        assert len(result.lines) > 0
    check("DOS command: help", test_dos_help)

    # Test 4: Directory operations
    test_dir = tempfile.mkdtemp(prefix="cargo_test_")
    def test_dos_mkdir():
        subdir = os.path.join(test_dir, "test_subdir")
        result = router.execute(f"mkdir test_subdir", test_dir)
        assert result.success
        assert os.path.isdir(subdir)
    check("DOS command: mkdir", test_dos_mkdir)

    def test_dos_cd():
        subdir = os.path.join(test_dir, "test_subdir")
        result = router.execute("cd test_subdir", test_dir)
        assert result.success
        assert result.new_cwd == subdir
    check("DOS command: cd", test_dos_cd)

    def test_dos_dir():
        result = router.execute("dir", test_dir)
        assert result.success
        assert len(result.lines) > 0
    check("DOS command: dir", test_dos_dir)

    def test_dos_echo():
        result = router.execute("echo hello world", test_dir)
        assert result.success
        found = any("hello world" in line for line, _ in result.lines)
        assert found
    check("DOS command: echo", test_dos_echo)

    def test_dos_type_cat():
        test_file = os.path.join(test_dir, "test.txt")
        with open(test_file, "w") as f:
            f.write("test content\n")
        result = router.execute("type test.txt", test_dir)
        assert result.success
        result2 = router.execute("cat test.txt", test_dir)
        assert result2.success
    check("DOS command: type/cat", test_dos_type_cat)

    # Test 5: Unknown command handling
    def test_unknown_cmd():
        result = router.execute("nonexistent_cmd", test_dir)
        assert not result.success
    check("Unknown command handling", test_unknown_cmd)

    # Test 6: Exit command
    def test_exit_cmd():
        result = router.execute("exit", test_dir)
        assert result.output == "__EXIT__"
    check("Exit command", test_exit_cmd)

    # Test 7: Theme / config accessible
    def test_config():
        from app.config import Theme, Window, App
        assert Theme.BG is not None
        assert Window.TITLE is not None
        assert App.DEFAULT_WORKSPACE is not None
    check("Config accessible", test_config)

    # Test 8: Logger works
    def test_logger():
        logger.info("selftest: logger check")
        assert logger is not None
    check("Logger functional", test_logger)

    # Summary
    print()
    print("=" * 60)
    print(f"  Results: {passed} passed, {failed} failed")
    print("=" * 60)

    if errors:
        print()
        print("Failures:")
        for name, err in errors:
            print(f"  - {name}: {err}")

    return 0 if failed == 0 else 1


def check_imports():
    """Verify all critical imports work. Returns exit code."""
    try:
        from app.commands.command_router import CommandRouter
        from app.commands.base import CommandResult, OutputType
        from app.commands.dos_commands import DosCommands
        from app.commands.cargo_executor import CargoExecutor
        from app.config import Theme, Window, App
        from app.logger import logger
        print(f"Cargo Commander v{app.__version__} - All imports OK")
        return 0
    except Exception as e:
        print(f"Import check FAILED: {e}", file=sys.stderr)
        return 1


def main():
    """Application entry point."""
    parser = argparse.ArgumentParser(description="Rust Cargo DOS Commander")
    parser.add_argument("--selftest", action="store_true",
                        help="Run self-test suite (no GUI required)")
    parser.add_argument("--version", action="store_true",
                        help="Show version and exit")
    parser.add_argument("--check-imports", action="store_true",
                        help="Verify all imports work and exit")
    args = parser.parse_args()

    if args.version:
        print(f"Cargo Commander v{app.__version__}")
        return 0

    if args.check_imports:
        return check_imports()

    if args.selftest:
        return run_selftest()

    # Normal GUI mode
    logger.info("=" * 60)
    logger.info("Rust Cargo DOS Commander starting...")
    logger.info("=" * 60)

    try:
        from app.gui.main_window import MainWindow
        window = MainWindow()
        window.run()
    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
    except Exception as e:
        logger.critical("Fatal error: %s", e, exc_info=True)
        print(f"\nFatal error: {e}", file=sys.stderr)
        sys.exit(1)

    logger.info("Application exited normally")
    return 0


if __name__ == "__main__":
    sys.exit(main())

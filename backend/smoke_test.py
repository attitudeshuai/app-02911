#!/usr/bin/env python3
"""
Headless smoke test script - no pytest dependency.
Used by CI and post-build validation to verify the app works.

Exit codes:
  0 - all checks passed
  1 - one or more checks failed

Usage:
    python smoke_test.py
    python smoke_test.py --verbose
"""
import sys
import os
import argparse
import tempfile
import shutil


def run_check(name, func):
    """Run a check and return (passed, message)."""
    try:
        result = func()
        if result is True or result is None:
            return True, "PASS"
        return False, f"FAIL: {result}"
    except Exception as e:
        return False, f"ERROR: {e}"


def check_import_app():
    import app
    assert hasattr(app, "__version__"), "Missing __version__"
    return True


def check_import_command_modules():
    from app.commands.base import CommandResult, OutputType
    from app.commands.dos_commands import DosCommands
    from app.commands.cargo_executor import CargoExecutor
    from app.commands.command_router import CommandRouter
    return True


def check_import_config():
    from app.config import Theme, Window, App
    assert Theme.BG is not None
    assert Window.TITLE is not None
    return True


def check_router_basic():
    from app.commands.command_router import CommandRouter
    router = CommandRouter()
    assert router is not None
    return True


def check_ver_command():
    from app.commands.command_router import CommandRouter
    router = CommandRouter()
    result = router.execute("ver", os.getcwd())
    assert result.success is True
    assert len(result.lines) > 0
    return True


def check_help_command():
    from app.commands.command_router import CommandRouter
    router = CommandRouter()
    result = router.execute("help", os.getcwd())
    assert result.success is True
    assert len(result.lines) > 5
    return True


def check_dir_command():
    from app.commands.command_router import CommandRouter
    tmpdir = tempfile.mkdtemp(prefix="smoke_test_")
    try:
        test_file = os.path.join(tmpdir, "test.txt")
        with open(test_file, "w") as f:
            f.write("test")
        router = CommandRouter()
        result = router.execute("dir", tmpdir)
        assert result.success is True
        texts = [line[0] for line in result.lines]
        assert any("test.txt" in t for t in texts), "File not found in dir output"
        return True
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def check_mkdir_cd_rmdir():
    from app.commands.command_router import CommandRouter
    tmpdir = tempfile.mkdtemp(prefix="smoke_test_")
    try:
        router = CommandRouter()

        result = router.execute("mkdir subdir", tmpdir)
        assert result.success is True, "mkdir failed"
        assert os.path.isdir(os.path.join(tmpdir, "subdir")), "dir not created"

        result = router.execute("cd subdir", tmpdir)
        assert result.success is True, "cd failed"
        assert result.new_cwd is not None, "cd did not return new_cwd"

        result = router.execute("cd ..", result.new_cwd)
        assert result.success is True, "cd .. failed"

        result = router.execute("rd subdir", tmpdir)
        assert result.success is True, "rmdir failed"
        assert not os.path.isdir(os.path.join(tmpdir, "subdir")), "dir not removed"
        return True
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def check_unknown_command_handling():
    from app.commands.command_router import CommandRouter
    router = CommandRouter()
    result = router.execute("this_command_does_not_exist_xyz", os.getcwd())
    assert result.success is False, "Unknown command should fail"
    return True


def main():
    parser = argparse.ArgumentParser(description="Headless smoke test for Cargo Commander")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show detailed output")
    args = parser.parse_args()

    checks = [
        ("Import app package", check_import_app),
        ("Import command modules", check_import_command_modules),
        ("Import config module", check_import_config),
        ("Create CommandRouter", check_router_basic),
        ("Execute 'ver' command", check_ver_command),
        ("Execute 'help' command", check_help_command),
        ("Execute 'dir' command", check_dir_command),
        ("mkdir + cd + rmdir sequence", check_mkdir_cd_rmdir),
        ("Unknown command handling", check_unknown_command_handling),
    ]

    print("=" * 60)
    print("  Cargo Commander - Headless Smoke Test")
    print("=" * 60)
    print()

    passed = 0
    failed = 0

    for name, func in checks:
        ok, msg = run_check(name, func)
        status = "✓ PASS" if ok else "✗ FAIL"
        print(f"  [{status}] {name}")
        if args.verbose and not ok:
            print(f"         {msg}")
        if ok:
            passed += 1
        else:
            failed += 1

    print()
    print("-" * 60)
    print(f"  Results: {passed} passed, {failed} failed, {len(checks)} total")
    print("=" * 60)

    if failed > 0:
        print("\nSmoke test FAILED")
        return 1
    else:
        print("\nSmoke test PASSED ✓")
        return 0


if __name__ == "__main__":
    sys.exit(main())

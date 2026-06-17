"""
Pre-commit check runner - cross-platform (Windows / macOS / Linux)
Runs import check, self-test, and unit tests before commit.

Usage:
    python scripts/precommit_checks.py [--skip-imports] [--skip-selftest] [--skip-unit]
"""
import sys
import os
import subprocess
import argparse

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
BACKEND_DIR = os.path.join(PROJECT_ROOT, "backend")


def run_check(name, cmd_args, cwd=None):
    """Run a check command and return (passed, output)."""
    work_dir = cwd or BACKEND_DIR
    print(f"\n[{name}] Running...")
    try:
        result = subprocess.run(
            cmd_args,
            cwd=work_dir,
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            print(f"[{name}] PASS")
            return True, result.stdout
        else:
            print(f"[{name}] FAIL (exit code {result.returncode})")
            if result.stdout:
                print("--- stdout ---")
                print(result.stdout)
            if result.stderr:
                print("--- stderr ---")
                print(result.stderr)
            return False, result.stderr or result.stdout
    except FileNotFoundError as e:
        print(f"[{name}] FAIL - command not found: {e}")
        return False, str(e)
    except Exception as e:
        print(f"[{name}] FAIL - error: {e}")
        return False, str(e)


def find_python():
    """Find the Python executable."""
    for cmd in ["python", "python3"]:
        try:
            subprocess.run([cmd, "--version"], capture_output=True, check=True)
            return cmd
        except (FileNotFoundError, subprocess.CalledProcessError):
            continue
    return None


def main():
    parser = argparse.ArgumentParser(description="Pre-commit checks")
    parser.add_argument("--skip-imports", action="store_true", help="Skip import check")
    parser.add_argument("--skip-selftest", action="store_true", help="Skip self-test")
    parser.add_argument("--skip-unit", action="store_true", help="Skip unit tests")
    args = parser.parse_args()

    python_cmd = find_python()
    if not python_cmd:
        print("ERROR: Python not found")
        return 1

    print("=" * 50)
    print("  Pre-commit Checks")
    print(f"  Python: {python_cmd}")
    print("=" * 50)

    passed = 0
    failed = 0

    # 1. Import check
    if not args.skip_imports:
        ok, _ = run_check("imports", [python_cmd, "main.py", "--check-imports"])
        if ok:
            passed += 1
        else:
            failed += 1

    # 2. Self-test
    if not args.skip_selftest:
        ok, _ = run_check("selftest", [python_cmd, "main.py", "--selftest"])
        if ok:
            passed += 1
        else:
            failed += 1

    # 3. Unit tests (only if pytest available)
    if not args.skip_unit:
        has_pytest = subprocess.run(
            [python_cmd, "-m", "pytest", "--version"],
            capture_output=True,
        ).returncode == 0
        if has_pytest:
            ok, _ = run_check("unit tests", [python_cmd, "-m", "pytest", "tests/test_commands.py", "-q"])
            if ok:
                passed += 1
            else:
                failed += 1
        else:
            print("\n[unit tests] SKIP (pytest not installed)")

    # Summary
    print("\n" + "=" * 50)
    print(f"  Results: {passed} passed, {failed} failed")
    print("=" * 50)

    if failed > 0:
        print("\nCommit blocked: fix the issues above first.")
        print("Tip: You can skip with git commit --no-verify")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())

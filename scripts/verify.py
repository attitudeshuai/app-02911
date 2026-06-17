#!/usr/bin/env python3
"""
Local one-click quality gate.

Runs exactly what CI runs, so "green locally" means "green in CI":
  1. ruff lint
  2. ruff format --check
  3. headless + cargo-mocked tests  (no display, no real Rust)
  4. GUI smoke launch (--smoke)     (skipped if no display)

Usage:
    python scripts/verify.py            # full gate
    python scripts/verify.py --no-gui   # skip the GUI smoke step
"""
import argparse
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND = os.path.join(ROOT, "backend")


def run(label, cmd, cwd=ROOT, env=None, allow_nonzero=False):
    print(f"\n=== {label} ===")
    print("$ " + " ".join(cmd))
    result = subprocess.run(cmd, cwd=cwd, env=env)
    if result.returncode != 0 and not allow_nonzero:
        print(f"\n[FAIL] {label} exited {result.returncode}")
        return False
    return True


def has_display():
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


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-gui", action="store_true", help="skip GUI smoke step")
    args = parser.parse_args()

    py = sys.executable
    ok = True

    ok &= run("ruff lint", [py, "-m", "ruff", "check", "backend"])
    ok &= run("ruff format --check", [py, "-m", "ruff", "format", "--check", "backend"])
    ok &= run(
        "headless tests",
        [py, "-m", "pytest", "-q", "-m", "not gui and not cargo", "backend/tests"],
    )

    if not args.no_gui:
        if not has_display():
            print("\n=== GUI smoke ===\n[SKIP] no display available")
        else:
            ok &= run(
                "GUI smoke launch",
                [py, "main.py", "--smoke"],
                cwd=BACKEND,
            )

    print("\n" + "=" * 40)
    if ok:
        print("ALL CHECKS PASSED")
        return 0
    print("SOME CHECKS FAILED")
    return 1


if __name__ == "__main__":
    sys.exit(main())

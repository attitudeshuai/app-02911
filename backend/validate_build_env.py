#!/usr/bin/env python3
"""
Build environment validator.
Checks that Python, Tcl/Tk, and all build dependencies match locked versions.

Exit codes:
  0 - all versions match
  1 - one or more version mismatches

Usage:
    python validate_build_env.py
    python validate_build_env.py --strict   # fail on any mismatch
    python validate_build_env.py --quiet    # only output on error
"""
import sys
import os
import argparse
import platform


EXPECTED = {
    "python_major_minor": "3.12",
    "python_patch": "10",
    "pyinstaller": "6.11.1",
    "pillow": "10.4.0",
    "tcltk_major_minor": "8.6",
}


class CheckResult:
    def __init__(self, name, actual, expected, status, detail=""):
        self.name = name
        self.actual = actual
        self.expected = expected
        self.status = status  # "ok", "warn", "fail"
        self.detail = detail


def check_python_version():
    actual = platform.python_version()
    expected_major_minor = EXPECTED["python_major_minor"]
    expected_patch = EXPECTED["python_patch"]

    actual_major_minor = ".".join(actual.split(".")[:2])

    if actual_major_minor != expected_major_minor:
        return CheckResult(
            "Python", actual, f"{expected_major_minor}.x",
            "fail", "Major/minor version mismatch"
        )
    elif actual.split(".")[2] != expected_patch:
        return CheckResult(
            "Python", actual, f"{expected_major_minor}.{expected_patch}",
            "warn", "Patch version differs (may work but untested)"
        )
    return CheckResult("Python", actual, f"{expected_major_minor}.{expected_patch}", "ok")


def check_tcltk_version():
    try:
        import tkinter
        tcl = tkinter.Tcl()
        patchlevel = tcl.eval("info patchlevel")
        actual = patchlevel
        expected_major_minor = EXPECTED["tcltk_major_minor"]
        actual_major_minor = ".".join(actual.split(".")[:2])

        if actual_major_minor != expected_major_minor:
            return CheckResult(
                "Tcl/Tk", actual, f"{expected_major_minor}.x",
                "fail", "Major/minor version mismatch - GUI may break"
            )
        return CheckResult("Tcl/Tk", actual, f"{expected_major_minor}.x", "ok")
    except ImportError:
        return CheckResult("Tcl/Tk", "NOT FOUND", f"{EXPECTED['tcltk_major_minor']}.x", "fail", "tkinter not available")


def check_pyinstaller():
    try:
        import PyInstaller
        actual = PyInstaller.__version__
        expected = EXPECTED["pyinstaller"]
        status = "ok" if actual == expected else "warn"
        return CheckResult("PyInstaller", actual, expected, status)
    except ImportError:
        return CheckResult("PyInstaller", "NOT INSTALLED", EXPECTED["pyinstaller"], "fail")


def check_pillow():
    try:
        from PIL import __version__ as pillow_version
        actual = pillow_version
        expected = EXPECTED["pillow"]
        status = "ok" if actual == expected else "warn"
        return CheckResult("Pillow", actual, expected, status)
    except ImportError:
        return CheckResult("Pillow", "NOT INSTALLED", EXPECTED["pillow"], "warn")


def main():
    parser = argparse.ArgumentParser(description="Validate build environment versions")
    parser.add_argument("--strict", action="store_true", help="Fail on warnings too")
    parser.add_argument("--quiet", action="store_true", help="Only output on errors")
    args = parser.parse_args()

    checks = [
        check_python_version(),
        check_tcltk_version(),
        check_pyinstaller(),
        check_pillow(),
    ]

    if not args.quiet:
        print("=" * 60)
        print("  Build Environment Validation")
        print("=" * 60)
        print()
        print(f"  {'Component':<14} {'Status':<6} {'Actual':<14} {'Expected'}")
        print(f"  {'-'*13}  {'-'*5}  {'-'*12}  {'-'*20}")

    errors = 0
    warnings = 0

    for c in checks:
        if c.status == "ok":
            icon = "✓"
        elif c.status == "warn":
            icon = "△"
            warnings += 1
        else:
            icon = "✗"
            errors += 1

        if not args.quiet:
            print(f"  {c.name:<14} [{icon}]   {c.actual:<14} {c.expected}")
            if c.detail and c.status != "ok":
                print(f"               {c.detail}")

    if not args.quiet:
        print()
        print("-" * 60)

    if errors > 0:
        if not args.quiet:
            print(f"  Result: {errors} error(s), {warnings} warning(s) - FAIL")
            print()
            print("  Please install correct versions before building:")
            print("  pip install -r build-requirements.txt")
        return 1
    elif warnings > 0 and args.strict:
        if not args.quiet:
            print(f"  Result: {errors} error(s), {warnings} warning(s) - FAIL (strict mode)")
        return 1
    else:
        if not args.quiet:
            print(f"  Result: {errors} error(s), {warnings} warning(s) - PASS")
        return 0


if __name__ == "__main__":
    sys.exit(main())

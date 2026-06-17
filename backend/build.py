#!/usr/bin/env python3
"""
Build script for Rust Cargo DOS Commander.
Supports Windows, macOS, and Linux.

Usage:
    python build.py            # Build for current platform
    python build.py --clean    # Clean build artifacts first
"""
import os
import sys
import shutil
import subprocess
import argparse
import platform


def get_platform_name():
    system = platform.system().lower()
    machine = platform.machine().lower()
    if system == "darwin":
        system = "macos"
    if machine in ("amd64", "x86_64"):
        arch = "x64"
    elif machine in ("arm64", "aarch64"):
        arch = "arm64"
    else:
        arch = machine
    return f"{system}-{arch}"


def clean_build():
    dirs_to_remove = ["build", "dist"]
    for d in dirs_to_remove:
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), d)
        if os.path.isdir(path):
            print(f"Removing {d}/")
            shutil.rmtree(path)
    spec_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "CargoCommander.spec")
    if os.path.isfile(spec_file):
        os.remove(spec_file)


def main():
    parser = argparse.ArgumentParser(description="Build Cargo Commander")
    parser.add_argument("--clean", action="store_true", help="Clean build artifacts first")
    parser.add_argument("--name", default="CargoCommander", help="App name")
    args = parser.parse_args()

    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)

    if args.clean:
        clean_build()

    print("=" * 60)
    print(f"  Building Cargo Commander for {get_platform_name()}")
    print("=" * 60)

    try:
        import PyInstaller
    except ImportError:
        print("PyInstaller not found. Installing...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])

    print("\n[1/3] Running smoke test before build...")
    result = subprocess.run([sys.executable, "main.py", "--check"])
    if result.returncode != 0:
        print("\nERROR: Smoke test failed! Aborting build.")
        sys.exit(1)
    print("Smoke test passed.\n")

    print("[2/3] Running unit tests...")
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/", "-v", "--tb=short"],
        cwd=script_dir
    )
    if result.returncode != 0:
        print("\nWARNING: Some tests failed. Continuing build anyway...\n")
    else:
        print("All tests passed.\n")

    print("[3/3] Running PyInstaller...")
    spec_file = "cargo_commander.spec"
    if not os.path.isfile(spec_file):
        print(f"Spec file {spec_file} not found!")
        sys.exit(1)

    cmd = [sys.executable, "-m", "PyInstaller", spec_file, "--clean", "--noconfirm"]
    subprocess.check_call(cmd)

    dist_dir = os.path.join(script_dir, "dist")
    platform_name = get_platform_name()

    print()
    print("=" * 60)
    print(f"  Build complete!")
    print(f"  Output: {dist_dir}")
    print(f"  Platform: {platform_name}")
    print("=" * 60)

    print("\nNext steps:")
    print(f"  1. Test the built executable in dist/")
    print(f"  2. Package for distribution")


if __name__ == "__main__":
    main()

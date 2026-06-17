"""
L2 GUI smoke test.

Launches the real application with `--smoke`, which builds the MainWindow and
auto-closes after 800ms. This is the automated replacement for "manually start
the app once". Requires a display, so it is marked `gui` and skipped on
headless machines (use `xvfb-run` on Linux).
"""

import os
import subprocess
import sys

import pytest

BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


@pytest.mark.gui
def test_app_launches_and_closes_smoke(has_display):
    if not has_display:
        pytest.skip("no display available (set DISPLAY or run under xvfb-run)")

    proc = subprocess.run(
        [sys.executable, "main.py", "--smoke"],
        cwd=BACKEND_DIR,
        capture_output=True,
        text=True,
        timeout=30,
    )

    assert (
        proc.returncode == 0
    ), f"smoke run exited {proc.returncode}\nstdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"

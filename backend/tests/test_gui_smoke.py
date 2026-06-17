"""
GUI smoke test - verifies the GUI can start and basic widgets exist.
Requires xvfb on Linux, or native display on macOS/Windows.
Can run headless with: xvfb-run python test_gui_smoke.py
"""
import os
import sys
import time
import tempfile
import threading

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_gui_imports():
    """Verify all GUI modules can be imported."""
    from app.gui.main_window import MainWindow
    from app.gui.toolbar import Toolbar
    from app.gui.statusbar import StatusBar
    from app.gui.tab_terminal import TabTerminalManager
    from app.gui.dialogs import NewProjectDialog
    from app.gui.syntax_highlight import SyntaxHighlighter
    from app.config import Theme, Window, App
    print("  [PASS] All GUI modules imported successfully")


def test_gui_startup():
    """Test that MainWindow can be created and destroyed without errors."""
    import tkinter as tk
    from app.gui.main_window import MainWindow

    root = tk.Tk()
    root.withdraw()

    try:
        window = MainWindow()
        assert window is not None
        assert window._root is not None
        assert window._router is not None
        assert window._tab_manager is not None
        assert window._toolbar is not None
        assert window._statusbar is not None
        print("  [PASS] MainWindow created successfully")

        window._root.update_idletasks()
        window._root.update()
        print("  [PASS] Main window event loop processed")

        window._root.destroy()
        print("  [PASS] MainWindow destroyed cleanly")
    except Exception as e:
        root.destroy()
        raise e


def test_command_integration():
    """Test that commands work through the full GUI stack."""
    import tkinter as tk
    from app.gui.main_window import MainWindow

    test_dir = tempfile.mkdtemp(prefix="cargo_gui_test_")

    root = tk.Tk()
    root.withdraw()

    try:
        window = MainWindow()
        window._cwd = test_dir

        result = window._router.execute("ver", test_dir)
        assert result.success
        print("  [PASS] Command router works from GUI context")

        result = window._router.execute("mkdir test_gui_dir", test_dir)
        assert result.success
        assert os.path.isdir(os.path.join(test_dir, "test_gui_dir"))
        print("  [PASS] Directory operations work from GUI context")

        window._root.destroy()
    except Exception as e:
        root.destroy()
        raise e


def main():
    print("=" * 60)
    print("  Cargo Commander GUI Smoke Test")
    print("=" * 60)
    print()

    tests = [
        ("GUI imports", test_gui_imports),
        ("GUI startup/shutdown", test_gui_startup),
        ("Command integration", test_command_integration),
    ]

    passed = 0
    failed = 0
    errors = []

    for name, test_fn in tests:
        try:
            test_fn()
            passed += 1
        except Exception as e:
            failed += 1
            errors.append((name, str(e)))
            print(f"  [FAIL] {name}: {e}")

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


if __name__ == "__main__":
    sys.exit(main())

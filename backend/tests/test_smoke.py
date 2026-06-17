"""
Smoke tests - verify the application can start and basic functionality works.
All tests run headless (no GUI required).
"""
import os
import sys
import importlib
import pytest


class TestModuleImports:
    """Verify all core modules can be imported without GUI."""

    def test_import_app(self):
        import app
        assert hasattr(app, "__version__")

    def test_import_config(self):
        from app.config import Theme, Window, App
        assert Theme.BG is not None
        assert Window.TITLE is not None
        assert App.DEFAULT_WORKSPACE is not None

    def test_import_logger(self):
        from app.logger import logger
        assert logger is not None

    def test_import_command_base(self):
        from app.commands.base import CommandResult, OutputType
        assert CommandResult is not None
        assert OutputType.NORMAL is not None

    def test_import_dos_commands(self):
        from app.commands.dos_commands import DosCommands
        assert DosCommands.cmd_dir is not None

    def test_import_cargo_executor(self):
        from app.commands.cargo_executor import CargoExecutor
        assert CargoExecutor is not None

    def test_import_command_router(self):
        from app.commands.command_router import CommandRouter
        assert CommandRouter is not None


class TestCoreSmoke:
    """Core functionality smoke tests - exercise the main command flows."""

    def test_router_creation(self, router):
        assert router is not None
        assert router.cargo is not None

    def test_basic_command_pipeline(self, router, temp_workspace):
        result = router.execute("ver", temp_workspace)
        assert result.success is True

        result = router.execute("help", temp_workspace)
        assert result.success is True
        assert len(result.lines) > 5

        result = router.execute("mkdir smoke_test_dir", temp_workspace)
        assert result.success is True

        result = router.execute("cd smoke_test_dir", temp_workspace)
        assert result.success is True
        assert result.new_cwd is not None

        result = router.execute("pwd", temp_workspace)
        assert result.success is True

    def test_multiple_commands_sequence(self, router, temp_workspace):
        steps = [
            ("mkdir proj", True),
            ("cd proj", True),
            ("echo hello world", True),
            ("dir", True),
            ("cd ..", True),
            ("rd proj", True),
        ]
        cwd = temp_workspace
        for cmd, should_succeed in steps:
            result = router.execute(cmd, cwd)
            assert result.success == should_succeed, f"Command '{cmd}' failed"
            if result.new_cwd:
                cwd = result.new_cwd

    def test_error_handling_smoke(self, router, temp_workspace):
        result = router.execute("cd nonexistent_dir_xyz", temp_workspace)
        assert result.success is False

        result = router.execute("type nonexistent_file.txt", temp_workspace)
        assert result.success is False

        result = router.execute("del nonexistent_file.txt", temp_workspace)
        assert result.success is False


class TestHeadlessStartup:
    """Verify the app can start in headless mode (import + init without Tk)."""

    def test_headless_startup_script(self):
        """Simulate a headless startup check - what CI would run."""
        code = """
import sys
import os

import app
from app.commands.command_router import CommandRouter
from app.commands.base import CommandResult

print(f"Version: {app.__version__}")

router = CommandRouter()
result = router.execute("ver", os.getcwd())
assert result.success, "ver command failed"
print("Startup OK - all core modules loaded")
print("Smoke test PASSED")
"""
        import subprocess
        backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        env = os.environ.copy()
        env["PYTHONPATH"] = backend_dir
        result = subprocess.run(
            [sys.executable, "-c", code],
            cwd=backend_dir,
            env=env,
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0, f"Smoke test failed: {result.stderr}"
        assert "Smoke test PASSED" in result.stdout

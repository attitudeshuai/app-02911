"""
Cargo command executor.
Handles all Rust Cargo subcommands with real subprocess execution
and streaming output support.
"""

import os
import shutil
import subprocess
import threading
from collections.abc import Callable

from app.commands.base import CommandResult, OutputType
from app.config import App
from app.logger import logger


class CargoExecutor:
    """Executes Cargo commands as subprocesses with real-time output streaming."""

    def __init__(self):
        self._current_process: subprocess.Popen | None = None
        self._cancelled = False

    @staticmethod
    def _get_cargo_path() -> str:
        """Get the path to the cargo executable."""
        if shutil.which("cargo"):
            return "cargo"
        # Fall back to standard rustup installation path
        return os.path.expanduser("~/.cargo/bin/cargo")

    @property
    def is_running(self) -> bool:
        return self._current_process is not None and self._current_process.poll() is None

    def cancel(self):
        """Cancel the currently running process."""
        self._cancelled = True
        if self._current_process and self._current_process.poll() is None:
            try:
                self._current_process.terminate()
                self._current_process.wait(timeout=5)
                logger.info("Cargo process terminated by user")
            except subprocess.TimeoutExpired:
                self._current_process.kill()
                logger.warning("Cargo process killed after timeout")

    @staticmethod
    def check_cargo_installed() -> bool:
        """Verify cargo is available on the system."""
        if shutil.which("cargo") is not None:
            return True
        # Check standard rustup installation path
        cargo_path = os.path.expanduser("~/.cargo/bin/cargo")
        return os.path.isfile(cargo_path) and os.access(cargo_path, os.X_OK)

    @classmethod
    def get_cargo_version(cls) -> str:
        """Get installed cargo version string."""
        try:
            result = subprocess.run(
                [cls._get_cargo_path(), "--version"], capture_output=True, text=True, timeout=10
            )
            return result.stdout.strip() if result.returncode == 0 else "unknown"
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return "not installed"

    @staticmethod
    def _get_rustc_path() -> str:
        """Get the path to the rustc executable."""
        if shutil.which("rustc"):
            return "rustc"
        return os.path.expanduser("~/.cargo/bin/rustc")

    @classmethod
    def get_rustc_version(cls) -> str:
        """Get installed rustc version string."""
        try:
            result = subprocess.run(
                [cls._get_rustc_path(), "--version"], capture_output=True, text=True, timeout=10
            )
            return result.stdout.strip() if result.returncode == 0 else "unknown"
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return "not installed"

    def execute_sync(self, args: list, cwd: str) -> CommandResult:
        """Execute a cargo command synchronously and return the result."""
        result = CommandResult()

        if not self.check_cargo_installed():
            result.add_error("'cargo' is not recognized as an internal or external command.")
            result.add_error("")
            result.add_info("Rust is not installed. Install from: https://rustup.rs/")
            return result

        if not args:
            result.add_error("Usage: CARGO <subcommand> [options]")
            result.add_line("")
            result.add_info("Available subcommands:")
            for cmd in App.CARGO_COMMANDS:
                result.add_line(f"  cargo {cmd}")
            return result

        subcommand = args[0]
        cmd_args = args[1:]
        cargo_path = self._get_cargo_path()
        full_cmd = [cargo_path, subcommand] + cmd_args

        logger.info("Executing: %s in %s", " ".join(full_cmd), cwd)
        result.add_system(f"Executing: cargo {subcommand} {' '.join(cmd_args)}".strip())
        result.add_line("")

        try:
            proc = subprocess.run(
                full_cmd,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=App.COMMAND_TIMEOUT,
                env={**os.environ, "CARGO_TERM_COLOR": "never"},
            )

            if proc.stdout:
                for line in proc.stdout.splitlines():
                    if line.strip().startswith("Compiling"):
                        result.add_info(line)
                    elif line.strip().startswith("Finished"):
                        result.add_success(line)
                    elif line.strip().startswith("Running"):
                        result.add_info(line)
                    elif line.strip().startswith("Created"):
                        result.add_success(line)
                    elif line.strip().startswith("warning"):
                        result.add_warning(line)
                    else:
                        result.add_line(line)

            if proc.stderr:
                for line in proc.stderr.splitlines():
                    if "warning" in line.lower():
                        result.add_warning(line)
                    elif "error" in line.lower():
                        result.add_error(line)
                    elif line.strip().startswith("Compiling"):
                        result.add_info(line)
                    elif line.strip().startswith("Finished"):
                        result.add_success(line)
                    elif line.strip().startswith("Downloading"):
                        result.add_info(line)
                    else:
                        result.add_line(line)

            if proc.returncode == 0:
                result.add_line("")
                result.add_success("Process finished with exit code 0")
            else:
                result.add_line("")
                result.add_error(f"Process finished with exit code {proc.returncode}")
                result.success = False

            logger.info("Cargo command completed: exit code %d", proc.returncode)

        except subprocess.TimeoutExpired:
            result.add_error(f"Command timed out after {App.COMMAND_TIMEOUT} seconds.")
            result.success = False
            logger.error("Cargo command timed out: %s", " ".join(full_cmd))
        except FileNotFoundError:
            result.add_error("'cargo' executable not found in PATH.")
            result.success = False
        except OSError as e:
            result.add_error(f"Failed to execute command: {e}")
            result.success = False
            logger.error("Cargo execution error: %s", e)

        return result

    def execute_async(
        self,
        args: list,
        cwd: str,
        on_output: Callable[[str, OutputType], None],
        on_complete: Callable[[int], None],
    ):
        """Execute a cargo command asynchronously with streaming output."""
        self._cancelled = False

        if not self.check_cargo_installed():
            on_output(
                "'cargo' is not recognized as an internal or external command.\n", OutputType.ERROR
            )
            on_output("Rust is not installed. Install from: https://rustup.rs/\n", OutputType.INFO)
            on_complete(-1)
            return

        cargo_path = self._get_cargo_path()
        full_cmd = [cargo_path] + args

        def _run():
            try:
                logger.info("Async executing: %s in %s", " ".join(full_cmd), cwd)
                on_output(f"Executing: cargo {' '.join(args)}\n", OutputType.SYSTEM)

                self._current_process = subprocess.Popen(
                    full_cmd,
                    cwd=cwd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                    env={**os.environ, "CARGO_TERM_COLOR": "never"},
                )

                for line in iter(self._current_process.stdout.readline, ""):
                    if self._cancelled:
                        break
                    stripped = line.rstrip()
                    if "error" in stripped.lower():
                        on_output(line, OutputType.ERROR)
                    elif "warning" in stripped.lower():
                        on_output(line, OutputType.WARNING)
                    elif stripped.startswith(("Compiling", "Downloading", "Running")):
                        on_output(line, OutputType.INFO)
                    elif stripped.startswith(("Finished", "Created")):
                        on_output(line, OutputType.SUCCESS)
                    else:
                        on_output(line, OutputType.NORMAL)

                self._current_process.wait()
                exit_code = self._current_process.returncode

                if self._cancelled:
                    on_output("\nProcess cancelled by user.\n", OutputType.WARNING)
                    on_complete(-1)
                elif exit_code == 0:
                    on_output("\nProcess finished with exit code 0\n", OutputType.SUCCESS)
                    on_complete(0)
                else:
                    on_output(f"\nProcess finished with exit code {exit_code}\n", OutputType.ERROR)
                    on_complete(exit_code)

                logger.info(
                    "Async cargo command completed: exit code %s",
                    "cancelled" if self._cancelled else exit_code,
                )

            except Exception as e:
                on_output(f"\nExecution error: {e}\n", OutputType.ERROR)
                on_complete(-1)
                logger.error("Async cargo execution error: %s", e)
            finally:
                self._current_process = None

        thread = threading.Thread(target=_run, daemon=True)
        thread.start()

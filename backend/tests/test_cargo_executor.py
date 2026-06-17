"""
L1 tests for CargoExecutor.

These do NOT require a real Rust toolchain. We monkeypatch shutil.which /
subprocess.run to drive the branches (cargo missing, cargo present, version
queries, output colouring).
"""

import subprocess

from app.commands.cargo_executor import CargoExecutor


def _text(result) -> str:
    return "\n".join(line for line, _ in result.lines).lower()


def test_check_cargo_installed_false(monkeypatch):
    monkeypatch.setattr("app.commands.cargo_executor.shutil.which", lambda _: None)
    monkeypatch.setattr("os.path.isfile", lambda p: False)
    assert CargoExecutor.check_cargo_installed() is False


def test_check_cargo_installed_true(monkeypatch):
    monkeypatch.setattr("app.commands.cargo_executor.shutil.which", lambda _: "/usr/bin/cargo")
    assert CargoExecutor.check_cargo_installed() is True


def test_execute_sync_without_cargo(monkeypatch):
    monkeypatch.setattr("app.commands.cargo_executor.shutil.which", lambda _: None)
    monkeypatch.setattr("os.path.isfile", lambda p: False)

    result = CargoExecutor().execute_sync(["build"], "/tmp")

    assert not result.success
    assert "not recognized" in _text(result)
    assert "rustup.rs" in _text(result)


def test_execute_sync_no_args_lists_subcommands(monkeypatch):
    monkeypatch.setattr("app.commands.cargo_executor.shutil.which", lambda _: "/usr/bin/cargo")

    result = CargoExecutor().execute_sync([], "/tmp")

    assert "usage" in _text(result)
    assert "cargo new" in _text(result)
    assert "cargo build" in _text(result)


def test_execute_sync_success(monkeypatch, tmp_path):
    monkeypatch.setattr("app.commands.cargo_executor.shutil.which", lambda _: "/usr/bin/cargo")
    monkeypatch.setattr(CargoExecutor, "_get_cargo_path", staticmethod(lambda: "/usr/bin/cargo"))

    class _FakeProc:
        returncode = 0
        stdout = "Compiling demo\nFinished release\n"
        stderr = ""

    monkeypatch.setattr(
        "app.commands.cargo_executor.subprocess.run",
        lambda *a, **k: _FakeProc(),
    )

    result = CargoExecutor().execute_sync(["build"], str(tmp_path))

    assert result.success
    text = _text(result)
    assert "compiling" in text
    assert "finished" in text
    assert "exit code 0" in text


def test_execute_sync_failure(monkeypatch, tmp_path):
    monkeypatch.setattr("app.commands.cargo_executor.shutil.which", lambda _: "/usr/bin/cargo")
    monkeypatch.setattr(CargoExecutor, "_get_cargo_path", staticmethod(lambda: "/usr/bin/cargo"))

    class _FakeProc:
        returncode = 101
        stdout = ""
        stderr = "error[E0599]: method not found\n"

    monkeypatch.setattr(
        "app.commands.cargo_executor.subprocess.run",
        lambda *a, **k: _FakeProc(),
    )

    result = CargoExecutor().execute_sync(["build"], str(tmp_path))

    assert not result.success
    assert "error" in _text(result)
    assert "exit code 101" in _text(result)


def test_get_cargo_version(monkeypatch):
    monkeypatch.setattr(CargoExecutor, "_get_cargo_path", staticmethod(lambda: "/usr/bin/cargo"))

    class _FakeProc:
        returncode = 0
        stdout = "cargo 1.80.0 (f9d6d2 2024-08-07)\n"

    monkeypatch.setattr(
        "app.commands.cargo_executor.subprocess.run",
        lambda *a, **k: _FakeProc(),
    )

    assert CargoExecutor.get_cargo_version() == "cargo 1.80.0 (f9d6d2 2024-08-07)"


def test_get_cargo_version_missing(monkeypatch):
    monkeypatch.setattr(CargoExecutor, "_get_cargo_path", staticmethod(lambda: "/usr/bin/cargo"))

    def _raise(*a, **k):
        raise FileNotFoundError

    monkeypatch.setattr("app.commands.cargo_executor.subprocess.run", _raise)

    assert CargoExecutor.get_cargo_version() == "not installed"


def test_execute_sync_timeout(monkeypatch, tmp_path):
    monkeypatch.setattr("app.commands.cargo_executor.shutil.which", lambda _: "/usr/bin/cargo")
    monkeypatch.setattr(CargoExecutor, "_get_cargo_path", staticmethod(lambda: "/usr/bin/cargo"))

    def _raise(*a, **k):
        raise subprocess.TimeoutExpired(cmd="cargo", timeout=120)

    monkeypatch.setattr("app.commands.cargo_executor.subprocess.run", _raise)

    result = CargoExecutor().execute_sync(["build"], str(tmp_path))

    assert not result.success
    assert "timed out" in _text(result)

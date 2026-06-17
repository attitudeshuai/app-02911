import os
import tempfile
import pytest
from app.commands.cargo_executor import CargoExecutor


@pytest.fixture
def executor():
    return CargoExecutor()


@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


class TestCargoChecks:
    def test_check_cargo_installed_returns_bool(self, executor):
        result = CargoExecutor.check_cargo_installed()
        assert isinstance(result, bool)

    def test_get_cargo_version_returns_string(self, executor):
        result = CargoExecutor.get_cargo_version()
        assert isinstance(result, str)
        assert len(result) > 0

    def test_get_rustc_version_returns_string(self, executor):
        result = CargoExecutor.get_rustc_version()
        assert isinstance(result, str)
        assert len(result) > 0

    def test_get_cargo_path(self, executor):
        path = CargoExecutor._get_cargo_path()
        assert isinstance(path, str)
        assert len(path) > 0

    def test_is_running_initially_false(self, executor):
        assert executor.is_running is False


@pytest.mark.skipif(
    not CargoExecutor.check_cargo_installed(),
    reason="Cargo not installed on this system"
)
class TestCargoExecuteSync:
    def test_cargo_no_args(self, executor, temp_dir):
        result = executor.execute_sync([], temp_dir)
        assert result.success is False
        full_text = "\n".join(line[0] for line in result.lines)
        assert "Usage" in full_text or "Available subcommands" in full_text

    def test_cargo_new_binary_project(self, executor, temp_dir):
        result = executor.execute_sync(["new", "test_project", "--bin"], temp_dir)
        assert result.success is True
        project_dir = os.path.join(temp_dir, "test_project")
        assert os.path.isdir(project_dir)
        assert os.path.isfile(os.path.join(project_dir, "Cargo.toml"))
        assert os.path.isfile(os.path.join(project_dir, "src", "main.rs"))

    def test_cargo_new_library_project(self, executor, temp_dir):
        result = executor.execute_sync(["new", "test_lib", "--lib"], temp_dir)
        assert result.success is True
        project_dir = os.path.join(temp_dir, "test_lib")
        assert os.path.isdir(project_dir)
        assert os.path.isfile(os.path.join(project_dir, "Cargo.toml"))
        assert os.path.isfile(os.path.join(project_dir, "src", "lib.rs"))

    def test_cargo_check_on_new_project(self, executor, temp_dir):
        executor.execute_sync(["new", "check_test", "--bin"], temp_dir)
        project_dir = os.path.join(temp_dir, "check_test")
        result = executor.execute_sync(["check"], project_dir)
        assert result.success is True

    def test_cargo_fmt_on_new_project(self, executor, temp_dir):
        executor.execute_sync(["new", "fmt_test", "--bin"], temp_dir)
        project_dir = os.path.join(temp_dir, "fmt_test")
        result = executor.execute_sync(["fmt"], project_dir)
        assert result.success is True

    def test_cargo_clean_on_new_project(self, executor, temp_dir):
        executor.execute_sync(["new", "clean_test", "--bin"], temp_dir)
        project_dir = os.path.join(temp_dir, "clean_test")
        executor.execute_sync(["build"], project_dir)
        result = executor.execute_sync(["clean"], project_dir)
        assert result.success is True

    def test_cargo_version(self, executor, temp_dir):
        result = executor.execute_sync(["--version"], temp_dir)
        assert result.success is True
        full_text = "\n".join(line[0] for line in result.lines)
        assert "cargo" in full_text.lower()

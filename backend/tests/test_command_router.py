import os
import tempfile
import pytest
from app.commands.command_router import CommandRouter


@pytest.fixture
def router():
    return CommandRouter()


@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


class TestParseInput:
    def test_parse_simple_command(self, router):
        cmd, args = router.parse_input("dir")
        assert cmd == "dir"
        assert args == []

    def test_parse_command_with_args(self, router):
        cmd, args = router.parse_input("cd subdir")
        assert cmd == "cd"
        assert args == ["subdir"]

    def test_parse_empty_input(self, router):
        cmd, args = router.parse_input("")
        assert cmd == ""
        assert args == []

    def test_parse_whitespace_only(self, router):
        cmd, args = router.parse_input("   ")
        assert cmd == ""
        assert args == []

    def test_parse_case_insensitive_command(self, router):
        cmd, args = router.parse_input("DIR /w")
        assert cmd == "dir"
        assert args == ["/w"]

    def test_parse_quoted_args(self, router):
        cmd, args = router.parse_input('echo "hello world"')
        assert cmd == "echo"
        assert args == ["hello world"]


class TestExecute:
    def test_execute_empty_input(self, router, temp_dir):
        result = router.execute("", temp_dir)
        assert result.success is True
        assert result.lines == []

    def test_execute_unknown_command(self, router, temp_dir):
        result = router.execute("foobar", temp_dir)
        assert result.success is False
        full_text = "\n".join(line[0] for line in result.lines)
        assert "not recognized" in full_text

    def test_execute_exit_command(self, router, temp_dir):
        result = router.execute("exit", temp_dir)
        assert result.output == "__EXIT__"

    def test_execute_quit_command(self, router, temp_dir):
        result = router.execute("quit", temp_dir)
        assert result.output == "__EXIT__"

    def test_execute_dos_command_dir(self, router, temp_dir):
        result = router.execute("dir", temp_dir)
        assert result.success is True
        full_text = "\n".join(line[0] for line in result.lines)
        assert "Directory of" in full_text

    def test_execute_dos_command_echo(self, router, temp_dir):
        result = router.execute("echo hello test", temp_dir)
        assert result.success is True
        full_text = "\n".join(line[0] for line in result.lines)
        assert "hello test" in full_text

    def test_execute_dos_command_mkdir_and_rmdir(self, router, temp_dir):
        result = router.execute("mkdir testdir", temp_dir)
        assert result.success is True
        assert os.path.isdir(os.path.join(temp_dir, "testdir"))

        result = router.execute("rmdir testdir", temp_dir)
        assert result.success is True
        assert not os.path.isdir(os.path.join(temp_dir, "testdir"))

    def test_execute_dos_command_cd_changes_cwd(self, router, temp_dir):
        os.makedirs(os.path.join(temp_dir, "subdir"))
        result = router.execute("cd subdir", temp_dir)
        assert result.success is True
        assert result.new_cwd == os.path.normpath(os.path.join(temp_dir, "subdir"))

    def test_execute_help(self, router, temp_dir):
        result = router.execute("help", temp_dir)
        assert result.success is True
        full_text = "\n".join(line[0] for line in result.lines)
        assert "Command Reference" in full_text


class TestExecuteAsync:
    def test_execute_async_non_cargo_returns_false(self, router, temp_dir):
        called = {"output": False, "complete": False}

        def on_output(text, output_type):
            called["output"] = True

        def on_complete(code):
            called["complete"] = True

        result = router.execute_async("echo hello", temp_dir, on_output, on_complete)
        assert result is False

    def test_execute_async_cargo_without_args_returns_false(self, router, temp_dir):
        def on_output(text, output_type):
            pass

        def on_complete(code):
            pass

        result = router.execute_async("cargo", temp_dir, on_output, on_complete)
        assert result is False

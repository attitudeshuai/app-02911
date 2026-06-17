"""
Unit tests for CommandRouter - input parsing and command dispatch.
Headless testing - no GUI required.
"""
import os
import pytest


class TestCommandRouter:
    def test_parse_input_basic(self, router):
        cmd, args = router.parse_input("dir /w")
        assert cmd == "dir"
        assert args == ["/w"]

    def test_parse_input_empty(self, router):
        cmd, args = router.parse_input("")
        assert cmd == ""
        assert args == []

    def test_parse_input_whitespace(self, router):
        cmd, args = router.parse_input("   echo   hello   world   ")
        assert cmd == "echo"
        assert args == ["hello", "world"]

    def test_parse_input_case_insensitive(self, router):
        cmd, args = router.parse_input("DIR")
        assert cmd == "dir"

    def test_parse_input_quoted(self, router):
        cmd, args = router.parse_input('echo "hello world"')
        assert cmd == "echo"
        assert args == ["hello world"]

    def test_execute_echo(self, router, temp_workspace):
        result = router.execute("echo test message", temp_workspace)
        assert result.success is True
        assert len(result.lines) == 1
        assert result.lines[0][0] == "test message"

    def test_execute_unknown_command(self, router, temp_workspace):
        result = router.execute("foobar", temp_workspace)
        assert result.success is False
        texts = [line[0] for line in result.lines]
        assert any("not recognized" in t for t in texts)

    def test_execute_empty(self, router, temp_workspace):
        result = router.execute("", temp_workspace)
        assert result.success is True

    def test_execute_pwd(self, router, temp_workspace):
        result = router.execute("pwd", temp_workspace)
        assert result.success is True
        assert result.lines[0][0] == temp_workspace

    def test_execute_cd_changes_cwd(self, router, temp_workspace):
        subdir = os.path.join(temp_workspace, "mydir")
        os.makedirs(subdir)

        result = router.execute("cd mydir", temp_workspace)
        assert result.success is True
        assert os.path.normpath(result.new_cwd) == os.path.normpath(subdir)

    def test_execute_mkdir_and_dir(self, router, temp_workspace):
        result = router.execute("mkdir newdir", temp_workspace)
        assert result.success is True
        assert os.path.isdir(os.path.join(temp_workspace, "newdir"))

        result = router.execute("dir", temp_workspace)
        assert result.success is True
        texts = [line[0] for line in result.lines]
        assert any("newdir" in t for t in texts)

    def test_execute_exit(self, router, temp_workspace):
        result = router.execute("exit", temp_workspace)
        assert result.output == "__EXIT__"

    def test_execute_help(self, router, temp_workspace):
        result = router.execute("help", temp_workspace)
        assert result.success is True
        assert len(result.lines) > 5

    def test_execute_alias_ls(self, router, temp_workspace):
        result = router.execute("ls", temp_workspace)
        assert result.success is True

    def test_execute_alias_clear(self, router, temp_workspace):
        result = router.execute("clear", temp_workspace)
        assert result.clear_screen is True

    def test_execute_alias_cat(self, router, temp_workspace):
        f = os.path.join(temp_workspace, "a.txt")
        with open(f, "w") as fh:
            fh.write("content")
        result = router.execute("cat a.txt", temp_workspace)
        assert result.success is True
        assert result.lines[0][0] == "content"

"""
Unit tests for CommandRouter and DOS commands.
These tests do NOT require a GUI.
"""
import os
import sys
import tempfile
import shutil
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.commands.command_router import CommandRouter
from app.commands.base import CommandResult, OutputType


@pytest.fixture
def router():
    return CommandRouter()


@pytest.fixture
def tmp_workspace():
    tmpdir = tempfile.mkdtemp(prefix="cargo_test_")
    yield tmpdir
    shutil.rmtree(tmpdir, ignore_errors=True)


class TestCommandRouter:
    def test_parse_input_empty(self, router):
        cmd, args = router.parse_input("")
        assert cmd == ""
        assert args == []

    def test_parse_input_single(self, router):
        cmd, args = router.parse_input("ver")
        assert cmd == "ver"
        assert args == []

    def test_parse_input_with_args(self, router):
        cmd, args = router.parse_input("cd /tmp/test")
        assert cmd == "cd"
        assert args == ["/tmp/test"]

    def test_parse_input_case_insensitive(self, router):
        cmd, args = router.parse_input("DIR")
        assert cmd == "dir"

    def test_execute_empty(self, router, tmp_workspace):
        result = router.execute("", tmp_workspace)
        assert isinstance(result, CommandResult)
        assert result.success

    def test_execute_unknown(self, router, tmp_workspace):
        result = router.execute("nonexistent", tmp_workspace)
        assert not result.success
        assert len(result.lines) > 0


class TestDosCommands:
    def test_ver(self, router, tmp_workspace):
        result = router.execute("ver", tmp_workspace)
        assert result.success
        assert len(result.lines) > 0

    def test_help(self, router, tmp_workspace):
        result = router.execute("help", tmp_workspace)
        assert result.success
        assert len(result.lines) > 0

    def test_help_alias(self, router, tmp_workspace):
        result = router.execute("?", tmp_workspace)
        assert result.success

    def test_echo(self, router, tmp_workspace):
        result = router.execute("echo hello test", tmp_workspace)
        assert result.success
        text_found = any("hello test" in line for line, _ in result.lines)
        assert text_found

    def test_mkdir_and_dir(self, router, tmp_workspace):
        result = router.execute("mkdir testdir", tmp_workspace)
        assert result.success
        assert os.path.isdir(os.path.join(tmp_workspace, "testdir"))

        result = router.execute("dir", tmp_workspace)
        assert result.success
        assert len(result.lines) > 0

    def test_mkdir_alias_md(self, router, tmp_workspace):
        result = router.execute("md testdir2", tmp_workspace)
        assert result.success
        assert os.path.isdir(os.path.join(tmp_workspace, "testdir2"))

    def test_cd(self, router, tmp_workspace):
        subdir = os.path.join(tmp_workspace, "subdir")
        os.makedirs(subdir)

        result = router.execute("cd subdir", tmp_workspace)
        assert result.success
        assert result.new_cwd == subdir

    def test_cd_alias_chdir(self, router, tmp_workspace):
        subdir = os.path.join(tmp_workspace, "subdir2")
        os.makedirs(subdir)

        result = router.execute("chdir subdir2", tmp_workspace)
        assert result.success
        assert result.new_cwd == subdir

    def test_pwd(self, router, tmp_workspace):
        result = router.execute("pwd", tmp_workspace)
        assert result.success
        found = any(tmp_workspace in line for line, _ in result.lines)
        assert found

    def test_type_file(self, router, tmp_workspace):
        test_file = os.path.join(tmp_workspace, "test.txt")
        with open(test_file, "w") as f:
            f.write("line1\nline2\n")

        result = router.execute("type test.txt", tmp_workspace)
        assert result.success

    def test_cat_alias(self, router, tmp_workspace):
        test_file = os.path.join(tmp_workspace, "test.txt")
        with open(test_file, "w") as f:
            f.write("content\n")

        result = router.execute("cat test.txt", tmp_workspace)
        assert result.success

    def test_del_file(self, router, tmp_workspace):
        test_file = os.path.join(tmp_workspace, "delme.txt")
        with open(test_file, "w") as f:
            f.write("delete me\n")

        result = router.execute("del delme.txt", tmp_workspace)
        assert result.success
        assert not os.path.exists(test_file)

    def test_rm_alias(self, router, tmp_workspace):
        test_file = os.path.join(tmp_workspace, "delme2.txt")
        with open(test_file, "w") as f:
            f.write("delete me\n")

        result = router.execute("rm delme2.txt", tmp_workspace)
        assert result.success
        assert not os.path.exists(test_file)

    def test_rmdir(self, router, tmp_workspace):
        subdir = os.path.join(tmp_workspace, "to_remove")
        os.makedirs(subdir)

        result = router.execute("rmdir to_remove", tmp_workspace)
        assert result.success
        assert not os.path.exists(subdir)

    def test_rd_alias(self, router, tmp_workspace):
        subdir = os.path.join(tmp_workspace, "to_remove2")
        os.makedirs(subdir)

        result = router.execute("rd to_remove2", tmp_workspace)
        assert result.success
        assert not os.path.exists(subdir)

    def test_cls(self, router, tmp_workspace):
        result = router.execute("cls", tmp_workspace)
        assert result.success
        assert result.clear_screen

    def test_clear_alias(self, router, tmp_workspace):
        result = router.execute("clear", tmp_workspace)
        assert result.success
        assert result.clear_screen

    def test_exit(self, router, tmp_workspace):
        result = router.execute("exit", tmp_workspace)
        assert result.output == "__EXIT__"

    def test_quit_alias(self, router, tmp_workspace):
        result = router.execute("quit", tmp_workspace)
        assert result.output == "__EXIT__"

    def test_tree(self, router, tmp_workspace):
        os.makedirs(os.path.join(tmp_workspace, "a", "b"))
        result = router.execute("tree", tmp_workspace)
        assert result.success
        assert len(result.lines) > 0

    def test_dir_alias_ls(self, router, tmp_workspace):
        result = router.execute("ls", tmp_workspace)
        assert result.success

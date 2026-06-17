"""
Unit tests for DOS built-in commands.
These tests run headless - no GUI required.
"""
import os
import pytest

from app.commands.dos_commands import DosCommands
from app.commands.base import OutputType


class TestDosCommands:
    def test_echo_basic(self, temp_workspace):
        result = DosCommands.cmd_echo(["hello", "world"], temp_workspace)
        assert result.success is True
        assert len(result.lines) == 1
        assert result.lines[0][0] == "hello world"

    def test_echo_empty(self, temp_workspace):
        result = DosCommands.cmd_echo([], temp_workspace)
        assert result.success is True
        assert result.lines[0][0] == "ECHO is on."

    def test_pwd(self, temp_workspace):
        result = DosCommands.cmd_pwd([], temp_workspace)
        assert result.success is True
        assert result.lines[0][0] == temp_workspace

    def test_ver(self, temp_workspace):
        result = DosCommands.cmd_ver([], temp_workspace)
        assert result.success is True
        texts = [line[0] for line in result.lines]
        assert any("Rust Cargo DOS Commander" in t for t in texts)

    def test_help(self, temp_workspace):
        result = DosCommands.cmd_help([], temp_workspace)
        assert result.success is True
        assert len(result.lines) > 5
        texts = [line[0] for line in result.lines]
        assert any("DIR" in t for t in texts)
        assert any("CD" in t for t in texts)

    def test_cls(self, temp_workspace):
        result = DosCommands.cmd_cls([], temp_workspace)
        assert result.clear_screen is True

    def test_mkdir_and_rmdir(self, temp_workspace):
        result = DosCommands.cmd_mkdir(["testdir"], temp_workspace)
        assert result.success is True
        assert os.path.isdir(os.path.join(temp_workspace, "testdir"))

        result = DosCommands.cmd_rmdir(["testdir"], temp_workspace)
        assert result.success is True
        assert not os.path.isdir(os.path.join(temp_workspace, "testdir"))

    def test_mkdir_already_exists(self, temp_workspace):
        os.makedirs(os.path.join(temp_workspace, "existing"))
        result = DosCommands.cmd_mkdir(["existing"], temp_workspace)
        assert result.success is True
        assert result.lines[0][1] == OutputType.WARNING

    def test_rmdir_not_found(self, temp_workspace):
        result = DosCommands.cmd_rmdir(["nope"], temp_workspace)
        assert result.success is False

    def test_dir_listing(self, temp_workspace):
        os.makedirs(os.path.join(temp_workspace, "subdir"))
        with open(os.path.join(temp_workspace, "file.txt"), "w") as f:
            f.write("hello")

        result = DosCommands.cmd_dir([], temp_workspace)
        assert result.success is True
        texts = [line[0] for line in result.lines]
        assert any("subdir" in t for t in texts)
        assert any("file.txt" in t for t in texts)
        assert any("File(s)" in t for t in texts)
        assert any("Dir(s)" in t for t in texts)

    def test_dir_not_found(self, temp_workspace):
        result = DosCommands.cmd_dir(["nonexistent"], temp_workspace)
        assert result.success is False

    def test_cd_and_back(self, temp_workspace):
        target = os.path.join(temp_workspace, "subdir")
        os.makedirs(target)

        result = DosCommands.cmd_cd(["subdir"], temp_workspace)
        assert result.success is True
        assert os.path.normpath(result.new_cwd) == os.path.normpath(target)

        result = DosCommands.cmd_cd([".."], target)
        assert result.success is True
        assert os.path.normpath(result.new_cwd) == os.path.normpath(temp_workspace)

    def test_cd_no_args(self, temp_workspace):
        result = DosCommands.cmd_cd([], temp_workspace)
        assert result.success is True
        assert result.lines[0][0] == temp_workspace
        assert result.new_cwd is None

    def test_cd_not_found(self, temp_workspace):
        result = DosCommands.cmd_cd(["nope"], temp_workspace)
        assert result.success is False
        assert result.new_cwd is None

    def test_type_file(self, temp_workspace):
        filepath = os.path.join(temp_workspace, "test.txt")
        with open(filepath, "w") as f:
            f.write("line1\nline2\n")

        result = DosCommands.cmd_type(["test.txt"], temp_workspace)
        assert result.success is True
        assert result.lines[0][0] == "line1\nline2\n"

    def test_type_not_found(self, temp_workspace):
        result = DosCommands.cmd_type(["nope.txt"], temp_workspace)
        assert result.success is False

    def test_type_no_args(self, temp_workspace):
        result = DosCommands.cmd_type([], temp_workspace)
        assert result.success is False

    def test_del_file(self, temp_workspace):
        filepath = os.path.join(temp_workspace, "delme.txt")
        with open(filepath, "w") as f:
            f.write("delete me")

        result = DosCommands.cmd_del(["delme.txt"], temp_workspace)
        assert result.success is True
        assert not os.path.isfile(filepath)

    def test_del_not_found(self, temp_workspace):
        result = DosCommands.cmd_del(["nope.txt"], temp_workspace)
        assert result.success is False

    def test_tree(self, temp_workspace):
        os.makedirs(os.path.join(temp_workspace, "a", "b"))
        with open(os.path.join(temp_workspace, "a", "file.txt"), "w") as f:
            f.write("x")

        result = DosCommands.cmd_tree([], temp_workspace)
        assert result.success is True
        texts = [line[0] for line in result.lines]
        assert any("Folder PATH listing" in t for t in texts)

    def test_tree_not_found(self, temp_workspace):
        result = DosCommands.cmd_tree(["nope"], temp_workspace)
        assert result.success is False

import os
import tempfile
import pytest
from app.commands.dos_commands import DosCommands
from app.commands.base import OutputType


@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


class TestCmdDir:
    def test_dir_empty_directory(self, temp_dir):
        result = DosCommands.cmd_dir([], temp_dir)
        assert result.success is True
        assert any("Directory of" in line[0] for line in result.lines)
        assert any("0 File(s)" in line[0] for line in result.lines)
        assert any("0 Dir(s)" in line[0] for line in result.lines)

    def test_dir_with_files_and_dirs(self, temp_dir):
        os.makedirs(os.path.join(temp_dir, "subdir"))
        with open(os.path.join(temp_dir, "test.txt"), "w") as f:
            f.write("hello")

        result = DosCommands.cmd_dir([], temp_dir)
        assert result.success is True
        assert any("subdir" in line[0] for line in result.lines)
        assert any("test.txt" in line[0] for line in result.lines)
        assert any("1 File(s)" in line[0] for line in result.lines)
        assert any("1 Dir(s)" in line[0] for line in result.lines)

    def test_dir_nonexistent_path(self, temp_dir):
        result = DosCommands.cmd_dir(["nonexistent"], temp_dir)
        assert result.success is False
        assert any("cannot find the path" in line[0].lower() for line in result.lines)


class TestCmdCd:
    def test_cd_to_subdir(self, temp_dir):
        subdir = os.path.join(temp_dir, "subdir")
        os.makedirs(subdir)

        result = DosCommands.cmd_cd(["subdir"], temp_dir)
        assert result.success is True
        assert result.new_cwd == os.path.normpath(subdir)

    def test_cd_parent(self, temp_dir):
        subdir = os.path.join(temp_dir, "subdir")
        os.makedirs(subdir)

        result = DosCommands.cmd_cd([".."], subdir)
        assert result.success is True
        assert result.new_cwd == temp_dir

    def test_cd_nonexistent(self, temp_dir):
        result = DosCommands.cmd_cd(["nonexistent"], temp_dir)
        assert result.success is False
        assert result.new_cwd is None
        assert any("cannot find the path" in line[0].lower() for line in result.lines)

    def test_cd_no_args_returns_cwd(self, temp_dir):
        result = DosCommands.cmd_cd([], temp_dir)
        assert result.success is True
        assert any(temp_dir in line[0] for line in result.lines)


class TestCmdCls:
    def test_cls_sets_clear_screen(self, temp_dir):
        result = DosCommands.cmd_cls([], temp_dir)
        assert result.clear_screen is True


class TestCmdType:
    def test_type_existing_file(self, temp_dir):
        test_file = os.path.join(temp_dir, "test.txt")
        content = "Hello, World!\nSecond line."
        with open(test_file, "w") as f:
            f.write(content)

        result = DosCommands.cmd_type(["test.txt"], temp_dir)
        assert result.success is True
        assert any(content in line[0] for line in result.lines)

    def test_type_nonexistent_file(self, temp_dir):
        result = DosCommands.cmd_type(["nonexistent.txt"], temp_dir)
        assert result.success is False
        assert any("cannot find the file" in line[0].lower() for line in result.lines)

    def test_type_no_args(self, temp_dir):
        result = DosCommands.cmd_type([], temp_dir)
        assert result.success is False
        assert any("syntax of the command is incorrect" in line[0].lower() for line in result.lines)


class TestCmdMkdir:
    def test_mkdir_new_directory(self, temp_dir):
        result = DosCommands.cmd_mkdir(["newdir"], temp_dir)
        assert result.success is True
        assert os.path.isdir(os.path.join(temp_dir, "newdir"))
        assert any("Directory created" in line[0] for line in result.lines)

    def test_mkdir_existing_directory(self, temp_dir):
        os.makedirs(os.path.join(temp_dir, "existing"))
        result = DosCommands.cmd_mkdir(["existing"], temp_dir)
        assert result.success is True
        assert any("already exists" in line[0].lower() for line in result.lines)

    def test_mkdir_no_args(self, temp_dir):
        result = DosCommands.cmd_mkdir([], temp_dir)
        assert result.success is False
        assert any("syntax of the command is incorrect" in line[0].lower() for line in result.lines)


class TestCmdRmdir:
    def test_rmdir_existing_directory(self, temp_dir):
        target = os.path.join(temp_dir, "toremove")
        os.makedirs(target)

        result = DosCommands.cmd_rmdir(["toremove"], temp_dir)
        assert result.success is True
        assert not os.path.isdir(target)
        assert any("Directory removed" in line[0] for line in result.lines)

    def test_rmdir_nonexistent(self, temp_dir):
        result = DosCommands.cmd_rmdir(["nonexistent"], temp_dir)
        assert result.success is False
        assert any("cannot find the path" in line[0].lower() for line in result.lines)

    def test_rmdir_no_args(self, temp_dir):
        result = DosCommands.cmd_rmdir([], temp_dir)
        assert result.success is False
        assert any("syntax of the command is incorrect" in line[0].lower() for line in result.lines)


class TestCmdDel:
    def test_del_existing_file(self, temp_dir):
        target = os.path.join(temp_dir, "todelete.txt")
        with open(target, "w") as f:
            f.write("delete me")

        result = DosCommands.cmd_del(["todelete.txt"], temp_dir)
        assert result.success is True
        assert not os.path.isfile(target)
        assert any("Deleted" in line[0] for line in result.lines)

    def test_del_nonexistent_file(self, temp_dir):
        result = DosCommands.cmd_del(["nonexistent.txt"], temp_dir)
        assert result.success is False
        assert any("Could not find" in line[0] for line in result.lines)

    def test_del_no_args(self, temp_dir):
        result = DosCommands.cmd_del([], temp_dir)
        assert result.success is False
        assert any("syntax of the command is incorrect" in line[0].lower() for line in result.lines)


class TestCmdEcho:
    def test_echo_with_text(self, temp_dir):
        result = DosCommands.cmd_echo(["hello", "world"], temp_dir)
        assert result.success is True
        assert any("hello world" in line[0] for line in result.lines)

    def test_echo_no_args(self, temp_dir):
        result = DosCommands.cmd_echo([], temp_dir)
        assert result.success is True
        assert any("ECHO is on" in line[0] for line in result.lines)


class TestCmdVer:
    def test_ver_contains_version_info(self, temp_dir):
        result = DosCommands.cmd_ver([], temp_dir)
        assert result.success is True
        full_text = "\n".join(line[0] for line in result.lines)
        assert "Rust Cargo DOS Commander" in full_text
        assert "Version" in full_text


class TestCmdPwd:
    def test_pwd_returns_cwd(self, temp_dir):
        result = DosCommands.cmd_pwd([], temp_dir)
        assert result.success is True
        assert any(temp_dir in line[0] for line in result.lines)


class TestCmdHelp:
    def test_help_contains_commands(self, temp_dir):
        result = DosCommands.cmd_help([], temp_dir)
        assert result.success is True
        full_text = "\n".join(line[0] for line in result.lines)
        assert "Command Reference" in full_text
        assert "DIR" in full_text
        assert "CD" in full_text
        assert "CARGO" in full_text


class TestCmdTree:
    def test_tree_shows_structure(self, temp_dir):
        os.makedirs(os.path.join(temp_dir, "dir1", "subdir"))
        os.makedirs(os.path.join(temp_dir, "dir2"))
        with open(os.path.join(temp_dir, "file.txt"), "w") as f:
            f.write("x")

        result = DosCommands.cmd_tree([], temp_dir)
        assert result.success is True
        full_text = "\n".join(line[0] for line in result.lines)
        assert "Folder PATH listing" in full_text
        assert "dir1" in full_text
        assert "dir2" in full_text

    def test_tree_nonexistent(self, temp_dir):
        result = DosCommands.cmd_tree(["nonexistent"], temp_dir)
        assert result.success is False

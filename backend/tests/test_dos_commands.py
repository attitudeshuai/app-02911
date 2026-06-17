"""
L1 tests for DOS built-in commands.

These exercise CommandRouter -> DosCommands directly with no GUI and no
display required. They cover the "basic commands work" guarantee.
"""

import os

from app.commands.base import OutputType
from app.commands.command_router import CommandRouter


def _text(result) -> str:
    """Flatten a CommandResult into a single lowercase string for assertions."""
    return "\n".join(line for line, _ in result.lines).lower()


def test_dir_lists_files(tmp_path):
    (tmp_path / "hello.txt").write_text("hi", encoding="utf-8")
    (tmp_path / "subdir").mkdir()

    result = CommandRouter().execute("dir", str(tmp_path))

    assert result.success
    assert "hello.txt" in _text(result)
    assert "subdir" in _text(result)


def test_dir_missing_path(tmp_path):
    result = CommandRouter().execute("dir does_not_exist", str(tmp_path))

    assert not result.success
    assert "cannot find the path" in _text(result)


def test_mkdir_then_rmdir(tmp_path):
    router = CommandRouter()

    created = router.execute("mkdir demo", str(tmp_path))
    assert created.success
    assert (tmp_path / "demo").is_dir()

    removed = router.execute("rmdir demo", str(tmp_path))
    assert removed.success
    assert not (tmp_path / "demo").exists()


def test_mkdir_duplicate_is_warning(tmp_path):
    router = CommandRouter()
    router.execute("mkdir demo", str(tmp_path))

    second = router.execute("mkdir demo", str(tmp_path))

    assert second.success is False or any(t == OutputType.WARNING for _, t in second.lines)
    assert (tmp_path / "demo").is_dir()


def test_echo_outputs_text():
    result = CommandRouter().execute("echo hello world", "/tmp")

    assert result.success
    assert "hello world" in _text(result)


def test_echo_no_args_is_on():
    result = CommandRouter().execute("echo", "/tmp")
    assert "echo is on" in _text(result)


def test_ver_shows_version():
    result = CommandRouter().execute("ver", "/tmp")
    text = _text(result)
    assert "version 1.0.0" in text
    assert "python" in text


def test_pwd_prints_cwd(tmp_path):
    result = CommandRouter().execute("pwd", str(tmp_path))
    assert str(tmp_path).lower() in _text(result)


def test_cd_changes_directory(tmp_path):
    sub = tmp_path / "child"
    sub.mkdir()

    result = CommandRouter().execute("cd child", str(tmp_path))

    assert result.success
    assert result.new_cwd == os.path.normpath(str(sub))


def test_cd_parent(tmp_path):
    sub = tmp_path / "child"
    sub.mkdir()
    result = CommandRouter().execute("cd ..", str(sub))
    assert result.success
    assert result.new_cwd == str(tmp_path)


def test_type_displays_file(tmp_path):
    (tmp_path / "note.txt").write_text("line one\nline two", encoding="utf-8")
    result = CommandRouter().execute("type note.txt", str(tmp_path))
    assert result.success
    assert "line one" in _text(result)
    assert "line two" in _text(result)


def test_type_missing_file(tmp_path):
    result = CommandRouter().execute("type nope.txt", str(tmp_path))
    assert not result.success
    assert "cannot find the file" in _text(result)


def test_del_removes_file(tmp_path):
    target = tmp_path / "gone.txt"
    target.write_text("x", encoding="utf-8")

    result = CommandRouter().execute("del gone.txt", str(tmp_path))

    assert result.success
    assert not target.exists()


def test_help_lists_commands():
    result = CommandRouter().execute("help", "/tmp")
    text = _text(result)
    assert result.success
    assert "command reference" in text
    assert "cargo" in text
    assert "mkdir" in text


def test_exit_returns_exit_token():
    result = CommandRouter().execute("exit", "/tmp")
    assert result.output == "__EXIT__"


def test_unknown_command_reports_error():
    result = CommandRouter().execute("foobar", "/tmp")
    assert not result.success
    assert "not recognized" in _text(result)


def test_empty_input_is_noop():
    result = CommandRouter().execute("", "/tmp")
    assert result.success
    assert result.lines == []


def test_case_insensitive_command():
    result = CommandRouter().execute("ECHO UpPeR", "/tmp")
    assert result.success
    assert "echo upper" in _text(result).replace("echo is on", "") or "upper" in _text(result)

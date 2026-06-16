"""
DOS built-in command implementations.
Simulates classic DOS commands: dir, cd, cls, type, mkdir, rmdir, del, echo, help, ver, exit.
"""
import os
import shutil
import platform
from datetime import datetime
from typing import Optional

from app.commands.base import CommandResult, OutputType
from app.logger import logger


class DosCommands:
    """Handles DOS-style built-in commands."""

    HELP_TEXT = {
        "dir": "DIR [path]              - List directory contents",
        "cd": "CD [path]               - Change current directory",
        "cls": "CLS                     - Clear the screen",
        "type": "TYPE <file>             - Display file contents",
        "mkdir": "MKDIR <dir>             - Create a directory",
        "md": "MD <dir>                - Create a directory (alias)",
        "rmdir": "RMDIR <dir>             - Remove a directory",
        "rd": "RD <dir>                - Remove a directory (alias)",
        "del": "DEL <file>              - Delete a file",
        "echo": "ECHO <text>             - Display text",
        "ver": "VER                     - Display version info",
        "help": "HELP                    - Show this help message",
        "exit": "EXIT                    - Close the application",
        "tree": "TREE [path]             - Display directory tree",
        "pwd": "PWD                     - Print working directory",
        "cargo": "CARGO <subcommand>      - Run Rust Cargo commands",
        "toml": "TOML                    - Open Cargo.toml visual editor",
    }

    @staticmethod
    def cmd_dir(args: list, cwd: str) -> CommandResult:
        """List directory contents in DOS style."""
        result = CommandResult()
        target = os.path.join(cwd, args[0]) if args else cwd

        if not os.path.isdir(target):
            result.add_error(f"The system cannot find the path specified: {target}")
            return result

        try:
            entries = sorted(os.listdir(target))
            result.add_system(f" Directory of {os.path.abspath(target)}")
            result.add_line("")

            total_files = 0
            total_dirs = 0
            total_size = 0

            for entry in entries:
                full_path = os.path.join(target, entry)
                try:
                    stat = os.stat(full_path)
                    mod_time = datetime.fromtimestamp(stat.st_mtime)
                    date_str = mod_time.strftime("%Y-%m-%d  %H:%M")

                    if os.path.isdir(full_path):
                        result.add_info(f"{date_str}    <DIR>          {entry}")
                        total_dirs += 1
                    else:
                        size = stat.st_size
                        total_size += size
                        result.add_line(f"{date_str}    {size:>14,} {entry}")
                        total_files += 1
                except PermissionError:
                    result.add_warning(f"{' ' * 20}    <ACCESS DENIED> {entry}")

            result.add_line("")
            result.add_system(f"    {total_files:>8} File(s)  {total_size:>14,} bytes")
            result.add_system(f"    {total_dirs:>8} Dir(s)")
            logger.info("DIR command executed on: %s (%d files, %d dirs)", target, total_files, total_dirs)
        except PermissionError:
            result.add_error(f"Access denied: {target}")
        except OSError as e:
            result.add_error(f"Error reading directory: {e}")

        return result

    @staticmethod
    def cmd_cd(args: list, cwd: str) -> CommandResult:
        """Change directory."""
        result = CommandResult()

        if not args:
            result.add_line(cwd)
            return result

        target = args[0]

        if target == "..":
            new_path = os.path.dirname(cwd)
        elif target == "\\" or target == "/":
            new_path = os.path.splitdrive(cwd)[0] or "/"
        elif os.path.isabs(target):
            new_path = target
        else:
            new_path = os.path.normpath(os.path.join(cwd, target))

        if os.path.isdir(new_path):
            result.new_cwd = new_path
            logger.info("CD: %s -> %s", cwd, new_path)
        else:
            result.add_error(f"The system cannot find the path specified: {target}")

        return result

    @staticmethod
    def cmd_cls(_args: list, _cwd: str) -> CommandResult:
        """Clear screen."""
        result = CommandResult()
        result.clear_screen = True
        return result

    @staticmethod
    def cmd_type(args: list, cwd: str) -> CommandResult:
        """Display file contents."""
        result = CommandResult()

        if not args:
            result.add_error("The syntax of the command is incorrect.")
            result.add_error("Usage: TYPE <filename>")
            return result

        filepath = os.path.join(cwd, args[0]) if not os.path.isabs(args[0]) else args[0]

        if not os.path.isfile(filepath):
            result.add_error(f"The system cannot find the file specified: {args[0]}")
            return result

        try:
            with open(filepath, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
            result.add_line(content)
            logger.info("TYPE: displayed file %s", filepath)
        except PermissionError:
            result.add_error(f"Access denied: {args[0]}")
        except OSError as e:
            result.add_error(f"Error reading file: {e}")

        return result

    @staticmethod
    def cmd_mkdir(args: list, cwd: str) -> CommandResult:
        """Create directory."""
        result = CommandResult()

        if not args:
            result.add_error("The syntax of the command is incorrect.")
            result.add_error("Usage: MKDIR <dirname>")
            return result

        target = os.path.join(cwd, args[0]) if not os.path.isabs(args[0]) else args[0]

        try:
            os.makedirs(target, exist_ok=False)
            result.add_success(f"Directory created: {args[0]}")
            logger.info("MKDIR: created %s", target)
        except FileExistsError:
            result.add_warning(f"A subdirectory or file {args[0]} already exists.")
        except OSError as e:
            result.add_error(f"Error creating directory: {e}")

        return result

    @staticmethod
    def cmd_rmdir(args: list, cwd: str) -> CommandResult:
        """Remove directory."""
        result = CommandResult()

        if not args:
            result.add_error("The syntax of the command is incorrect.")
            result.add_error("Usage: RMDIR <dirname>")
            return result

        target = os.path.join(cwd, args[0]) if not os.path.isabs(args[0]) else args[0]

        if not os.path.isdir(target):
            result.add_error(f"The system cannot find the path specified: {args[0]}")
            return result

        try:
            shutil.rmtree(target)
            result.add_success(f"Directory removed: {args[0]}")
            logger.info("RMDIR: removed %s", target)
        except PermissionError:
            result.add_error(f"Access denied: {args[0]}")
        except OSError as e:
            result.add_error(f"Error removing directory: {e}")

        return result

    @staticmethod
    def cmd_del(args: list, cwd: str) -> CommandResult:
        """Delete file."""
        result = CommandResult()

        if not args:
            result.add_error("The syntax of the command is incorrect.")
            result.add_error("Usage: DEL <filename>")
            return result

        target = os.path.join(cwd, args[0]) if not os.path.isabs(args[0]) else args[0]

        if not os.path.isfile(target):
            result.add_error(f"Could not find: {args[0]}")
            return result

        try:
            os.remove(target)
            result.add_success(f"Deleted: {args[0]}")
            logger.info("DEL: deleted %s", target)
        except PermissionError:
            result.add_error(f"Access denied: {args[0]}")
        except OSError as e:
            result.add_error(f"Error deleting file: {e}")

        return result

    @staticmethod
    def cmd_echo(args: list, _cwd: str) -> CommandResult:
        """Echo text."""
        result = CommandResult()
        result.add_line(" ".join(args) if args else "ECHO is on.")
        return result

    @staticmethod
    def cmd_ver(_args: list, _cwd: str) -> CommandResult:
        """Display version."""
        result = CommandResult()
        result.add_system("")
        result.add_system("Rust Cargo DOS Commander [Version 1.0.0]")
        result.add_system(f"Python {platform.python_version()} on {platform.system()} {platform.release()}")
        result.add_system("")
        return result

    @staticmethod
    def cmd_pwd(_args: list, cwd: str) -> CommandResult:
        """Print working directory."""
        result = CommandResult()
        result.add_line(cwd)
        return result

    @staticmethod
    def cmd_tree(args: list, cwd: str, max_depth: int = 4) -> CommandResult:
        """Display directory tree."""
        result = CommandResult()
        target = os.path.join(cwd, args[0]) if args else cwd

        if not os.path.isdir(target):
            result.add_error(f"The system cannot find the path specified: {target}")
            return result

        result.add_info(f"Folder PATH listing for {os.path.abspath(target)}")

        def _walk(path: str, prefix: str, depth: int):
            if depth > max_depth:
                result.add_line(f"{prefix}...")
                return
            try:
                entries = sorted(os.listdir(path))
            except PermissionError:
                result.add_warning(f"{prefix}[ACCESS DENIED]")
                return

            dirs = [e for e in entries if os.path.isdir(os.path.join(path, e)) and not e.startswith(".")]
            for i, d in enumerate(dirs):
                is_last = i == len(dirs) - 1
                connector = "└── " if is_last else "├── "
                result.add_info(f"{prefix}{connector}{d}")
                extension = "    " if is_last else "│   "
                _walk(os.path.join(path, d), prefix + extension, depth + 1)

        _walk(target, "", 0)
        return result

    @staticmethod
    def cmd_help(_args: list, _cwd: str) -> CommandResult:
        """Show help."""
        result = CommandResult()
        result.add_system("")
        result.add_system("═══════════════════════════════════════════════════════════")
        result.add_system("  Rust Cargo DOS Commander - Command Reference")
        result.add_system("═══════════════════════════════════════════════════════════")
        result.add_line("")

        for cmd, desc in sorted(DosCommands.HELP_TEXT.items()):
            result.add_line(f"  {desc}")

        result.add_line("")
        result.add_info("  Cargo subcommands: new, build, run, test, check, clean,")
        result.add_info("                     doc, bench, update, fmt, clippy")
        result.add_line("")
        result.add_system("═══════════════════════════════════════════════════════════")
        return result

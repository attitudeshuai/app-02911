"""
Command router - parses user input and dispatches to appropriate handler.
Central hub for all command processing.
"""
import shlex
from typing import Callable, Optional

from app.commands.base import CommandResult, OutputType
from app.commands.dos_commands import DosCommands
from app.commands.cargo_executor import CargoExecutor
from app.logger import logger


class CommandRouter:
    """Routes parsed commands to their respective handlers."""

    # Map command names to handler methods
    DOS_COMMAND_MAP = {
        "dir": DosCommands.cmd_dir,
        "ls": DosCommands.cmd_dir,
        "cd": DosCommands.cmd_cd,
        "chdir": DosCommands.cmd_cd,
        "cls": DosCommands.cmd_cls,
        "clear": DosCommands.cmd_cls,
        "type": DosCommands.cmd_type,
        "cat": DosCommands.cmd_type,
        "mkdir": DosCommands.cmd_mkdir,
        "md": DosCommands.cmd_mkdir,
        "rmdir": DosCommands.cmd_rmdir,
        "rd": DosCommands.cmd_rmdir,
        "del": DosCommands.cmd_del,
        "rm": DosCommands.cmd_del,
        "echo": DosCommands.cmd_echo,
        "ver": DosCommands.cmd_ver,
        "pwd": DosCommands.cmd_pwd,
        "tree": DosCommands.cmd_tree,
        "help": DosCommands.cmd_help,
        "?": DosCommands.cmd_help,
    }

    def __init__(self):
        self.cargo = CargoExecutor()

    def parse_input(self, raw_input: str) -> tuple:
        """Parse raw input into command and arguments."""
        raw_input = raw_input.strip()
        logger.debug("Raw input received: %r (len=%d)", raw_input, len(raw_input))
        if not raw_input:
            return "", []

        try:
            parts = shlex.split(raw_input)
        except ValueError:
            parts = raw_input.split()

        command = parts[0].lower()
        args = parts[1:]
        logger.debug("Parsed command: %r, args: %r", command, args)
        return command, args

    def execute(self, raw_input: str, cwd: str) -> CommandResult:
        """Execute a command synchronously."""
        command, args = self.parse_input(raw_input)

        if not command:
            return CommandResult()

        logger.debug("Routing command: '%s' args=%s cwd=%s", command, args, cwd)

        # Check for exit
        if command in ("exit", "quit"):
            result = CommandResult()
            result.add_system("Goodbye!")
            result.output = "__EXIT__"
            return result

        # DOS built-in commands
        if command in self.DOS_COMMAND_MAP:
            handler = self.DOS_COMMAND_MAP[command]
            return handler(args, cwd)

        # Cargo commands
        if command == "cargo":
            return self.cargo.execute_sync(args, cwd)

        # Unknown command
        result = CommandResult()
        result.add_error(f"'{command}' is not recognized as an internal or external command,")
        result.add_error("operable program or batch file.")
        result.add_line("")
        result.add_info("Type 'help' for a list of available commands.")
        return result

    def execute_async(self, raw_input: str, cwd: str,
                      on_output: Callable[[str, OutputType], None],
                      on_complete: Callable[[int], None]) -> bool:
        """Execute a command asynchronously (for cargo commands that may take long)."""
        command, args = self.parse_input(raw_input)

        if command == "cargo" and args:
            self.cargo.execute_async(args, cwd, on_output, on_complete)
            return True
        return False

    def cancel_running(self):
        """Cancel any running async process."""
        self.cargo.cancel()

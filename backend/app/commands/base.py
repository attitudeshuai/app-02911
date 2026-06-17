"""
Base command interface and result container.
"""

from dataclasses import dataclass, field
from enum import Enum


class OutputType(Enum):
    """Output message type for color coding."""

    NORMAL = "normal"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"
    SUCCESS = "success"
    SYSTEM = "system"


@dataclass
class CommandResult:
    """Encapsulates the result of a command execution."""

    output: str = ""
    output_type: OutputType = OutputType.NORMAL
    success: bool = True
    new_cwd: str | None = None  # If command changes directory
    clear_screen: bool = False
    lines: list = field(default_factory=list)  # For multi-type output

    def add_line(self, text: str, output_type: OutputType = OutputType.NORMAL):
        """Add a line with specific type."""
        self.lines.append((text, output_type))

    def add_error(self, text: str):
        self.add_line(text, OutputType.ERROR)
        self.success = False

    def add_info(self, text: str):
        self.add_line(text, OutputType.INFO)

    def add_success(self, text: str):
        self.add_line(text, OutputType.SUCCESS)

    def add_warning(self, text: str):
        self.add_line(text, OutputType.WARNING)

    def add_system(self, text: str):
        self.add_line(text, OutputType.SYSTEM)

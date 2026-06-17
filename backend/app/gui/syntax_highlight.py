"""
Syntax highlighting for Rust source code and simulated compile error display.
Provides keyword-based highlighting for .rs files shown via 'type' command,
and formatted display of cargo build errors.
"""

import re
import tkinter as tk

from app.commands.base import OutputType


# Rust syntax token colors
class RustColors:
    KEYWORD = "#569CD6"  # blue - fn, let, mut, pub, struct, etc.
    TYPE = "#4EC9B0"  # teal - i32, String, Vec, etc.
    STRING = "#CE9178"  # orange - string literals
    COMMENT = "#6A9955"  # green - comments
    NUMBER = "#B5CEA8"  # light green - numeric literals
    MACRO = "#DCDCAA"  # yellow - macros like println!
    ATTRIBUTE = "#C586C0"  # purple - #[derive(...)]
    LIFETIME = "#D7BA7D"  # gold - 'a, 'static
    OPERATOR = "#D4D4D4"  # light gray
    FUNCTION = "#DCDCAA"  # yellow - function names


# Rust keywords
RUST_KEYWORDS = {
    "as",
    "async",
    "await",
    "break",
    "const",
    "continue",
    "crate",
    "dyn",
    "else",
    "enum",
    "extern",
    "false",
    "fn",
    "for",
    "if",
    "impl",
    "in",
    "let",
    "loop",
    "match",
    "mod",
    "move",
    "mut",
    "pub",
    "ref",
    "return",
    "self",
    "Self",
    "static",
    "struct",
    "super",
    "trait",
    "true",
    "type",
    "unsafe",
    "use",
    "where",
    "while",
    "yield",
}

RUST_TYPES = {
    "i8",
    "i16",
    "i32",
    "i64",
    "i128",
    "isize",
    "u8",
    "u16",
    "u32",
    "u64",
    "u128",
    "usize",
    "f32",
    "f64",
    "bool",
    "char",
    "str",
    "String",
    "Vec",
    "Option",
    "Result",
    "Box",
    "Rc",
    "Arc",
    "HashMap",
    "HashSet",
    "BTreeMap",
    "BTreeSet",
    "Ok",
    "Err",
    "Some",
    "None",
}

# Regex patterns for Rust syntax
RUST_PATTERNS = [
    ("comment_line", r"//.*$"),
    ("comment_block", r"/\*[\s\S]*?\*/"),
    ("string_double", r'"(?:[^"\\]|\\.)*"'),
    ("string_raw", r'r#*"[\s\S]*?"#*'),
    ("char_literal", r"'(?:[^'\\]|\\.)'"),
    ("attribute", r"#\[[\w:(),\s]*\]"),
    ("lifetime", r"'\w+"),
    ("macro_call", r"\b\w+!"),
    (
        "number",
        r"\b(?:0x[\da-fA-F_]+|0b[01_]+|0o[0-7_]+|\d[\d_]*(?:\.\d[\d_]*)?(?:[eE][+-]?\d+)?)\b",
    ),
    ("keyword", r"\b(?:" + "|".join(RUST_KEYWORDS) + r")\b"),
    ("type", r"\b(?:" + "|".join(RUST_TYPES) + r")\b"),
    ("function_def", r"(?<=fn\s)\w+"),
]

# Compile patterns
COMPILED_PATTERNS = [(name, re.compile(pattern, re.MULTILINE)) for name, pattern in RUST_PATTERNS]

TOKEN_COLORS = {
    "comment_line": RustColors.COMMENT,
    "comment_block": RustColors.COMMENT,
    "string_double": RustColors.STRING,
    "string_raw": RustColors.STRING,
    "char_literal": RustColors.STRING,
    "attribute": RustColors.ATTRIBUTE,
    "lifetime": RustColors.LIFETIME,
    "macro_call": RustColors.MACRO,
    "number": RustColors.NUMBER,
    "keyword": RustColors.KEYWORD,
    "type": RustColors.TYPE,
    "function_def": RustColors.FUNCTION,
}


class SyntaxHighlighter:
    """Applies syntax highlighting to Rust code displayed in a Text widget."""

    @staticmethod
    def setup_tags(text_widget: tk.Text):
        """Configure syntax highlight tags on a Text widget."""
        for token_name, color in TOKEN_COLORS.items():
            text_widget.tag_configure(f"syn_{token_name}", foreground=color)
        # Line number tag
        text_widget.tag_configure("line_number", foreground="#858585")

    @staticmethod
    def highlight_rust_code(text_widget: tk.Text, code: str, start_index: str = "1.0"):
        """Apply syntax highlighting to Rust code in the text widget."""
        lines = code.split("\n")
        for line_num, line in enumerate(lines):
            line_start = f"{start_index}+{line_num}lines linestart"

            # Apply patterns (order matters - later patterns can override)
            for token_name, pattern in COMPILED_PATTERNS:
                for match in pattern.finditer(line):
                    s, e = match.start(), match.end()
                    tag_start = f"{line_start}+{s}chars"
                    tag_end = f"{line_start}+{e}chars"
                    text_widget.tag_add(f"syn_{token_name}", tag_start, tag_end)

    @staticmethod
    def format_with_line_numbers(code: str) -> list[tuple[str, str]]:
        """Format code with line numbers, returning (text, tag) pairs."""
        lines = code.split("\n")
        width = len(str(len(lines)))
        result = []
        for i, line in enumerate(lines, 1):
            num_str = f" {i:>{width}} │ "
            result.append((num_str, "line_number"))
            result.append((line + "\n", "normal"))
        return result


class CompileErrorFormatter:
    """Formats simulated or real cargo compile errors with visual structure."""

    # Patterns to detect error components
    ERROR_PATTERN = re.compile(r"^error(?:\[E\d+\])?: (.+)$")
    WARNING_PATTERN = re.compile(r"^warning(?:\[E\d+\])?: (.+)$")
    LOCATION_PATTERN = re.compile(r"^\s*--> (.+):(\d+):(\d+)$")
    PIPE_PATTERN = re.compile(r"^\s*\d*\s*\|")
    HELP_PATTERN = re.compile(r"^\s*= help: (.+)$")
    NOTE_PATTERN = re.compile(r"^\s*= note: (.+)$")

    @staticmethod
    def format_error_output(raw_output: str) -> list[tuple[str, OutputType]]:
        """Parse cargo error output and return formatted (text, type) pairs."""
        lines = raw_output.split("\n")
        result = []

        for line in lines:
            stripped = line.rstrip()
            if not stripped:
                result.append(("", OutputType.NORMAL))
                continue

            if CompileErrorFormatter.ERROR_PATTERN.match(stripped):
                result.append((stripped, OutputType.ERROR))
            elif CompileErrorFormatter.WARNING_PATTERN.match(stripped):
                result.append((stripped, OutputType.WARNING))
            elif CompileErrorFormatter.LOCATION_PATTERN.match(stripped):
                result.append((stripped, OutputType.INFO))
            elif CompileErrorFormatter.HELP_PATTERN.match(stripped):
                result.append((stripped, OutputType.SUCCESS))
            elif CompileErrorFormatter.NOTE_PATTERN.match(stripped):
                result.append((stripped, OutputType.SYSTEM))
            elif CompileErrorFormatter.PIPE_PATTERN.match(stripped):
                # Source code lines with pipe - check for error markers
                if "^" in stripped or "~" in stripped:
                    result.append((stripped, OutputType.ERROR))
                else:
                    result.append((stripped, OutputType.INFO))
            elif stripped.startswith("error") or stripped.startswith("warning"):
                otype = OutputType.ERROR if stripped.startswith("error") else OutputType.WARNING
                result.append((stripped, otype))
            else:
                result.append((stripped, OutputType.NORMAL))

        return result

    @staticmethod
    def generate_sample_error(project_name: str = "my_project") -> str:
        """Generate a sample Rust compile error for demonstration."""
        return """error[E0308]: mismatched types
 --> src/main.rs:5:20
  |
5 |     let x: i32 = "hello";
  |            ---   ^^^^^^^ expected `i32`, found `&str`
  |            |
  |            expected due to this
  |
  = help: try using a conversion method: `"hello".parse::<i32>()`

error[E0425]: cannot find value `y` in this scope
 --> src/main.rs:8:20
  |
8 |     println!("{}", y);
  |                      ^ not found in this scope
  |
  = help: consider declaring a variable: `let y = ...;`

warning: unused variable: `x`
 --> src/main.rs:5:9
  |
5 |     let x: i32 = "hello";
  |         ^ help: if this is intentional, prefix it with an underscore: `_x`
  |
  = note: `#[warn(unused_variables)]` on by default

error: aborting due to 2 previous errors; 1 warning emitted

For more information about this error, try `rustc --explain E0308`."""

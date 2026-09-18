"""AI: Text manipulation utilities for shifting, indenting, and clipboard operations on source text."""

import re
import subprocess
import sys
import tempfile
from pathlib import Path

import pyperclip


class TextUtils:
    """AI: Text manipulation utilities for shifting, indenting, and clipboard operations on source text."""

    __PRECEDING_SPACES_PATTERN = re.compile(r"([\t\s]*)")

    @staticmethod
    def shift_left(text: str, shift: int, start_line: int = 0) -> str:
        """Shifts each line of the given text to the left by the specified number of spaces. Only spaces are shifted."""
        if shift == 0:
            return text
        pattern = re.compile(r"\s{0," + str(shift) + "}(.*)")
        lines = text.split("\n")
        for idx, line in enumerate(lines[start_line:]):
            lines[idx + start_line] = pattern.sub(r"\1", line)
        return "\n".join(lines)

    @staticmethod
    def correct_indent(text: str, indent: int, depth: int = 0) -> str:
        """Shifts each line of the given text to the left by the specified number of spaces. Only spaces are shifted."""
        lines = text.split("\n")
        for idx, line in enumerate(lines):
            depth -= line.count("}")
            stripped = re.sub(r"^\s*", "", line)
            lines[idx] = " " * depth * indent + stripped if stripped else stripped
            depth += line.count("{")

        return "\n".join(lines)

    @staticmethod
    def strip_indent(text: str, start_line: int = 0) -> str:
        """Shift the text left so the first line has no leading spaces.

        All other lines are shifted left by the same amount.
        """
        matcher = TextUtils.__PRECEDING_SPACES_PATTERN.search(text)
        if matcher:
            spaces = matcher[1]
            text = TextUtils.shift_left(text, len(spaces), start_line)
        return text.strip()

    @staticmethod
    def shift_right(text: str, shift: int, start_line: int = 0) -> str:
        """Shifts each line of the given text to the left by the specified number of spaces. Only spaces are shifted."""
        if shift == 0:
            return text
        lines = text.split("\n")
        spaces = " " * shift
        for idx, line in enumerate(lines[start_line:]):
            lines[idx + start_line] = spaces + line if line else line
        return "\n".join(lines)

    @staticmethod
    def get_indent(content: bytes, offset: int) -> int:
        """Calculate the indentation level of a line in a byte string.

        Args:
            content (bytes): The byte string containing the text.
            offset (int): The position within the byte string to start calculating the indentation from.

        Returns:
            int: The number of leading whitespace characters (tabs or spaces) from the start of the line to the given offset.

        """
        indent = offset
        while indent > 1:
            if content[indent - 1] in b"\n\r":
                break
            indent -= 1
        start_of_line = indent
        while indent < offset:
            if content[indent] not in b"\t ":
                break
            indent += 1
        return indent - start_of_line

    @staticmethod
    def get_spaces_before(content: bytes, offset: int) -> int:
        """Calculate the indentation level of a line in a byte string.

        Args:
            content (bytes): The byte string containing the text.
            offset (int): The position within the byte string to start calculating the indentation from.

        Returns:
            int: The number of leading whitespace characters (tabs or spaces) from the start of the line to the given offset.

        """
        indent = offset - 1
        while indent > 0:
            if content[indent] not in b" \t":
                break
            indent -= 1
        return offset - indent - 1

    @staticmethod
    def to_clipboard(text: str) -> None:
        """AI: Copy the given text to the system clipboard."""
        pyperclip.copy(text)

    @staticmethod
    def to_file(filename: str, text: str) -> None:
        """Write the given text to a file with the specified filename."""
        with Path(filename).open("w") as f:
            f.write(text)


def signature_to_id(signature: str) -> str:
    """AI: Derive a short, filesystem/identifier-safe id from a node signature."""
    text = signature.replace("\n", " ")
    return re.sub(r"[^\w\s]", "", text)[:30]  # Remove punctuation, limit length


def snake_case(snippet: str) -> str:
    """Convert a camelCase or PascalCase string to snake_case, preserving acronyms as single words.

    Leaves a string already in snake_case unchanged.
    """
    snippet = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", snippet)
    snippet = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", snippet)
    return snippet.lower()


def fix_indent(code_string: str) -> str | None:
    """AI: Reformat code_string's indentation by round-tripping it through a temporary file and an external formatter."""
    with tempfile.NamedTemporaryFile(suffix=".py", mode="w+", delete=False) as temp_file:
        file_path = temp_file.name
        temp_file.write(code_string)

    try:
        if not Path(file_path).is_file():
            print(f"Error: {file_path} does not exist.")
            return None

        # Step 1: Run flake8 to show issues
        print("Running flake8...")
        subprocess.run([sys.executable, "-m", "flake8", file_path])

        # Step 2: Auto-fix with autopep8
        print("Auto-fixing with autopep8...")
        subprocess.run(
            [
                sys.executable,
                "-m",
                "autopep8",
                "--in-place",
                "--aggressive",
                "--aggressive",
                file_path,
            ],
        )

        # Step 3: Run flake8 again to verify
        print("Re-running flake8 after fixes...")
        subprocess.run([sys.executable, "-m", "flake8", file_path])

        # Read the fixed code
        with Path(file_path).open() as file:
            fixed_code = file.read()

        # black format
        # return format_str(fixed_code, mode=FileMode())
        return fixed_code
    except Exception as e:
        print(f"Error formatting code: {e}")
    finally:
        # Clean up the temporary file
        if Path(file_path).exists():
            Path(file_path).unlink()

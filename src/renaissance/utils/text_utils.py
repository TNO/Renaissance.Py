import os
import re
import subprocess
import sys
import tempfile

import pyperclip


class TextUtils:
    __PRECEDING_SPACES_PATTERN = re.compile(r"([\t\s]*)")

    @staticmethod
    def shift_left(text: str, shift: int, start_line: int = 0) -> str:
        """Shifts each line of the given text to the left by the specified number of spaces. Only spaces are shifted"""
        if shift == 0:
            return text
        pattern = re.compile(r"\s{0," + str(shift) + "}(.*)")
        lines = text.split("\n")
        for idx, line in enumerate(lines[start_line:]):
            lines[idx + start_line] = pattern.sub(r"\1", line)
        return "\n".join(lines)

    @staticmethod
    def correct_indent(text: str, indent: int, depth: int = 0) -> str:
        """Shifts each line of the given text to the left by the specified number of spaces. Only spaces are shifted"""
        lines = text.split("\n")
        for idx, line in enumerate(lines):
            depth -= line.count("}")
            lines[idx] = " " * depth * indent + re.sub(r"^\s*", "", line)
            depth += line.count("{")

        return "\n".join(lines)

    @staticmethod
    def strip_indent(text: str, start_line: int = 0) -> str:
        """Shifts left the text such that the first line has no leading spaces and all other lines shifted left with the first line spaces length."""
        matcher = TextUtils.__PRECEDING_SPACES_PATTERN.search(text)
        if matcher:
            spaces = matcher[1]
            text = TextUtils.shift_left(text, len(spaces), start_line)
        return text.strip()

    @staticmethod
    def shift_right(text: str, shift: int, start_line: int = 0) -> str:
        """Shifts each line of the given text to the left by the specified number of spaces. Only spaces are shifted"""
        if shift == 0:
            return text
        lines = text.split("\n")
        spaces = " " * shift
        for idx, line in enumerate(lines[start_line:]):
            lines[idx + start_line] = spaces + line
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
        pyperclip.copy(text)

    @staticmethod
    def to_file(filename: str, text: str) -> None:
        """Write the given text to a file with the specified filename."""
        with open(filename, "w") as f:
            f.write(text)


def signature2id(signature: str) -> str:
    text = signature.replace("\n", " ")
    return re.sub(r"[^\w\s]", "", text)[:30]  # Remove punctuation, limit length


def camel_case(snippet: str) -> str:
    parts = snippet.split("_")
    return parts[0] + "".join(word.capitalize() for word in parts[1:])


def snake_case(snippet: str) -> str:
    """Convert a PascalCase/camelCase identifier to snake_case.

    Splits on two kinds of word boundary: an acronym followed by a word
    (e.g. "HTMLParser" -> "HTML_Parser"), and a lowercase letter followed
    by an uppercase letter (e.g. "TypeVarCheck" -> "Type_Var_Check"). A
    digit does not trigger a split, so "Unit2Pytest" stays "unit2pytest".
    """
    s1 = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", snippet)
    s2 = re.sub(r"([a-z])([A-Z])", r"\1_\2", s1)
    return s2.lower()


def fix_indent(code_string: str) -> str | None:
    with tempfile.NamedTemporaryFile(suffix=".py", mode="w+", delete=False) as temp_file:
        file_path = temp_file.name
        temp_file.write(code_string)

    try:
        if not os.path.isfile(file_path):
            print(f"Error: {file_path} does not exist.")
            return

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
            ]
        )

        # Step 3: Run flake8 again to verify
        print("Re-running flake8 after fixes...")
        subprocess.run([sys.executable, "-m", "flake8", file_path])

        # Read the fixed code
        with open(file_path) as file:
            fixed_code = file.read()

        # black format
        # return format_str(fixed_code, mode=FileMode())
        return fixed_code
    except Exception as e:
        print(f"Error formatting code: {e}")
    finally:
        pass
        # Clean up the temporary file
        if os.path.exists(file_path):
            os.remove(file_path)

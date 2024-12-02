
import re

import pyperclip


class TextUtils:

    __PRECEDING_SPACES_PATTERN = re.compile(r"([\t\s]*)")

    @staticmethod
    def shift_left(text: str, shift: int, start_line=0):
        """
        Shifts each line of the given text to the left by the specified number of spaces. Only spaces are shifted
        """
        if shift == 0:
            return text
        pattern = re.compile(r'\s{0,'+str(shift)+'}(.*)')
        lines = text.split('\n')
        for idx, line in enumerate(lines[start_line:]):
            lines[idx+start_line] = pattern.sub(r'\1', line)
        return '\n'.join(lines)

    @staticmethod
    def correct_indent(text: str, indent: int, depth=0):
        """
        Shifts each line of the given text to the left by the specified number of spaces. Only spaces are shifted
        """
        lines = text.split('\n')
        for idx, line in enumerate(lines):
            depth -= line.count('}')
            lines[idx] = ' '*depth*indent + re.sub(r'^\s*', '', line)
            depth += line.count('{')

        return '\n'.join(lines)


    @staticmethod
    def strip_indent(text: str, start_line = 0):
        """
        Shifts left the text such that the first line has no leading spaces and all other lines shifted left with the first line spaces length.
        """
        matcher = TextUtils.__PRECEDING_SPACES_PATTERN.search(text)
        if matcher:
            spaces = matcher[1]
            text = TextUtils.shift_left(text, len(spaces), start_line)
        return text.strip()

    @staticmethod
    def shift_right(text: str, shift: int, start_line=0):
        """
        Shifts each line of the given text to the left by the specified number of spaces. Only spaces are shifted
        """
        if shift == 0:
            return text
        lines = text.split('\n')
        spaces = ' ' * shift
        for idx, line in enumerate(lines[start_line:]):
            lines[idx+start_line] = spaces + line
        return '\n'.join(lines)

    @staticmethod
    def get_indent(content: bytes, offset):
        """
        Calculate the indentation level of a line in a byte string.

        Args:
            content (bytes): The byte string containing the text.
            offset (int): The position within the byte string to start calculating the indentation from.

        Returns:
            int: The number of leading whitespace characters (tabs or spaces) from the start of the line to the given offset.
        """
        indent = offset
        while indent > 1:
            if content[indent-1] in b'\n\r':
                break
            indent -= 1
        start_of_line =  indent
        while indent < offset:
            if content[indent] not in b'\t ':
                break
            indent += 1
        return indent - start_of_line
    
    @staticmethod
    def get_spaces_before(content: bytes, offset):
        """
        Calculate the indentation level of a line in a byte string.

        Args:
            content (bytes): The byte string containing the text.
            offset (int): The position within the byte string to start calculating the indentation from.

        Returns:
            int: The number of leading whitespace characters (tabs or spaces) from the start of the line to the given offset.
        """
        indent = offset - 1
        while indent > 0:
            if not content[indent] in b' \t':
                break
            indent -= 1
        return offset - indent - 1
    
    @staticmethod
    def to_clipboard(text:str):
        pyperclip.copy(text)

    @staticmethod
    def to_file(filename:str, text:str):
        with open(filename  , 'w') as f:
            f.write(text)   

import os
import subprocess
import sys
import tempfile

import black

def fix_indent(code_string):
    with tempfile.NamedTemporaryFile(suffix='.py', mode='w+', delete=False) as temp_file:
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
        subprocess.run([
            sys.executable, "-m", "autopep8",
            "--in-place", "--aggressive", "--aggressive", file_path
        ])

        # Step 3: Run flake8 again to verify
        print("Re-running flake8 after fixes...")
        subprocess.run([sys.executable, "-m", "flake8", file_path])

        # Read the fixed code
        with open(file_path, 'r') as file:
            fixed_code = file.read()

        #black format
        # return format_str(fixed_code, mode=FileMode())
        return fixed_code
    except Exception as e:
        print(f"Error formatting code: {e}")
    finally:
        pass
        # Clean up the temporary file
        if os.path.exists(file_path):
            os.remove(file_path)

def add_indent(code, spaces=4):
    # Create the indentation string
    indent = ' ' * spaces

    # Split the code into lines
    lines = code.splitlines()

    # If there's only one line or no lines, return the original code
    if len(lines) <= 1:
        return code

    # Keep the first line unchanged, add indentation to the rest
    indented_lines = [lines[0]] + [indent + line for line in lines[1:]]
    indented_code = '\n'.join(indented_lines)

    return indented_code

def is_block_statement(statement):
    """
    Check if a given statement is an if, with, or try statement that requires indentation.

    Args:
        statement (str): The Python statement to check

    Returns:
        bool: True if the statement is an if, with, or try statement, False otherwise

    Examples:
        >>> is_block_statement("if x > 5:")
        True
        >>> is_block_statement("with open('file.txt') as f:")
        True
        >>> is_block_statement("try:")
        True
        >>> is_block_statement("x = 5")
        False
    """
    # Strip whitespace and comments
    statement = statement.strip()
    if '#' in statement:
        statement = statement[:statement.find('#')].strip()

    # Check if the statement is empty after stripping
    if not statement:
        return False

    # Check for if, elif, else statements
    if statement.startswith('if ') and statement.endswith(':'):
        return True
    if statement.startswith('elif ') and statement.endswith(':'):
        return True
    if statement == 'else:':
        return True

    # Check for with statements
    if statement.startswith('with ') and statement.endswith(':'):
        return True

    # Check for try, except, finally statements
    if statement == 'try:':
        return True
    if statement.startswith('except') and statement.endswith(':'):
        return True
    if statement == 'finally:':
        return True

    # Check for loops
    if statement.startswith('for ') and statement.endswith(':'):
        return True
    if statement.startswith('while ') and statement.endswith(':'):
        return True

    # Check for function and class definitions
    if statement.startswith('def ') and statement.endswith(':'):
        return True
    if statement.startswith('class ') and statement.endswith(':'):
        return True

    return False
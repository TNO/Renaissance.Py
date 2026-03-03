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
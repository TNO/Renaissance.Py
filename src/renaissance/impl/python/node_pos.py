import libcst as cst
from libcst.metadata import MetadataWrapper, PositionProvider

source_code = """
x = 42
y = x + 10
print(y)
"""

# Create metadata wrapper
module = cst.parse_module(source_code)
wrapper = MetadataWrapper(module)

# Resolve positions
positions = wrapper.resolve(PositionProvider)

# Access specific nodes directly
for statement in module.body:
    if isinstance(statement, cst.SimpleStatementLine):
        # Get position of the statement
        pos = positions.get(statement)
        if pos:
            print(f"Statement at Line {pos.start.line}: {statement}")
            print(f"  Start: Line {pos.start.line}, Column {pos.start.column}")
            print(f"  End: Line {pos.end.line}, Column {pos.end.column}")
            print()


def find_node_at_position(source_code: str, target_line: int, target_column: int):
    """Find the CST node at a specific line and column"""
    module = cst.parse_module(source_code)
    wrapper = MetadataWrapper(module)
    positions = wrapper.resolve(PositionProvider)

    def search_node(node):
        """Recursively search for node at target position"""
        if node in positions:
            pos = positions[node]
            # Check if target position is within this node's range
            if (pos.start.line <= target_line <= pos.end.line and
                    pos.start.column <= target_column <= pos.end.column):

                # Try to find a more specific child node
                for child in node.children:
                    result = search_node(child)
                    if result:
                        return result

                # If no child matches, return this node
                return node, pos

        return None

    return search_node(module)


# Example usage
source = """
def calculate(a, b):
    result = a + b
    return result
"""

# Find node at line 2, column 4 (the 'result' variable)
found = find_node_at_position(source, 2, 4)
if found:
    node, position = found
    print(f"Found node: {type(node).__name__}")
    print(f"Code: {node}")
    print(f"Position: Line {position.start.line}, Col {position.start.column}")


def extract_code_by_position(source_code: str):
    """Extract actual code snippets using position metadata"""
    lines = source_code.split('\n')

    module = cst.parse_module(source_code)
    wrapper = MetadataWrapper(module)
    positions = wrapper.resolve(PositionProvider)

    results = []

    def extract_from_node(node):
        if node in positions:
            pos = positions[node]

            # Extract the actual source code for this node
            if pos.start.line == pos.end.line:
                # Single line
                code_snippet = lines[pos.start.line - 1][pos.start.column:pos.end.column]
            else:
                # Multi-line
                code_parts = []
                for line_num in range(pos.start.line, pos.end.line + 1):
                    if line_num == pos.start.line:
                        code_parts.append(lines[line_num - 1][pos.start.column:])
                    elif line_num == pos.end.line:
                        code_parts.append(lines[line_num - 1][:pos.end.column])
                    else:
                        code_parts.append(lines[line_num - 1])
                code_snippet = '\n'.join(code_parts)

            results.append({
                'node_type': type(node).__name__,
                'position': f"L{pos.start.line}:C{pos.start.column}-L{pos.end.line}:C{pos.end.column}",
                'code': code_snippet.strip()
            })

        for child in node.children:
            extract_from_node(child)

    extract_from_node(wrapper.module)
    return results


# Usage
source = """
def add(x, y):
    return x + y
"""
if __name__ == '__main__':
    print(f"Code POS: \n")
    snippets = extract_code_by_position(source)
    for snippet in snippets[:5]:  # Show first 5
        print(f"{snippet['node_type']} at {snippet['position']}")
        print(f"Code: {snippet['code']}\n")
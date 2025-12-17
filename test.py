import tree_sitter_python as tspython
from tree_sitter import Language, Parser

PY_LANGUAGE = Language(tspython.language())

parser = Parser(PY_LANGUAGE)
tree = parser.parse(
    bytes(
        """
def foo():
    if bar:
        baz()
""",
        "utf8",
    )
)

print("Root node type:", tree.root_node.type)
print("Root node start point:", tree.root_node.start_point)
print("Root node end point:", tree.root_node.end_point)
print("Root node is named:", tree.root_node.is_named)
print("Root node start byte:", tree.root_node.start_byte)
print("Root node end byte:", tree.root_node.end_byte)
print("Root node children:")
for child in tree.root_node.children:
    print(f"  - {child.type} ({child.start_point} to {child.end_point})")
    print(f"    Signature: {tree.root_node.text[child.start_byte:child.end_byte]}")
    print(f"    Is named: {child.is_named}")
    print(f"    Start byte: {child.start_byte}, End byte: {child.end_byte}")
print("Full source code:")
print(tree.root_node.text.decode("utf8"))
print("Full source code with offsets:")
for child in tree.root_node.children:
    print(f"  - {child.type} ({child.start_byte}:{child.end_byte})")
    print(f"    Signature: {tree.root_node.text[child.start_byte:child.end_byte]}")
    print(f"    Start point: {child.start_point}, End point: {child.end_point}")
    print(f"    Is named: {child.is_named}")

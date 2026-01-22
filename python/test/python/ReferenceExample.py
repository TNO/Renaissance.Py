import ast


# Sample code with attribute access
code = """
class Person:
    def __init__(self):
        self.name = "John"
        self.age = 30

person = Person()
print(person.name)  # Attribute access
person.age = 31     # Attribute assignment
self.work()
"""

# Parse the code into an AST
tree = ast.parse(code)


# Function to find and analyze attribute access
def analyze_attributes(node):
    results = []

    class AttributeVisitor(ast.NodeVisitor):
        def visit_Attribute(self, node):
            ctx_type = type(node.ctx).__name__
            results.append({
                'object': ast.unparse(node.value),
                'attribute': node.attr,
                'context': ctx_type,  # Load, Store, or Del
                'line': getattr(node, 'lineno', 'unknown'),
                'col': getattr(node, 'col_offset', 'unknown'),
                'full_expression': ast.unparse(node)
            })
            self.generic_visit(node)

    visitor = AttributeVisitor()
    visitor.visit(node)
    return results


# Analyze the code
attributes = analyze_attributes(tree)

# Print the results
for i, attr in enumerate(attributes, 1):
    print(f"\nAttribute Access {i}:")
    print(f"  Object: {attr['object']}")
    print(f"  Attribute: {attr['attribute']}")
    print(f"  Context: {attr['context']}")
    print(f"  Full Expression: {attr['full_expression']}")
    print(f"  Location: line {attr['line']}, col {attr['col']}")

# If you have astpretty installed, you can see the structure of one attribute node
try:

    print("\nExample AST structure of an Attribute node:")
    # Find a simple attribute access node
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute) : #or isinstance(node, ast.Call) : #and isinstance(node.value, ast.Name):
            print(ast.dump(node))
            # break
except ImportError:
    print("\nInstall astpretty for prettier AST printing: pip install astpretty")
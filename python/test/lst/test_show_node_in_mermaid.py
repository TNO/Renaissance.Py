import tree_sitter_python as tspython
import tree_sitter_cpp as tscpp
import tree_sitter_java as tsjava

from impl.tree_sitter_adapter.tree_sitter_adapter import TreeSitterAdapter
from visualizers.lst_mermaid_visualizer import LSTMermaidVisualizer


def process_code(language_name, grammar_module, code):
    print(f"\n==== {language_name.upper()} ====")
    print(f"\n==== {grammar_module} ====")
    adapter = TreeSitterAdapter(grammar_module)
    tree = adapter.parse_code(code)
    lst = adapter.to_lst(code, tree)

    visualizer = LSTMermaidVisualizer()
    mermaid = visualizer.render(lst)
    print(mermaid)

    with open(f"lst_output_{language_name.upper()}.md", "w", encoding="utf-8") as f:
        f.write("```mermaid\n")
        f.write(mermaid)
        f.write("\n```")


def test_create_diagrams():
    code_py = "def foo():\n    return 42"
    code_cpp = "int main() { return 0; }"
    code_java = "public class Test { public static void main(String[] args) {} }"

    process_code("python", tspython, code_py)
    process_code("cpp", tscpp, code_cpp)
    process_code("java", tsjava, code_java)

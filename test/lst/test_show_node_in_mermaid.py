import textwrap

import pytest
import tree_sitter_cpp as tscpp
import tree_sitter_java as tsjava
import tree_sitter_python as tspython
from hamcrest import assert_that, empty, is_not

from renaissance.integrations.tree_sitter.adapter import TreeSitterAdapter
from renaissance.integrations.tree_sitter.visualizer import LstVisualizer


class TestShowNodeInMermaid:
    def process_code(self, grammar_module, code):
        adapter = TreeSitterAdapter(grammar_module)
        tree = adapter.parse_code(code)
        lst = adapter.to_lst(code, tree)
        visualizer = LstVisualizer()
        mermaid = visualizer.render(lst)
        return mermaid

    @pytest.mark.parametrize(
        "raw, module",
        [
            ("def foo():\n    return 42", tspython),
            ("int main() { return 0; }", tscpp),
            ("public class Test { public static void main(String[] args) {} }", tsjava),
        ],
    )
    def test_create_diagrams(self, raw, module):
        result = self.process_code(module, raw)
        # with open(f"lst_output_{module.__name__}.mmd", "w", encoding="utf-8") as f:
        #     f.write(mermaid)
        assert_that(textwrap.dedent(result), is_not(empty()))

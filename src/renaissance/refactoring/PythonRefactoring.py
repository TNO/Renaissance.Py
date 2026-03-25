from renaissance.impl.python import PythonASTNode, PythonPatternFactory
from renaissance.impl.python.python_ast_util import to_str
from renaissance.syntax_tree import ASTFactory, ASTProcessor
from renaissance.syntax_tree.match_finder import match_pattern


class PythonRefactoring(ASTProcessor):
    def __init__(self, file):
        factory = ASTFactory(PythonASTNode, [])
        atu = factory.create(file)
        super().__init__(atu, factory, False)
        self.pattern_factory = PythonPatternFactory(self.factory)

    def replace_stmt(self, find, repl):
        pattern = self.pattern_factory.create_statements(find)
        for match in match_pattern(self.root.children, pattern):
            replacement = repl
            for exp in match.expansions:
                arg_str = ", ".join([to_str(node) for node in match.expansions[exp]])
                replacement = replacement.replace(exp, arg_str)

            replacement = replacement.replace(" ,)", ")").replace(", )", ")")
            self.replace(replacement, match.nodes, False, False)

import os
import textwrap
from typing import Any

from renaissance.impl.python import PythonASTNode, PythonPatternFactory
from renaissance.syntax_tree import ASTRewriter, ASTFactory, ASTFinder, PatternMatch
from renaissance.syntax_tree.match_finder import match_pattern
from renaissance.utils.text_utils import TextUtils


class SimplifyRenaissance:
    def __init__(self, file):
        self.file = file
        self.factory = ASTFactory(PythonASTNode, [])
        self.pattern_factory = PythonPatternFactory(self.factory, None)
        self.atu = self.factory.create(file)
        self.stmts = self.atu.children
        self.rewriter = ASTRewriter(self.atu)

    def raw(self, nodes):
        res = ''
        for node in nodes:
            res += '\n\n    ' + node.text
        return res + '\n    '

    def simplify(self):
        print(f"simplify {self.file}")
        self.replace('unittest.main()', 'pytest.main()')
        self.replace('import unittest', 'import pytest\nfrom hamcrest import *')
        self.replace("factory = ASTFactory(PythonASTNode)\n$atu = factory.create_from_text($code, $name)",
            "PythonASTNode.load_from_text($code, $name)")

    def replace(self, find, repl):
        pattern = self.pattern_factory.create_statements(find)
        for match in match_pattern(self.stmts[-1].body[0].body, pattern):
            replacement = repl
            for exp in match.expansions:
                arg_str = ', '.join([self.to_str(node) for node in match.expansions[exp]])
                replacement = replacement.replace(exp, arg_str)

            replacement = replacement.replace(' ,)', ')').replace(', )', ')')
            self.rewriter.replace(replacement, match.nodes, False, False)

        if self.rewriter.has_changed():
            with open(self.file, 'w') as f:
                f.write(self.rewriter.apply_to_string())
            self.atu = self.factory.create_from_text(self.rewriter.apply_to_string(), self.file)
            self.stmts = self.atu.children
            self.rewriter = ASTRewriter(self.atu)

    def to_str(self, node) -> Any:
        if hasattr(node, 'signature'):
            return node.signature
        else:
            return str(node)


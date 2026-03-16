from renaissance.impl.python import PythonASTNode, PythonPatternFactory
from renaissance.syntax_tree import ASTRewriter, ASTFactory
from renaissance.syntax_tree.match_finder import match_pattern

factory = ASTFactory(PythonASTNode, [])
pattern_factory = PythonPatternFactory(factory, None)
PYUNIT_TEST_CASE_PATTERN = 'def $test_case(self):\n    $$aaa'
PYTEST_REPLACEMENT = 'def $test_case():\n    $$aaa'


class Unit2PyTest:
    def __init__(self, file):
        self.file = file
        self.pattern_factory = PythonPatternFactory(factory, None)
        self.atu = factory.create(file)
        self.stmts = self.atu.children
        self.rewriter = ASTRewriter(self.atu)


    def raw(self, nodes):
        res = ''
        for node in nodes:
            res += '\n\n    ' + node.text
        return res + '\n    '

    def convert_pytest(self):
        print(f"refactoring {self.file}")

        self.convert_test_class()
        self.commit()

        self.replace('import unittest', 'import pytest\nfrom hamcrest import *')
        self.replace('from unittest import $$symbols', 'import pytest\nfrom hamcrest import *')
        self.replace('assert $exp', 'assert_that($exp)')

        self.replace('self.assertTrue($exp)', 'assert_that($exp)')
        self.replace('self.assertFalse($exp)', 'assert_that(not $exp)')
        self.convert_assert('self.assertEqual($exp, $act)', 'assert_that($exp, is_($act))')
        self.convert_assert('self.assertGreaterEqual($exp, $act)', 'assert_that($exp, greater_than_or_equal_to($act))')
        self.convert_assert('self.assertGreater($exp, $act)', 'assert_that($exp, greater_than($act))')
        self.convert_assert('self.assertLesserEqual($exp, $act)', 'assert_that($exp, less_than_or_equal_to($act))')
        self.convert_assert('self.assertLesser($exp, $act)', 'assert_that($exp, less_than($act))')
        self.convert_assert('self.assertIn($act, $exp)', 'assert_that($exp, contain_string($act))')

        # convert_plain_assert_not_empty(pattern_factory, rewriter, atu)
        # convert_plain_assert_same_length(pattern_factory, rewriter, atu)
        # convert_plain_assert_string(pattern_factory, rewriter, atu)

        self.remove_print()

        self.convert_test_setup()
        self.replace('unittest.main()', 'pytest.main()')
        self.commit()

        self.replace('assert_that(isinstance($exp, $act))', 'assert_that($exp, is_($act))')
        self.replace('assert_that(len($exp), $act)', 'assert_that($exp, has_length($act))')
        self.replace('assert_that(len($exp) >= 1)', 'assert_that($exp, is_not(empty()))')
        self.replace('assert_that(len($exp) == $length)', 'assert_that($exp, has_length($length))')
        self.replace('assert_that($exp == $act)', 'assert_that($exp, is_($act))')
        # self.replace('assert_that($exp.startswith($act))', 'assert_that($exp, starts_with($act))')

        self.commit()
        self.convert_parameterized_test()

        with open(self.file, 'w') as f:
            f.write(self.rewriter.apply_to_string())

    def commit(self) -> None:
        if self.rewriter.has_changed():
            with open(self.file, 'w') as f:
                f.write(self.rewriter.apply_to_string())
            self.atu = factory.create_from_text(self.rewriter.apply_to_string(), self.file)
            self.rewriter = ASTRewriter(self.atu)

    def convert_test_class(self):
        test_main = self.pattern_factory.create_statements('class $klass($unittest):\n    $$test_cases\n')
        for match in match_pattern(self.atu.children, test_main):
            klass = match.expansions['$klass'][0]
            if klass.endswith('Test'):
                repl = match.nodes[0].signature.replace(f'{klass}(unittest.TestCase):', f'Test{klass[:-4]}:')
            else:
                repl = match.nodes[0].signature.replace(f'(match):', ':')

            # repl = f'class {match.expansions["$klass"][0]}:\n{raw(match.expansions["$$test_cases"])}'
            self.rewriter.replace(repl, match.nodes, False, False)

    def convert_test_setup(self):
        test_main = pattern_factory.create_statements('def setUp(self): $$stmts')
        for match in match_pattern(self.atu.children, test_main):
            # stmts = self.raw(match.expansions['$$stmts'])
            repl = f'@pytest.fixture(autouse=True)\n{match.nodes[0].signature}'
            self.rewriter.replace(repl, match.nodes, False, False)

    def convert_assert(self, pattern, repl):
        pattern = pattern_factory.create_statements(pattern)
        for match in match_pattern(self.stmts, pattern):
            if match.expansions['$act'][0].kind in ['Constant']:
                act = match.expansions['$act'][0].signature
                exp = match.expansions['$exp'][0].signature
            else:  # original is wrong
                exp = match.expansions['$act'][0].signature
                act = match.expansions['$exp'][0].signature
            repl = repl.replace('$exp', exp).replace('$act', act)
            self.rewriter.replace(repl, match.nodes, False, False)

    def replace(self, find, repl):
        pattern = self.pattern_factory.create_statements(find)
        for match in match_pattern(self.stmts, pattern):
            replacement = repl
            for exp in match.expansions:
                replacement = replacement.replace(exp, match.expansions[exp][0].signature)
            self.rewriter.replace(replacement, match.nodes, False, False)

    def convert_parameterized_test(self):

        unittest = pattern_factory.create_statements(
            '@parameterized.expand($$parameters)\ndef $fun($$args):\n    $$stmts')

        for match in match_pattern(self.stmts, unittest):
            fun = match.nodes[0]
            args = ', '.join([arg.node.arg for arg in match.expansions['$$args']])
            args = args.replace('self, ', '')
            repl = fun.signature.replace('@parameterized.expand(', f'    @pytest.mark.parametrize("{args}",')
            self.rewriter.replace(repl, fun, False, False)

    def remove_print(self):
        print_msg = pattern_factory.create_statements('print($$msg)')
        for match in match_pattern(self.stmts, print_msg):
            if len(match.nodes[0].parent.parent.body) == 1:
                self.rewriter.remove([match.nodes[0].parent.parent], False, False)
            else:
                self.rewriter.remove(match.nodes, False, False)

    # def raw(nodes):
    #     res = ''
    #     for node in nodes:
    #         if isinstance(node, PythonASTNode):
    #             res += node.signature + '\n        '
    #         else:
    #             res += str(node)
    #     return res #+ '\n'

from hamcrest import assert_that

from renaissance.impl.python import PythonASTNode, PythonPatternFactory
from renaissance.syntax_tree import ASTRewriter, ASTFactory, ASTFinder
from renaissance.syntax_tree.match_finder import match_pattern
from renaissance.utils.text_utils import TextUtils

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

        # 1: file level changes
        self.replace('unittest.main()', 'pytest.main()')
        self.convert_test_class()
        self.replace('import unittest', 'import pytest\nfrom hamcrest import *')
        self.replace('from parameterized import parameterized', 'import pytest\nfrom hamcrest import *')


        self.replace('from unittest import $$symbols', 'import pytest\nfrom hamcrest import *')
        self.commit()

        # 2: class level changes
        self.convert_parameterized_test()
        self.convert_test_setup()
        self.commit()

        # 3: function level changes

        self.replace('assert $stmt, $$msg','assert_that($stmt, is_(True), $$msg)')
        self.replace('self.assertTrue($exp,$$msg)', 'assert_that($exp, is_(True), $$msg)')
        self.replace('self.assertFalse($exp, $$msg)', 'assert_that($exp, is_(False), $$msg)')

        self.convert_assert('self.assertEqual($exp, $act)', 'assert_that($exp, is_($act))')
        self.convert_assert('self.assertGreaterEqual($exp, $act)', 'assert_that($exp, greater_than_or_equal_to($act))')
        self.convert_assert('self.assertGreater($exp, $act)', 'assert_that($exp, greater_than($act))')
        self.convert_assert('self.assertLesserEqual($exp, $act)', 'assert_that($exp, less_than_or_equal_to($act))')
        self.convert_assert('self.assertLesser($exp, $act)', 'assert_that($exp, less_than($act))')
        self.convert_assert('self.assertMultiLineEqual($act, $exp)', 'assert_that($act, is_($exp))')

        self.replace('self.assertIn($act, $exp)', 'assert_that($exp, contain_string($act))')
        self.replace('self.assertIsInstance($act, $exp)', 'assert_that($act, is_($exp))')
        self.replace('with self.assertRaises($exception): $call()', 'assert_that(calling($call), raises($exception))')



        #
        self.remove_print()
        self.convert_plain_assert_same_length()

        # 4: improve to mor concise asserts
        while self.rewriter.has_changed():
            self.commit()
            self.replace('assert_that($exp)', 'assert_that($exp, is_(True))')
            self.replace('assert_that(isinstance($exp, $act))', 'assert_that($exp, is_($act))')
            self.replace('assert_that(len($exp), $act)', 'assert_that($exp, has_length($act))')
            self.replace('assert_that(len($exp) >= 1)', 'assert_that($exp, is_not(empty()))')
            self.replace('assert_that(len($exp) >= 1, is_(True))', 'assert_that($exp, is_not(empty()))')
            self.replace('assert_that(len($exp) == $length)', 'assert_that($exp, has_length($length))')
            self.replace('assert_that($exp == $act)', 'assert_that($exp, is_($act))')
            self.replace('assert_that($exp == $act, is_(True))', 'assert_that($exp, is_($act))')
            self.replace('assert_that(not $stmt, is_(True), $$msg)', 'assert_that($stmt, is_(False) ,$$msg)')
            self.replace('assert_that($stmt, is_not(True), $$msg)', 'assert_that($stmt, is_(False) ,$$msg)')
            self.replace('assert_that(not $stmt)', 'assert_that($stmt, is_(False))')
            self.replace('assert_that($element in $collection, is_(True))', 'assert_that($collection, contains_exactly($element))')
            self.replace('assert_that($exp, has_length(is_($act)))', 'assert_that($exp, has_length($act))')
            self.swap_expected_and_actual()
            self.convert_skip_test()

        # self.replace('assert_that(not $stmt)', 'assert_that($stmt, is_(False))')
        # self.replace('assert_that($exp.startswith($act))', 'assert_that($exp, starts_with($act))')


        self.commit()

    def commit(self) -> None:
        if self.rewriter.has_changed():
            with open(self.file, 'w') as f:
                f.write(self.rewriter.apply_to_string())
            self.atu = factory.create_from_text(self.rewriter.apply_to_string(), self.file)
            self.stmts = self.atu.children
            self.rewriter = ASTRewriter(self.atu)

    def convert_test_class(self):
        test_main = self.pattern_factory.create_statements('class $klass($test_class):\n    $$test_cases\n')
        for match in match_pattern(self.atu.children, test_main):
            klass = match.expansions['$klass'][0]
            test_class = match.expansions['$test_class'][0].signature
            if test_class.endswith('TestCase'):
                if klass.endswith('Test'):
                    repl = match.nodes[0].signature.replace(f'{klass}({test_class}):', f'Test{klass[:-4]}:')
                else:
                    repl = match.nodes[0].signature.replace(f'({test_class}):', ':')

                # repl = f'class {match.expansions["$klass"][0]}:\n{raw(match.expansions["$$test_cases"])}'
                self.rewriter.replace(repl, match.nodes, False, False)

    def convert_test_setup(self):
        test_main = pattern_factory.create_statements('def setUp(self): $$stmts')
        for match in match_pattern(self.atu.children, test_main):
            # stmts = self.raw(match.expansions['$$stmts'])
            repl = f'@pytest.fixture(autouse=True)\n{match.nodes[0].signature}'
            self.rewriter.replace(repl, match.nodes, False, False)

    def convert_assert(self, pattern, replacement):
        pattern = pattern_factory.create_statements(pattern)
        for match in match_pattern(self.stmts, pattern):
            repl = replacement
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
                if len(match.expansions[exp])==1:
                    if hasattr(match.expansions[exp][0],'signature'):
                        replacement = replacement.replace(exp, match.expansions[exp][0].signature)
                    else:
                        replacement = replacement.replace(exp, match.expansions[exp][0])
                else:
                    replacement = replacement.replace(exp, ', '.join(match.expansions[exp]))
            replacement = replacement.replace(' ,)',')').replace(', )',')')
            self.rewriter.replace(replacement, match.nodes, False, False)

    def convert_parameterized_test(self):

        unittest = pattern_factory.create_statements(
            '@parameterized.expand($$parameters)\ndef $fun($$args):\n    $$stmts')

        for match in match_pattern(self.stmts, unittest):
            fun = match.nodes[0]
            args = ', '.join([arg.node.arg for arg in match.expansions['$$args']])
            args = args.replace('self, ', '')
            repl = fun.signature
            if '    def ' in repl:
                repl = repl.replace('@parameterized.expand(', f'    @pytest.mark.parametrize("{args}",')
                repl = TextUtils.strip_indent(repl)
            else:
                repl = repl.replace('@parameterized.expand(', f'@pytest.mark.parametrize("{args}",')

            self.rewriter.replace(repl, fun, False, False)

        unittest = pattern_factory.create_statements(
            '@parameterized.expand($$parameters)\n@$$decorator\ndef $fun($$args):\n    $$stmts')

        for match in match_pattern(self.stmts, unittest):
            fun = match.nodes[0]
            args = ', '.join([arg.node.arg for arg in match.expansions['$$args']])
            args = args.replace('self, ', '')
            repl = fun.signature
            if '    def ' in repl:
                repl = repl.replace('@parameterized.expand(', f'    @pytest.mark.parametrize("{args}",')
                repl = repl.replace('@unittest.skip(', f'    @pytest.mark.skip(')
                repl = TextUtils.strip_indent(repl)
            else:
                repl = repl.replace('@parameterized.expand(', f'@pytest.mark.parametrize("{args}",')
                repl = repl.replace('@unittest.skip(', f'@pytest.mark.skip(')
            self.rewriter.replace(repl, fun, False, False)

    # @parameterized.expand(Factories.factories)
    # @pytest.mark.skip("stmt and expr are the same")



    def remove_print(self):
        print_msg = pattern_factory.create_statements('print($$msg)')
        for match in match_pattern(self.stmts, print_msg):
            if len(match.nodes[0].parent.parent.body) == 1:
                self.rewriter.remove([match.nodes[0].parent.parent], False, False)
            else:
                self.rewriter.remove(match.nodes, False, False)


    def convert_plain_assert_same_length(self):

        pattern = pattern_factory.create_statements('$act: int = len($real)\nassert $exp == $act, "$act = " + str($act)')
        for match in match_pattern(self.stmts, pattern):
            repl = 'assert_that($real, has_length($exp), f"length of $real = {len($real)}")'
            real = match.expansions['$real'][0].signature
            if match.expansions['$exp'][0].kind in ['Constant']:
                exp = match.expansions['$exp'][0].signature
            else:  # original is wrong
                exp = match.expansions['$act'][0].signature
            repl = repl.replace('$exp', exp).replace('$real', real)
            self.rewriter.replace(repl, match.nodes, False, False)


    def convert_skip_test(self):

        nodes = ASTFinder.find_kind(self.atu, 'Attribute').to_iterable()
        for node in nodes:
            if node.signature =='unittest.skip':
                self.rewriter.replace('pytest.mark.skip', node, False, False)


    def swap_expected_and_actual(self):
        pattern = pattern_factory.create_statements('assert_that($exp, is_($act))')
        for match in match_pattern(self.stmts, pattern):
            if match.expansions['$exp'][0].kind in ['Constant']:
                repl = 'assert_that($act, is_($exp))'
                act = match.expansions['$act'][0].signature
                exp = match.expansions['$exp'][0].signature
                repl = repl.replace('$exp', exp).replace('$act', act)
                self.rewriter.replace(repl, match.nodes, False, False)

    # def raw(nodes):
    #     res = ''
    #     for node in nodes:
    #         if isinstance(node, PythonASTNode):
    #             res += node.signature + '\n        '
    #         else:
    #             res += str(node)
    #     return res #+ '\n'


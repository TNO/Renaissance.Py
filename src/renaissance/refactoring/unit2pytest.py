import os
import textwrap
from typing import Sequence

from renaissance.impl.python.python_ast_util import convert_function
from renaissance.refactoring.python_refactoring import PythonRefactoring
from renaissance.syntax_tree import ASTFinder
from renaissance.syntax_tree.match_finder import match_pattern, AstProtocol


class Unit2Pytest(PythonRefactoring):
    def __init__(self, file):
        '''hide intenal administration in the parent class so that this class you only deals with specific refactors
        '''
        super().__init__(file)

    def convert_pytest(self):
        '''
        entry point for converting unittest to pytest
        '''


        # 1: file level changes
        self.convert_test_class()
        self.restructure_module()
        self.replace_stmt("unittest.main()", "pytest.main()")
        self.replace_stmt("import unittest", "import pytest\nfrom hamcrest import *")
        self.replace_stmt("from parameterized import parameterized", "import pytest\nfrom hamcrest import *")
        self.replace_stmt("from unittest import TestCase,$$symbols","import pytest\nfrom hamcrest import *")
        self.replace_stmt("from unittest import TestCase", "import pytest\nfrom hamcrest import *")

        # 2: class level changes
        self.convert_parameterized_test()
        self.convert_test_setup()
        self.commit()
        #

        # 3: function level changes

        self.convert_skip_test()
        self.remove_print()
        self.convert_plain_assert_same_length()
        self.commit()
        self.replace_stmt("assert $stmt, $$msg", "assert_that($stmt, is_(True), $$msg)")
        self.replace_stmt("self.assertTrue($exp,$$msg)", "assert_that($exp, is_(True), $$msg)")
        self.replace_stmt("self.assertFalse($exp, $$msg)", "assert_that($exp, is_(False), $$msg)")

        self.convert_assert("self.assertEqual($exp, $act)", "assert_that($exp, is_($act))")
        self.convert_assert(
            "self.assertGreaterEqual($exp, $act)",
            "assert_that($exp, greater_than_or_equal_to($act))",
        )
        self.convert_assert("self.assertGreater($exp, $act)", "assert_that($exp, greater_than($act))")
        self.convert_assert(
            "self.assertLesserEqual($exp, $act)",
            "assert_that($exp, less_than_or_equal_to($act))",
        )
        self.convert_assert("self.assertLesser($exp, $act)", "assert_that($exp, less_than($act))")
        self.convert_assert("self.assertMultiLineEqual($act, $exp)", "assert_that($act, is_($exp))")

        self.replace_stmt("self.assertIn($act, $exp)", "assert_that($exp, contain_string($act))")
        self.replace_stmt("self.assertIsInstance($act, $exp)", "assert_that($act, is_($exp))")
        self.replace_stmt(
            "with self.assertRaises($exception): $call()",
            "assert_that(calling($call), raises($exception))",
        )

        # 4: improve to more concise asserts
        while self.has_changed():
            self.commit()
            self.replace_stmt("assert_that($exp)", "assert_that($exp, is_(True))")
            self.replace_stmt("assert_that(isinstance($exp, $act))", "assert_that($exp, is_($act))")
            self.replace_stmt("assert_that(len($exp), $act)", "assert_that($exp, has_length($act))")
            self.replace_stmt("assert_that(len($exp) >= 1)", "assert_that($exp, is_not(empty()))")
            self.replace_stmt(
                "assert_that(len($exp) >= 1, is_(True))",
                "assert_that($exp, is_not(empty()))",
            )
            self.replace_stmt(
                "assert_that(len($exp) == $length)",
                "assert_that($exp, has_length($length))",
            )
            self.replace_stmt("assert_that($exp == $act)", "assert_that($exp, is_($act), $$msg)")
            self.replace_stmt(
                "assert_that($exp == $act, is_(True), $$msg)",
                "assert_that($exp, is_($act), $$msg)",
            )
            self.replace_stmt(
                "assert_that(not $stmt, is_(True), $$msg)",
                "assert_that($stmt, is_(False) ,$$msg)",
            )
            self.replace_stmt(
                "assert_that($stmt, is_not(True), $$msg)",
                "assert_that($stmt, is_(False) ,$$msg)",
            )
            self.replace_stmt("assert_that(not $stmt)", "assert_that($stmt, is_(False))")
            self.replace_stmt(
                "assert_that($element in $collection, is_(True))",
                "assert_that($collection, contains_exactly($element))",
            )
            self.replace_stmt(
                "assert_that($exp, has_length(is_($act)))",
                "assert_that($exp, has_length($act))",
            )
            self.swap_expected_and_actual()

            self.replace_stmt("assert_that(not $stmt)", "assert_that($stmt, is_(False))")
            self.replace_stmt("assert_that($exp.startswith($act))", "assert_that($exp, starts_with($act))")
            self.remove_duplicate_import("import pytest\nfrom hamcrest import *")
        self.commit()

    def convert_test_class(self):
        test_main: Sequence[AstProtocol] = self.pattern_factory.create_statements("class $klass($test_class):\n    $$test_cases\n")  # type: ignore[assignment]
        for match in match_pattern(self.root.children, test_main):
            klass = match.expansions["$klass"][0]
            test_class = self.signature_of(match,"$test_class")
            if test_class.endswith("TestCase"):
                if klass.endswith("Test"):
                    repl = self.signature_of(match).replace(f"{klass}({test_class}):", f"Test{klass[:-4]}:")
                else:
                    repl = self.signature_of(match).replace(f"({test_class}):", ":")

                # repl = f'class {match.expansions["$klass"][0]}:\n{raw(match.expansions["$$test_cases"])}'
                self.replace(repl, match.nodes, False, False)

    def convert_test_setup(self):
        test_main: Sequence[AstProtocol] = self.pattern_factory.create_statements("def setUp(self): $$stmts")  # type: ignore[assignment]
        children: Sequence[AstProtocol] = self.root.children  # type: ignore[assignment]
        for match in match_pattern(children, test_main):
            # stmts = self.raw(match.expansions['$$stmts'])
            repl = f"@pytest.fixture(autouse=True)\n{match.nodes[0].signature}"
            self.replace(repl, match.nodes, False, False)

    def convert_assert(self, pattern, replacement):
        pat: Sequence[AstProtocol] = self.pattern_factory.create_statements(pattern)  # type: ignore[assignment]
        for match in match_pattern(self.root.children, pat):
            repl = replacement
            if match.expansions["$exp"][0].kind in ["Constant"]:
                exp = match.expansions["$act"][0].signature
                act = match.expansions["$exp"][0].signature
            else:  # original is wrong
                act = match.expansions["$act"][0].signature
                exp = match.expansions["$exp"][0].signature
            repl = repl.replace("$exp", exp).replace("$act", act)
            self.replace(repl, match.nodes, False, False)

    def convert_parameterized_test(self):
        unittest: Sequence[AstProtocol] = self.pattern_factory.create_statements(  # type: ignore[assignment]
            "@parameterized.expand($$parameters)\n@$$decorator\ndef $fun($$args, *$$varg):\n    $$stmts"
        )
        for match in match_pattern(self.root.children, unittest):
            fun = match.nodes[0]
            args = ", ".join([arg.node.arg for arg in match.expansions["$$args"]])
            if varg := match.expansions["$$varg"]:
                args = f"{args}, *{varg[0].signature}"
            args = args.replace("self, ", "")
            repl = fun.signature
            if "    def " in repl:
                repl = repl.replace("@parameterized.expand(", f'    @pytest.mark.parametrize("{args}",')
                repl = repl.replace("@unittest.skip(", f"@pytest.mark.skip(")
                repl = textwrap.dedent(repl)
            else:
                repl = repl.replace("@parameterized.expand(", f'@pytest.mark.parametrize("{args}",')
                repl = repl.replace("@unittest.skip(", f"@pytest.mark.skip(")
            self.replace(repl, fun, False, False)

    def remove_print(self):
        print_msg: Sequence[AstProtocol] = self.pattern_factory.create_statements("print($$msg)")  # type: ignore[assignment]
        for match in match_pattern(self.root.children, print_msg):
            if len(match.nodes[0].parent.parent.body) == 1:
                self.remove([match.nodes[0].parent.parent], False, False)
            else:
                self.remove(match.nodes, False, False)

    def convert_plain_assert_same_length(self):
        pattern: Sequence[AstProtocol] = self.pattern_factory.create_statements('$act: int = len($real)\nassert $exp == $act, "$act = " + str($act)')  # type: ignore[assignment]
        for match in match_pattern(self.root.children, pattern):
            repl = 'assert_that($real, has_length($exp), f"length of $real = {len($real)}")'
            real = match.expansions["$real"][0].signature
            if match.expansions["$exp"][0].kind in ["Constant"]:
                exp = match.expansions["$exp"][0].signature
            else:  # original is wrong
                exp = match.expansions["$act"][0].signature
            repl = repl.replace("$exp", exp).replace("$real", real)
            self.replace(repl, match.nodes, False, False)

    def convert_skip_test(self):

        nodes = ASTFinder.find_kind(self.root, "Attribute")
        for node in nodes:
            if node.signature == "unittest.skip":
                self.replace("pytest.mark.skip", node, False, False)

    def swap_expected_and_actual(self):
        pattern: Sequence[AstProtocol] = self.pattern_factory.create_statements("assert_that($exp, is_($act))")  # type: ignore[assignment]
        for match in match_pattern(self.root.children, pattern):
            if match.expansions["$exp"][0].kind in ["Constant"]:
                repl = "assert_that($act, is_($exp))"
                act = match.expansions["$act"][0].signature
                exp = match.expansions["$exp"][0].signature
                repl = repl.replace("$exp", exp).replace("$act", act)
                self.replace(repl, match.nodes, False, False)

    def restructure_module(self):
        funs = []
        test_classes = []
        for stmt in self.root.children:
            if stmt.kind == "FunctionDef":
                funs.append(stmt)
            elif stmt.kind == "ClassDef" and stmt.name.startswith('Test'):
                test_classes.append(stmt)

        if len(funs) > 0:
            if len(test_classes) < 1:

                cls = f"class {self.convert_file_to_test_class()}:\n"
                for fun in funs:

                    cls += textwrap.indent(convert_function(fun), "    ")
                self.replace(cls, funs)
            else:
                for fun in funs:
                    # assuming the class comes first
                    meth = convert_function(fun)
                    self.insert_after(meth, test_classes[-1].body[-1])
                    self.remove(fun)
            self.commit()
            function_call = [self.pattern_factory.create_expression(f"{fun.name}($$args)")]
            for call in match_pattern(self.root.children, function_call):
                sig = call.nodes[0].signature
                self.replace(f"self.{sig}", call.nodes, False, False)
            self.commit()

    def convert_file_to_test_class(self):
        stem = os.path.splitext(os.path.basename(self.filename))[0]
        parts = stem.split("_")
        if parts[-1].lower() == "test":
            parts = parts[:-1]
        name = "".join(word.capitalize() for word in parts)
        return name if name.startswith("Test") else f"Test{name}"

    def remove_duplicate_import(self, import_str):
        import_stmt: Sequence[AstProtocol] = self.pattern_factory.create_statements(import_str)  # type: ignore[assignment]
          # type: ignore[assignment]
        duplicate_imports = match_pattern(self.root.body, import_stmt)

        for match in duplicate_imports[1:-1]:
            self.remove(match.nodes, False, False)

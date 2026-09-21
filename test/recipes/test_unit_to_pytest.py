"""Tests for the UnitToPytest recipe."""

import textwrap
from pathlib import Path

from hamcrest import assert_that, contains_string, ends_with, is_, not_

import targets
from renaissance.integrations.python.ast.rst_node import PythonRstNode
from renaissance.recipes.unit_to_pytest import UnitToPytest


class TestUnitToPytest:
    """AI: Tests for the UnitToPytest recipe."""

    def test_init(self):
        """AI: Verify the recipe's filename attribute reflects the constructed path."""
        subject = UnitToPytest(Path(targets.__file__).parent / "demo.py")
        assert_that(subject.filename, ends_with("demo.py"))

    def test_commit_does_nothing_when_not_changed(self, mocker):
        """AI: Verify has_changed() returns False when the code hasn't been modified."""
        subject = self._create(
            mocker,
            """
         1
            """,
        )
        assert_that(subject.has_changed(), is_(False))

    def test_convert_test_class_updates_only_testcase_bases(self, mocker):
        """AI: Verify convert_test_class rewrites only classes that extend TestCase, and normalizes their names."""
        subject = self._create(
            mocker,
            """
            class TestClass1(TestCase):
                pass
            class Class2Test(unittest.TestCase):
                pass
            """,
        )
        subject.convert_test_class()

        assert_that(subject.apply_to_string(), contains_string("class TestClass1:"))
        assert_that(subject.apply_to_string(), contains_string("class TestClass2:"))

    def _create(self, mocker, text) -> UnitToPytest:
        code = textwrap.dedent(text)
        mocker.patch(
            "renaissance.integrations.python.ast.factory.PythonFactory.create",
            return_value=PythonRstNode.load_from_text(code),
        )
        subject = UnitToPytest("x.py")
        subject.in_memory = True
        return subject

    def test_convert_plain_assert_same_length_rewrites_to_has_length(self, mocker):
        """AI: Verify convert_plain_assert_same_length rewrites a length-equality assert into assert_that/has_length."""
        expected = textwrap.dedent("""
        def test_asert():
            results = ['1']
            assert_that(results, has_length(1), f"length of results = {len(results)}")
        """)

        subject = self._create(
            mocker,
            """
        def test_asert():
            results = ['1']
            count: int = len(results)
            assert 1 == count, "count = " + str(count)
        """,
        )
        subject.convert_plain_assert_same_length()
        assert_that(subject.apply_to_string(), is_(expected))

    def test_restructure_module_injects_methods_when_class_exists(self, mocker):
        """AI: Verify restructure_module moves a module-level function into the existing test class as a method."""
        subject = self._create(
            mocker,
            """
        class TestFoo:
            def test_foo(self):
                pass
        def parse(a):
            pass
        """,
        )

        subject.in_memory = True
        subject.restructure_module()
        subject.commit()

        assert_that(subject.apply_to_string(), contains_string("def parse(self,a):"))

    def test_convert(self, mocker):
        """AI: Verify run() invokes convert_test_class, convert_test_setup, and replace_stmt the expected number of times."""
        sut = self._create(
            mocker,
            """
        class TestClass:
            def test_fun(self):
                with self.assertRaises(Eexception):
                    call()
        """,
        )
        spy = mocker.spy(sut, "convert_test_class")
        spy2 = mocker.spy(sut, "convert_test_setup")
        spy3 = mocker.spy(sut, "replace_stmt")
        sut.run()

        assert_that(spy.call_count, is_(1))
        assert_that(spy2.call_count, is_(1))
        assert_that(spy3.call_count, is_(26))

    def test_convert_assert(self, mocker):
        """AI: Verify convert_assert rewrites assertEqual calls into assert_that/is_, regardless of argument order."""
        sut = self._create(
            mocker,
            """
        class TestClass:
            def test_fun(self):
                self.assertEqual(1, call())
                self.assertEqual(call(),1)
        """,
        )
        sut.convert_assert("self.assertEqual($exp, $act)", "assert_that($exp, is_($act))")
        assert_that(sut.apply_to_string(), contains_string("assert_that(call()"))
        assert_that(sut.apply_to_string(), not_(contains_string("assert_that(1")))

    def test_to_assertthat(self, mocker):
        """AI: Verify a manual replace_stmt call rewrites a plain assert into assert_that(..., is_(True), ...)."""
        sut = self._create(
            mocker,
            """
            def test_fun():
                assert call() >=1
        """,
        )

        sut.replace_stmt("assert $stmt, $$msg", "assert_that($stmt, is_(True), $$msg)")
        assert_that(sut.apply_to_string(), contains_string("assert_that(call()"))
        assert_that(sut.apply_to_string(), not_(contains_string("assert_that(1")))

    def test_convert_test_class_renames_class_ending_with_test(self, mocker):
        """AI: Verify convert_test_class renames a FooTest class to TestFoo."""
        subject = self._create(
            mocker,
            """
            class FooTest(TestCase):
                pass
            """,
        )
        subject.convert_test_class()
        assert_that(subject.apply_to_string(), contains_string("class TestFoo:"))

    def test_convert_parameterized_test_at_top_level(self, mocker):
        """AI: Verify convert_parameterized_test rewrites a top-level @parameterized.expand into @pytest.mark.parametrize."""
        subject = self._create(
            mocker,
            """
            @parameterized.expand([("a",), ("b",)])
            @some_decorator
            def test_fun(self, val):
                pass
            """,
        )
        subject.convert_parameterized_test()
        assert_that(subject.apply_to_string(), contains_string("@pytest.mark.parametrize"))

    def test_convert_parameterized_test_inside_class(self, mocker):
        """AI: Verify convert_parameterized_test rewrites a class-nested @parameterized.expand into @pytest.mark.parametrize."""
        subject = self._create(
            mocker,
            """
            class TestFoo:
                @parameterized.expand([("a",), ("b",)])
                @some_decorator
                def test_fun(self, val):
                    pass
            """,
        )
        subject.convert_parameterized_test()
        assert_that(subject.apply_to_string(), contains_string("@pytest.mark.parametrize"))

    def test_remove_print_removes_entire_function_when_only_statement(self, mocker):
        """AI: Verify remove_print removes the entire function when print() is its only statement."""
        subject = self._create(
            mocker,
            """
            def test_foo(self):
                print("hello")
            """,
        )
        subject.remove_print()
        assert_that(subject.apply_to_string(), not_(contains_string("test_foo")))

    def test_remove_print_removes_only_print_when_other_statements_exist(self, mocker):
        """AI: Verify remove_print removes only the print() call, keeping other statements in the function."""
        subject = self._create(
            mocker,
            """
            def test_foo(self):
                print("hello")
                assert 1 == 1
            """,
        )
        subject.remove_print()
        assert_that(subject.apply_to_string(), not_(contains_string("print")))
        assert_that(subject.apply_to_string(), contains_string("assert 1 == 1"))

    def test_convert_plain_assert_same_length_when_not_swapped(self, mocker):
        """AI: Verify convert_plain_assert_same_length still rewrites to has_length when operands aren't swapped."""
        subject = self._create(
            mocker,
            """
        def test_foo():
            results = ['1']
            count: int = len(results)
            assert results == count, "count = " + str(count)
        """,
        )
        subject.convert_plain_assert_same_length()
        assert_that(subject.apply_to_string(), contains_string("has_length"))

    def test_convert_skip_test_replaces_unittest_skip(self, mocker):
        """AI: Verify convert_skip_test rewrites @unittest.skip to @pytest.mark.skip."""
        subject = self._create(
            mocker,
            """
            @unittest.skip("reason")
            def test_foo(self):
                pass
            """,
        )
        subject.convert_skip_test()
        assert_that(subject.apply_to_string(), contains_string("pytest.mark.skip"))
        assert_that(subject.apply_to_string(), not_(contains_string("unittest.skip")))

    def test_swap_expected_and_actual_swaps_when_literal_is_expected(self, mocker):
        """AI: Verify swap_expected_and_actual reorders assert_that args so the literal becomes the expected value."""
        subject = self._create(
            mocker,
            """
            def test_foo(self):
                assert_that(1, is_(call()))
            """,
        )
        subject.swap_expected_and_actual()
        assert_that(subject.apply_to_string(), contains_string("assert_that(call(), is_(1))"))

    def test_restructure_module_moves_functions_into_existing_test_class(self, mocker):
        """AI: Verify restructure_module moves a standalone helper function into the existing TestFoo class."""
        subject = self._create(
            mocker,
            """
            class TestFoo:
                def test_existing(self):
                    pass
            def helper(a):
                return a
            """,
        )
        subject.in_memory = True
        subject.restructure_module()
        subject.commit()
        assert_that(subject.apply_to_string(), contains_string("def helper(self,a):"))

    def test_remove_duplicate_import_removes_middle_duplicates(self, mocker):
        """AI: Verify remove_duplicate_import collapses repeated identical import statements down to the first and last."""
        subject = self._create(
            mocker,
            """
            import pytest
            from hamcrest import *
            import pytest
            from hamcrest import *
            import pytest
            from hamcrest import *
            def test_foo():
                pass
            """,
        )
        subject.remove_duplicate_import("import pytest")
        result = subject.apply_to_string()
        assert_that(result.count("import pytest"), is_(2))

    def test_convert_test_setup_adds_pytest_fixture(self, mocker):
        """AI: Verify convert_test_setup rewrites setUp into a pytest autouse fixture named setup."""
        subject = self._create(
            mocker,
            """
            class TestFoo:
                def setUp(self):
                    self.x = 1
                def test_foo(self):
                    pass
            """,
        )
        subject.convert_test_setup()
        assert_that(subject.apply_to_string(), contains_string("@pytest.fixture(autouse=True)"))
        assert_that(subject.apply_to_string(), contains_string("def setup(self)"))

    def test_convert_parameterized_test_with_vargs(self, mocker):
        """AI: Verify convert_parameterized_test preserves *rest varargs when rewriting to @pytest.mark.parametrize."""
        subject = self._create(
            mocker,
            """
            @parameterized.expand([("a", 1), ("b", 2)])
            @some_decorator
            def test_fun(self, val, *rest):
                pass
            """,
        )
        subject.convert_parameterized_test()
        assert_that(subject.apply_to_string(), contains_string("@pytest.mark.parametrize"))
        assert_that(subject.apply_to_string(), contains_string("*rest"))

    def test_restructure_module_rewrites_call_sites_in_existing_class(self, mocker):
        """AI: Verify restructure_module rewrites call sites of a moved helper function to use self."""
        subject = self._create(
            mocker,
            """
            class TestFoo:
                def test_existing(self):
                    result = helper(1)
            def helper(a):
                return a
            """,
        )
        subject.in_memory = True
        subject.restructure_module()
        subject.commit()
        assert_that(subject.apply_to_string(), contains_string("self.helper(1)"))

    def test_convert_file_to_test_class_strips_trailing_test(self, mocker):
        """AI: Verify convert_file_to_test_class strips a trailing '_test' suffix when deriving the class name."""
        subject = self._create(mocker, "pass")
        mocker.patch.object(type(subject), "filename", new_callable=lambda: property(lambda self: "my_module_test.py"))
        assert_that(subject.convert_file_to_test_class(), is_("TestMyModule"))

    def test_convert_file_to_test_class_keeps_test_prefix(self, mocker):
        """AI: Verify convert_file_to_test_class keeps a leading 'test_' prefix when deriving the class name."""
        subject = self._create(mocker, "pass")
        mocker.patch.object(type(subject), "filename", new_callable=lambda: property(lambda self: "test_my_module.py"))
        assert_that(subject.convert_file_to_test_class(), is_("TestMyModule"))

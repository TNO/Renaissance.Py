import textwrap
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, mock_open, patch

import pytest
from hamcrest import assert_that, contains_string, has_length, is_, ends_with, not_

import targets
from renaissance.impl.python import PythonRstNode, PythonPatternFactory
from renaissance.impl.python.factory import PythonFactory
from renaissance.refactoring import unit2pytest as mod
from renaissance.refactoring.unit2pytest import Unit2Pytest
from renaissance.syntax_tree import ASTFactory
from renaissance.syntax_tree.match_finder import match_pattern

class TestUnit2Pytest:
    def test_init(self):
        subject = Unit2Pytest(Path(targets.__file__).parent / "demo.py")
        assert_that(subject.filename, ends_with("demo.py"))



    def test_commit_does_nothing_when_not_changed(self,mocker):
        subject = self._create(mocker, """
         1
            """)
        assert_that(subject.has_changed(), is_(False))


    def test_convert_test_class_updates_only_testcase_bases(self,mocker):
        subject = self._create(mocker, """
            class TestClass1(TestCase):
                pass
            class Class2Test(unittest.TestCase):    
                pass
            """)
        subject.convert_test_class()

        assert_that(subject.apply_to_string(), contains_string("class TestClass1:"))
        assert_that(subject.apply_to_string(), contains_string("class TestClass2:"))


    def _create(self,mocker,text) -> Unit2Pytest:
        code = textwrap.dedent(text)
        mocker.patch(
            "renaissance.impl.python.factory.PythonFactory.create",
            return_value=PythonRstNode.load_from_text(code),
        )
        subject = Unit2Pytest("x.py")
        subject.in_memory = True
        return subject


    def test_convert_plain_assert_same_length_rewrites_to_has_length(self,mocker):
        expected = textwrap.dedent("""
        def test_asert():
            results = ['1']
            assert_that(results, has_length(1), f"length of results = {len(results)}")
        """)

        subject = self._create(mocker,"""
        def test_asert():
            results = ['1']
            count: int = len(results)
            assert 1 == count, "count = " + str(count)
        """)
        subject.convert_plain_assert_same_length()
        assert_that(subject.apply_to_string(), is_(expected))


    def test_restructure_module_injects_methods_when_class_exists(self,mocker):
        subject = self._create(mocker,"""
        class TestFoo:
            def test_foo(self):
                pass
        def parse(a):
            pass
        """)

        subject.in_memory = True
        subject.restructure_module()
        subject.commit()

        assert_that(subject.apply_to_string(), contains_string("def parse(self,a):"))


    def test_convert(self, mocker):
        sut = self._create(mocker, '''
        class TestClass:
            def test_fun(self):
                with self.assertRaises(Eexception): 
                    call()
        ''')
        spy = mocker.spy(sut, 'convert_test_class')
        spy2 = mocker.spy(sut, 'convert_test_setup')
        spy3 = mocker.spy(sut, 'replace_stmt')
        sut.run()

        assert_that(spy.call_count, is_(1))
        assert_that(spy2.call_count, is_(1))
        assert_that(spy3.call_count, is_(26))

    def test_convert_assert(self, mocker):
        sut = self._create(mocker, '''
        class TestClass:
            def test_fun(self):
                self.assertEqual(1, call())
                self.assertEqual(call(),1)
        ''')
        sut.run()
        assert_that(sut.apply_to_string(), contains_string("assert_that(call()"))
        assert_that(sut.apply_to_string(), not_(contains_string("assert_that(1")))


    def test_to_class(self, mocker):
        sut = self._create(mocker, '''
            def test_fun():
                assert call() >=1
        ''')

        sut.refactor()
        assert_that(sut.apply_to_string(), contains_string("assert_that(call()"))
        assert_that(sut.apply_to_string(), not_(contains_string("assert_that(1")))

    def test_convert_test_class_renames_class_ending_with_test(self, mocker):
        subject = self._create(mocker, """
            class FooTest(TestCase):
                pass
            """)
        subject.convert_test_class()
        assert_that(subject.apply_to_string(), contains_string("class TestFoo:"))

    def test_convert_parameterized_test_at_top_level(self, mocker):
        subject = self._create(mocker, """
            @parameterized.expand([("a",), ("b",)])
            @some_decorator
            def test_fun(self, val):
                pass
            """)
        subject.convert_parameterized_test()
        assert_that(subject.apply_to_string(), contains_string("@pytest.mark.parametrize"))

    def test_convert_parameterized_test_inside_class(self, mocker):
        subject = self._create(mocker, """
            class TestFoo:
                @parameterized.expand([("a",), ("b",)])
                @some_decorator
                def test_fun(self, val):
                    pass
            """)
        subject.convert_parameterized_test()
        assert_that(subject.apply_to_string(), contains_string("@pytest.mark.parametrize"))

    def test_remove_print_removes_entire_function_when_only_statement(self, mocker):
        subject = self._create(mocker, """
            def test_foo(self):
                print("hello")
            """)
        subject.remove_print()
        assert_that(subject.apply_to_string(), not_(contains_string("test_foo")))

    def test_remove_print_removes_only_print_when_other_statements_exist(self, mocker):
        subject = self._create(mocker, """
            def test_foo(self):
                print("hello")
                assert 1 == 1
            """)
        subject.remove_print()
        assert_that(subject.apply_to_string(), not_(contains_string("print")))
        assert_that(subject.apply_to_string(), contains_string("assert 1 == 1"))

    def test_convert_plain_assert_same_length_when_not_swapped(self, mocker):
        subject = self._create(mocker, """
        def test_foo():
            results = ['1']
            count: int = len(results)
            assert results == count, "count = " + str(count)
        """)
        subject.convert_plain_assert_same_length()
        assert_that(subject.apply_to_string(), contains_string("has_length"))

    def test_convert_skip_test_replaces_unittest_skip(self, mocker):
        subject = self._create(mocker, """
            @unittest.skip("reason")
            def test_foo(self):
                pass
            """)
        subject.convert_skip_test()
        assert_that(subject.apply_to_string(), contains_string("pytest.mark.skip"))
        assert_that(subject.apply_to_string(), not_(contains_string("unittest.skip")))

    def test_swap_expected_and_actual_swaps_when_literal_is_expected(self, mocker):
        subject = self._create(mocker, """
            def test_foo(self):
                assert_that(1, is_(call()))
            """)
        subject.swap_expected_and_actual()
        assert_that(subject.apply_to_string(), contains_string("assert_that(call(), is_(1))"))

    def test_restructure_module_moves_functions_into_existing_test_class(self, mocker):
        subject = self._create(mocker, """
            class TestFoo:
                def test_existing(self):
                    pass
            def helper(a):
                return a
            """)
        subject.in_memory = True
        subject.restructure_module()
        subject.commit()
        assert_that(subject.apply_to_string(), contains_string("def helper(self,a):"))

    def test_remove_duplicate_import_removes_middle_duplicates(self, mocker):
        subject = self._create(mocker, """
            import pytest
            from hamcrest import *
            import pytest
            from hamcrest import *
            import pytest
            from hamcrest import *
            def test_foo():
                pass
            """)
        subject.remove_duplicate_import("import pytest\nfrom hamcrest import *")
        result = subject.apply_to_string()
        assert_that(result.count("import pytest"), is_(2))

    def test_convert_test_setup_adds_pytest_fixture(self, mocker):
        subject = self._create(mocker, """
            class TestFoo:
                def setUp(self):
                    self.x = 1
                def test_foo(self):
                    pass
            """)
        subject.convert_test_setup()
        assert_that(subject.apply_to_string(), contains_string("@pytest.fixture(autouse=True)"))
        assert_that(subject.apply_to_string(), contains_string("def setup(self)"))

    def test_convert_parameterized_test_with_vargs(self, mocker):
        subject = self._create(mocker, """
            @parameterized.expand([("a", 1), ("b", 2)])
            @some_decorator
            def test_fun(self, val, *rest):
                pass
            """)
        subject.convert_parameterized_test()
        assert_that(subject.apply_to_string(), contains_string("@pytest.mark.parametrize"))
        assert_that(subject.apply_to_string(), contains_string("*rest"))

    def test_restructure_module_rewrites_call_sites_in_existing_class(self, mocker):
        subject = self._create(mocker, """
            class TestFoo:
                def test_existing(self):
                    result = helper(1)
            def helper(a):
                return a
            """)
        subject.in_memory = True
        subject.restructure_module()
        subject.commit()
        assert_that(subject.apply_to_string(), contains_string("self.helper(1)"))

    def test_convert_file_to_test_class_strips_trailing_test(self, mocker):
        subject = self._create(mocker, "pass")
        mocker.patch.object(type(subject), "filename", new_callable=lambda: property(lambda self: "my_module_test.py"))
        assert_that(subject.convert_file_to_test_class(), is_("TestMyModule"))

    def test_convert_file_to_test_class_keeps_test_prefix(self, mocker):
        subject = self._create(mocker, "pass")
        mocker.patch.object(type(subject), "filename", new_callable=lambda: property(lambda self: "test_my_module.py"))
        assert_that(subject.convert_file_to_test_class(), is_("TestMyModule"))


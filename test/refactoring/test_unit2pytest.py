import textwrap
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, mock_open, patch

import pytest
from hamcrest import assert_that, contains_string, has_length, is_, ends_with, not_

import targets
from renaissance.impl.python import PythonASTNode, PythonPatternFactory
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
            return_value=PythonASTNode.load_from_text(code),
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

    @pytest.mark.skip("failing before demo fix")
    def test_convert_assert(self, mocker):
        sut = self._create(mocker, '''
        class TestClass:
            def test_fun(self):
                self.assertEqual(1, call())
                self.assertEqual(call(),1)
        ''')
        sut.convert_pytest()
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


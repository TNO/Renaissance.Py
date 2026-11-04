# Copyright (C) 2024-2026 TNO
#
# Licensed under the terms specified in the LICENSE file in the root directory
# of this repository, also available at:
# https://github.com/TNO/Renaissance.Py/blob/main/LICENSE

"""Tests for the UnitToPytest recipe."""

import importlib.util
import re
import subprocess
import sys
import textwrap
from collections import Counter
from pathlib import Path
from typing import Protocol, cast

import pytest
from hamcrest import assert_that, contains_string, ends_with, equal_to, is_, not_
from pytest_mock import MockerFixture

import targets
from renaissance.integrations.python.ast.rst_node import PythonRstNode
from renaissance.recipes.unit_to_pytest import UnitToPytest


class TestUnitToPytest:
    """AI: Tests for the UnitToPytest recipe."""

    def test_init(self) -> None:
        """AI: Verify the recipe's filename attribute reflects the constructed path."""
        subject = UnitToPytest(Path(targets.__file__).parent / "demo.py")
        assert_that(subject.filename, ends_with("demo.py"))

    def test_commit_does_nothing_when_not_changed(self, mocker: MockerFixture) -> None:
        """AI: Verify has_changed() returns False when the code hasn't been modified."""
        subject = self._create(
            mocker,
            """
         1
            """,
        )
        assert_that(subject.has_changed(), is_(False))

    def test_convert_test_class_updates_only_testcase_bases(self, mocker: MockerFixture) -> None:
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

    def _create(self, mocker: MockerFixture, text: str) -> UnitToPytest:
        code = textwrap.dedent(text)
        mocker.patch(
            "renaissance.integrations.python.ast.factory.PythonFactory.create",
            return_value=PythonRstNode.load_from_text(code),
        )
        subject = UnitToPytest("x.py")
        subject.in_memory = True
        return subject

    def test_convert_plain_assert_same_length_rewrites_to_has_length(self, mocker: MockerFixture) -> None:
        """AI: Verify convert_plain_assert_same_length rewrites a length-equality assert into assert_that/has_length."""
        expected = textwrap.dedent("""
        def test_assert():
            results = ['1']
            assert_that(results, has_length(1), f"length of results = {len(results)}")
        """)

        subject = self._create(
            mocker,
            """
        def test_assert():
            results = ['1']
            count: int = len(results)
            assert 1 == count, "count = " + str(count)
        """,
        )
        subject.convert_plain_assert_same_length()
        assert_that(subject.apply_to_string(), is_(expected))

    def test_convert_plain_assert_same_length_with_variable_on_left(self, mocker: MockerFixture) -> None:
        """AI: Verify convert_plain_assert_same_length also rewrites 'assert count == 1' into assert_that/has_length."""
        expected = textwrap.dedent("""
        def test_assert():
            results = ['1']
            assert_that(results, has_length(1), f"length of results = {len(results)}")
        """)

        subject = self._create(
            mocker,
            """
        def test_assert():
            results = ['1']
            count: int = len(results)
            assert count == 1, "count = " + str(count)
        """,
        )
        subject.convert_plain_assert_same_length()
        assert_that(subject.apply_to_string(), is_(expected))

    def test_restructure_module_injects_methods_when_class_exists(self, mocker) -> None:
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

    def test_convert(self, mocker: MockerFixture) -> None:
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

    def test_convert_assert(self, mocker: MockerFixture) -> None:
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

    def test_to_assertthat(self, mocker: MockerFixture) -> None:
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

    def test_convert_test_class_renames_class_ending_with_test(self, mocker: MockerFixture) -> None:
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

    def test_convert_parameterized_test_at_top_level(self, mocker: MockerFixture) -> None:
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
        assert_that(subject.apply_to_string(), contains_string('@pytest.mark.parametrize("val",'))

    def test_convert_parameterized_test_inside_class(self, mocker: MockerFixture) -> None:
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
        assert_that(subject.apply_to_string(), contains_string('@pytest.mark.parametrize("val",'))

    def test_convert_parameterized_test_with_return_annotation(self, mocker: MockerFixture) -> None:
        """AI: Verify convert_parameterized_test also rewrites functions with annotated parameters and return type."""
        subject = self._create(
            mocker,
            """
            class TestFoo:
                @parameterized.expand([("a", 1), ("b", 2)])
                def test_fun(self, name: str, val: int) -> None:
                    pass
            """,
        )
        subject.convert_parameterized_test()
        assert_that(subject.apply_to_string(), contains_string('@pytest.mark.parametrize(("name", "val"),'))
        assert_that(subject.apply_to_string(), not_(contains_string("@parameterized.expand")))

    def test_remove_print_removes_entire_function_when_only_statement(self, mocker: MockerFixture) -> None:
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

    def test_remove_print_removes_only_print_when_other_statements_exist(self, mocker: MockerFixture) -> None:
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

    def test_convert_plain_assert_same_length_when_not_swapped(self, mocker: MockerFixture) -> None:
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

    def test_convert_skip_test_replaces_unittest_skip(self, mocker: MockerFixture) -> None:
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

    def test_swap_expected_and_actual_swaps_when_literal_is_expected(self, mocker: MockerFixture) -> None:
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

    def test_restructure_module_moves_functions_into_existing_test_class(self, mocker: MockerFixture) -> None:
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

    @pytest.mark.xfail(
        strict=True,
        reason="The first and the last copy are kept: https://github.com/TNO/Renaissance.Py/issues/317",
    )
    def test_remove_duplicate_import_keeps_one_copy(self, mocker: MockerFixture) -> None:
        """remove_duplicate_import leaves a single copy of an import statement that appears several times."""
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
        assert_that(result.count("import pytest"), is_(1))

    def test_convert_test_setup_adds_pytest_fixture(self, mocker: MockerFixture) -> None:
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

    def test_convert_parameterized_test_with_vargs(self, mocker: MockerFixture) -> None:
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
        assert_that(subject.apply_to_string(), contains_string('@pytest.mark.parametrize(("val", "*rest"),'))

    def test_restructure_module_rewrites_call_sites_in_existing_class(self, mocker: MockerFixture) -> None:
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

    def test_convert_file_to_test_class_strips_trailing_test(self, mocker: MockerFixture) -> None:
        """AI: Verify convert_file_to_test_class strips a trailing '_test' suffix when deriving the class name."""
        subject = self._create(mocker, "pass")
        mocker.patch.object(type(subject), "filename", new_callable=lambda: property(lambda self: "my_module_test.py"))
        assert_that(subject.convert_file_to_test_class(), is_("TestMyModule"))

    def test_convert_file_to_test_class_keeps_test_prefix(self, mocker: MockerFixture) -> None:
        """AI: Verify convert_file_to_test_class keeps a leading 'test_' prefix when deriving the class name."""
        subject = self._create(mocker, "pass")
        mocker.patch.object(type(subject), "filename", new_callable=lambda: property(lambda self: "test_my_module.py"))
        assert_that(subject.convert_file_to_test_class(), is_("TestMyModule"))


_ISSUE_URL = "https://github.com/TNO/Renaissance.Py/issues/317"
_CONVERSION_TIMEOUT_SECONDS = 10
_CONVERT_SCRIPT = "import sys; from renaissance.recipes.unit_to_pytest import UnitToPytest; UnitToPytest(sys.argv[1]).run()"
_ASSERTION_TEST = """\
import unittest


class TestFoo(unittest.TestCase):
    def test_a(self):
        {assertion}
"""


class _ConvertedTest(Protocol):
    """The converted test class of _ASSERTION_TEST."""

    def test_a(self) -> None:
        """Run the converted assertion."""


def _known_bug(reason: str) -> pytest.MarkDecorator:
    """Return a strict xfail mark for a defect of UnitToPytest.run(), with its reason and the issue that tracks it."""
    return pytest.mark.xfail(strict=True, reason=f"{reason}: {_ISSUE_URL}")


def _write_test_file(tmp_path: Path, source: str) -> Path:
    """Write the dedented source to test_foo.py in tmp_path and return its path."""
    target = tmp_path / "test_foo.py"
    target.write_text(textwrap.dedent(source).lstrip(), encoding="utf-8")
    return target


def _converted_test_class(target: Path) -> type[_ConvertedTest]:
    """Convert target with UnitToPytest, import the result and return its TestFoo class."""
    UnitToPytest(str(target)).run()
    spec = importlib.util.spec_from_file_location(f"converted_{target.parent.name}", target)
    if spec is None or spec.loader is None:
        message = f"could not load {target} as a module"
        raise RuntimeError(message)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return cast("type[_ConvertedTest]", vars(module)["TestFoo"])


def _pytest_outcomes(target: Path) -> Counter[str]:
    """Convert target with UnitToPytest in a separate interpreter, run pytest on it and count the outcomes.

    Raises:
        subprocess.CalledProcessError: if the conversion raises.
        subprocess.TimeoutExpired: if the conversion does not return within _CONVERSION_TIMEOUT_SECONDS.

    """
    subprocess.run(  # noqa: S603 (runs this interpreter on a file the test wrote)
        [sys.executable, "-c", _CONVERT_SCRIPT, str(target)],
        capture_output=True,
        check=True,
        timeout=_CONVERSION_TIMEOUT_SECONDS,
    )
    result = subprocess.run(  # noqa: S603 (runs this interpreter on a file the test wrote)
        [sys.executable, "-m", "pytest", "-q", "--color=no", "-p", "no:cacheprovider", target.name],
        capture_output=True,
        check=False,
        cwd=target.parent,
        text=True,
    )
    summary = result.stdout.strip().splitlines()[-1]
    return Counter({outcome: int(count) for count, outcome in re.findall(r"(\d+) (passed|failed|skipped|error)", summary)})


class TestRunEndToEnd:
    """run() on a whole unittest file: the converted file must test the same things as the original."""

    @pytest.mark.parametrize(
        ("assertion", "passing", "failing"),
        [
            pytest.param("self.assertEqual(x, 5)", 5, 4, id="equal"),
            pytest.param(
                "self.assertGreaterEqual(5, x)",
                4,
                6,
                id="greater-equal",
                marks=_known_bug("The arguments are swapped but the matcher is kept"),
            ),
            pytest.param(
                "self.assertGreater(5, x)",
                4,
                5,
                id="greater",
                marks=_known_bug("The arguments are swapped but the matcher is kept"),
            ),
            pytest.param("self.assertLessEqual(x, 5)", 5, 6, id="less-equal", marks=_known_bug("The pattern says assertLesserEqual")),
            pytest.param("self.assertLess(x, 5)", 4, 5, id="less", marks=_known_bug("The pattern says assertLesser")),
            pytest.param('self.assertIn("a", x)', "abc", "xyz", id="in-string", marks=_known_bug("contain_string does not exist")),
            pytest.param("self.assertIn(1, x)", [1, 2], [3], id="in-list", marks=_known_bug("contain_string does not exist")),
            pytest.param("self.assertIsNone(x)", None, 0, id="is-none", marks=_known_bug("assertIsNone is not converted")),
            pytest.param("self.assertNotEqual(x, 5)", 4, 5, id="not-equal", marks=_known_bug("assertNotEqual is not converted")),
            pytest.param(
                'self.assertEqual(x, 5, "message")',
                5,
                4,
                id="equal-with-message",
                marks=_known_bug("An assertion with a message is not converted"),
            ),
        ],
    )
    def test_converted_assertion_checks_the_same_condition(self, tmp_path: Path, assertion: str, passing: object, failing: object) -> None:
        """The converted assertion passes for a value of x that satisfies the original one, and fails for one that doesn't."""
        target = _write_test_file(tmp_path, _ASSERTION_TEST.format(assertion=assertion))
        test_class = _converted_test_class(target)
        module_globals = test_class.test_a.__globals__

        module_globals["x"] = passing
        test_class().test_a()
        module_globals["x"] = failing
        with pytest.raises(AssertionError):
            test_class().test_a()

    @pytest.mark.parametrize(
        ("source", "expected"),
        [
            pytest.param(
                """
                import unittest


                class TestFoo(unittest.TestCase):
                    def test_a(self):
                        x = 1
                        self.assertEqual(x, 1)
                """,
                Counter(passed=1),
                id="plain",
            ),
            pytest.param(
                """
                import unittest


                class FooTest(unittest.TestCase):
                    def setUp(self):
                        self.x = 1

                    def test_a(self):
                        x = self.x
                        self.assertEqual(x, 1)
                """,
                Counter(passed=1),
                id="setup",
                marks=_known_bug("The setUp fixture is glued to the previous statement"),
            ),
            pytest.param(
                """
                import unittest

                calls = []


                class TestFoo(unittest.TestCase):
                    def tearDown(self):
                        calls.append("torn down")

                    def test_a(self):
                        x = 1
                        self.assertEqual(x, 1)

                    def test_b(self):
                        x = len(calls)
                        self.assertEqual(x, 1)
                """,
                Counter(passed=2),
                id="teardown",
                marks=_known_bug("tearDown is not converted, so it is no longer called"),
            ),
            pytest.param(
                """
                import unittest


                def helper(a):
                    return a


                class FooTest(unittest.TestCase):
                    def test_a(self):
                        x = helper(1)
                        self.assertEqual(x, 1)
                """,
                Counter(passed=1),
                id="module-helper",
                marks=_known_bug("The helper goes to a second class with the same name"),
            ),
            pytest.param(
                """
                import unittest


                class TestFoo(unittest.TestCase):
                    @unittest.skipIf(True, "not on this platform")
                    def test_a(self):
                        raise AssertionError

                    def test_b(self):
                        x = 1
                        self.assertEqual(x, 1)
                """,
                Counter(passed=1, skipped=1),
                id="skip-if",
                marks=_known_bug("unittest.skipIf stays while the unittest import is removed"),
            ),
            pytest.param(
                """
                import unittest


                class MyTestCase(unittest.TestCase):
                    def one(self):
                        return 1


                class TestFoo(MyTestCase):
                    def test_a(self):
                        x = self.one()
                        self.assertEqual(x, 1)
                """,
                Counter(passed=1),
                id="custom-base",
                marks=_known_bug("A base class whose name ends with TestCase is dropped"),
            ),
            pytest.param(
                """
                import unittest

                print("loading")


                class TestFoo(unittest.TestCase):
                    def test_a(self):
                        x = 1
                        self.assertEqual(x, 1)
                """,
                Counter(passed=1),
                id="module-print",
                marks=_known_bug("remove_print raises AttributeError on a module-level print"),
            ),
            pytest.param(
                """
                import unittest


                class TestFoo(unittest.TestCase):
                    def test_a(self):
                        self.assertEqual(1, 1)
                """,
                Counter(passed=1),
                id="literal-equal",
                marks=_known_bug("post_processing never stops swapping the two literals"),
            ),
            pytest.param(
                """
                def test_x():
                    assert 1 == 1
                """,
                Counter(passed=1),
                id="already-pytest",
                marks=_known_bug("A file already in pytest style is rewritten and run() does not return"),
            ),
        ],
    )
    def test_converted_file_behaves_like_the_unittest_original(self, tmp_path: Path, source: str, expected: Counter[str]) -> None:
        """Under pytest, the converted file has the outcomes the original has under unittest, and the conversion returns."""
        target = _write_test_file(tmp_path, source)

        assert_that(_pytest_outcomes(target), equal_to(expected))

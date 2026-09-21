"""Tests for the PythonRefactoring recipe base class."""

import ast
import keyword
import textwrap
from typing import cast
from unittest.mock import patch

from hamcrest import assert_that, contains_string, is_
from hypothesis import given, settings
from hypothesis import strategies as st
from pytest_mock import MockerFixture

from renaissance.integrations.python.ast.rst_node import PythonRstNode
from renaissance.recipes.python_refactoring import PythonRefactoring
from renaissance.recipes.unit_to_pytest import UnitToPytest
from renaissance.syntax_tree.semantic_kind import SemanticKind


class TestPythonRefactoring:
    """AI: Tests for the PythonRefactoring recipe base class."""

    _LEAF_EXPR_STRATEGY = st.one_of(
        st.integers(min_value=-100, max_value=100).map(str),
        st.text(alphabet="abc ", min_size=0, max_size=6).map(repr),
    )
    _EXPR_STRATEGY = st.recursive(
        _LEAF_EXPR_STRATEGY,
        lambda child: st.builds(
            lambda fn_name, args: f"{fn_name}({', '.join(args)})",
            st.sampled_from(["inner", "g", "helper"]),
            st.lists(child, max_size=3),
        ),
        max_leaves=8,
    )
    _IDENTIFIER_STRATEGY = (
        st.from_regex(r"[A-Za-z_][A-Za-z0-9_]{0,30}", fullmatch=True)
        .filter(str.isidentifier)
        .filter(lambda name: not keyword.iskeyword(name))
    )

    def _patch_factory(self, mocker, text="pass", filename="test_foo.py"):
        code = textwrap.dedent(text)
        mocker.patch(
            "renaissance.integrations.python.ast.factory.PythonFactory.create",
            return_value=PythonRstNode.load_from_text(code, filename),
        )

    # ------------------------------------------------------------------
    # __init__ / replace_stmt
    # ------------------------------------------------------------------

    def test_init_sets_default_list_patterns(self, mocker):
        """AI: Verify a subclass's __init__ sets its black/white list patterns from subclass defaults."""
        self._patch_factory(mocker)
        subject = UnitToPytest("test_foo.py")
        # base class defaults are overridden by subclass, but they are set in __init__
        assert_that(subject.black_list_pattern, is_("utils_for_test"))
        assert_that(subject.white_list_pattern, is_("test"))

    def test_replace_stmt_rewrites_matching_pattern(self, mocker):
        """AI: Verify replace_stmt rewrites a statement matching an exact pattern."""
        self._patch_factory(
            mocker,
            """
            import unittest
            """,
            "test_foo.py",
        )
        subject = UnitToPytest("test_foo.py")
        subject.in_memory = True
        subject.replace_stmt("import unittest", "import pytest\nfrom hamcrest import *")
        assert_that(subject.apply_to_string(), contains_string("import pytest"))
        assert_that(subject.apply_to_string(), contains_string("from hamcrest import *"))

    def test_replace_stmt_expands_variadic_captures(self, mocker):
        """AI: Verify replace_stmt rewrites a statement matched via a variadic ($$symbols) capture."""
        self._patch_factory(
            mocker,
            """
            from unittest import TestCase, skip
            """,
            "test_foo.py",
        )
        subject = UnitToPytest("test_foo.py")
        subject.in_memory = True
        subject.replace_stmt(
            "from unittest import TestCase,$$symbols",
            "import pytest\nfrom hamcrest import *",
        )
        assert_that(subject.apply_to_string(), contains_string("import pytest"))

    # ------------------------------------------------------------------
    # extract_call_arguments()
    # ------------------------------------------------------------------

    def test_extract_call_arguments_positional_only(self, mocker):
        """Verify extract_call_arguments returns only positional values for positional-only calls."""
        self._patch_factory(mocker, "fun(1, 'x')")
        subject = UnitToPytest("test_foo.py")
        call_node = subject.find_semantic_kind(SemanticKind.CALL)[0]

        positional, keyword = subject.extract_call_arguments(call_node)

        assert_that(positional, is_(["1", "'x'"]))
        assert_that(keyword, is_({}))

    def test_extract_call_arguments_keyword_only(self, mocker):
        """Verify extract_call_arguments returns only keyword values for keyword-only calls."""
        self._patch_factory(mocker, "fun(a=1, b='x')")
        subject = UnitToPytest("test_foo.py")
        call_node = subject.find_semantic_kind(SemanticKind.CALL)[0]

        positional, keyword = subject.extract_call_arguments(call_node)

        assert_that(positional, is_([]))
        assert_that(keyword, is_({"a": "1", "b": "'x'"}))

    def test_extract_call_arguments_mixed(self, mocker):
        """Verify extract_call_arguments splits mixed positional and keyword arguments correctly."""
        self._patch_factory(mocker, "fun(1, 2, b='x', c=other)")
        subject = UnitToPytest("test_foo.py")
        call_node = subject.find_semantic_kind(SemanticKind.CALL)[0]

        positional, keyword = subject.extract_call_arguments(call_node)

        assert_that(positional, is_(["1", "2"]))
        assert_that(keyword, is_({"b": "'x'", "c": "other"}))

    def test_extract_call_arguments_accepts_node_inside_call(self, mocker):
        """Verify extract_call_arguments works when given a child node nested inside a call."""
        self._patch_factory(mocker, "fun(1, k='v')")
        subject = UnitToPytest("test_foo.py")
        call_node = subject.find_semantic_kind(SemanticKind.CALL)[0]
        node_inside_call = call_node.children[0]

        positional, keyword = subject.extract_call_arguments(node_inside_call)

        assert_that(positional, is_(["1"]))
        assert_that(keyword, is_({"k": "'v'"}))

    def test_extract_call_arguments_walks_parent_chain_to_first_call(self, mocker):
        """Verify extract_call_arguments climbs ancestors and uses the first enclosing call node."""
        self._patch_factory(mocker, "outer(inner(1), k=2)")
        subject = UnitToPytest("test_foo.py")
        call_nodes = subject.find_semantic_kind(SemanticKind.CALL)
        inner_call = next(call for call in call_nodes if call.signature.startswith("inner("))

        node_below_inner_call = inner_call.children[0]

        positional, keyword = subject.extract_call_arguments(node_below_inner_call)

        assert_that(positional, is_(["1"]))
        assert_that(keyword, is_({}))

    def test_extract_call_arguments_returns_empty_for_non_call_node(self, mocker):
        """Verify extract_call_arguments returns empty positional/keyword results for non-call nodes."""
        self._patch_factory(mocker, "x = 1")
        subject = UnitToPytest("test_foo.py")
        assign_node = subject.find_semantic_kind(SemanticKind.ASSIGNMENT)[0]

        positional, keyword = subject.extract_call_arguments(assign_node)

        assert_that(positional, is_([]))
        assert_that(keyword, is_({}))

    @settings(max_examples=50)
    @given(
        positional_args=st.lists(_EXPR_STRATEGY, max_size=4),
        keyword_args=st.dictionaries(keys=_IDENTIFIER_STRATEGY, values=_EXPR_STRATEGY, max_size=4),
    )
    def test_extract_call_arguments_hypothesis_roundtrip(self, positional_args, keyword_args):
        """Property: extraction round-trips generated positional and keyword call arguments."""
        rendered_kwargs = [f"{name}={value}" for name, value in keyword_args.items()]
        source = f"fun({', '.join([*positional_args, *rendered_kwargs])})"

        code = textwrap.dedent(source)
        with patch(
            "renaissance.integrations.python.ast.factory.PythonFactory.create",
            return_value=PythonRstNode.load_from_text(code, "test_foo.py"),
        ):
            subject = UnitToPytest("test_foo.py")
        call_node = subject.find_semantic_kind(SemanticKind.CALL)[0]

        positional, keyword_result = subject.extract_call_arguments(call_node)

        assert_that(positional, is_(positional_args))
        assert_that(keyword_result, is_(keyword_args))

    # ------------------------------------------------------------------
    # class_declares_base() / class_base_arguments()
    # ------------------------------------------------------------------

    def test_class_base_arguments_returns_declared_bases(self, mocker):
        """Verify class_base_arguments returns all explicitly declared base classes."""
        self._patch_factory(mocker, "class Child(Base1, Base2):\n    pass")
        subject = UnitToPytest("test_foo.py")
        class_node = subject.find_semantic_kind(SemanticKind.CLASS)[0]

        bases = subject.class_base_arguments(class_node)

        assert_that(bases, is_(["Base1", "Base2"]))

    def test_class_base_arguments_returns_empty_without_bases(self, mocker):
        """Verify class_base_arguments returns an empty list for classes without base classes."""
        self._patch_factory(mocker, "class Child:\n    pass")
        subject = UnitToPytest("test_foo.py")
        class_node = subject.find_semantic_kind(SemanticKind.CLASS)[0]

        bases = subject.class_base_arguments(class_node)

        assert_that(bases, is_([]))

    def test_class_declares_base_checks_base_membership(self, mocker):
        """Verify class_declares_base reports whether a requested base class is present."""
        self._patch_factory(mocker, "class Child(Base):\n    pass")
        subject = UnitToPytest("test_foo.py")
        class_node = subject.find_semantic_kind(SemanticKind.CLASS)[0]

        assert_that(subject.class_declares_base(class_node, "Base"), is_(True))
        assert_that(subject.class_declares_base(class_node, "Other"), is_(False))

    def test_class_declares_base_does_not_follow_transitive_inheritance(self, mocker):
        """Verify class_declares_base checks only direct bases, not transitive ancestors."""
        self._patch_factory(
            mocker,
            """
            class Top:
                pass

            class Middle(Top):
                pass

            class Bottom(Middle):
                pass
            """,
        )
        subject = UnitToPytest("test_foo.py")
        class_nodes = subject.find_semantic_kind(SemanticKind.CLASS)
        bottom_node = next(node for node in class_nodes if node.name == "Bottom")

        assert_that(subject.class_declares_base(bottom_node, "Middle"), is_(True))
        assert_that(subject.class_declares_base(bottom_node, "Top"), is_(False))

    # ------------------------------------------------------------------
    # process() — skip branch
    # ------------------------------------------------------------------

    def test_process_skips_file_matching_black_list(self, mocker, capsys):
        """AI: Verify process() skips and does not run the refactor when the filename matches the black list."""
        self._patch_factory(mocker, "pass", "utils_for_test_foo.py")
        run_spy = mocker.patch("renaissance.recipes.unit_to_pytest.UnitToPytest.run")
        PythonRefactoring.process("UnitToPytest", "utils_for_test_foo.py")
        captured = capsys.readouterr()
        assert_that(captured.out, contains_string("skipping"))
        assert_that(run_spy.call_count, is_(0))

    def test_process_skips_file_not_matching_white_list(self, mocker, capsys):
        """AI: Verify process() skips and does not run the refactor when the filename doesn't match the white list."""
        self._patch_factory(mocker, "pass", "my_module.py")
        run_spy = mocker.patch("renaissance.recipes.unit_to_pytest.UnitToPytest.run")
        PythonRefactoring.process("UnitToPytest", "my_module.py")
        captured = capsys.readouterr()
        assert_that(captured.out, contains_string("skipping"))
        assert_that(run_spy.call_count, is_(0))

    # ------------------------------------------------------------------
    # process() — run branch
    # ------------------------------------------------------------------

    def test_process_runs_refactor_on_matching_file(self, mocker, capsys):
        """AI: Verify process() runs the refactor when the filename matches both white and black list patterns."""
        self._patch_factory(mocker, "pass", "test_foo.py")
        run_spy = mocker.patch("renaissance.recipes.unit_to_pytest.UnitToPytest.run")
        PythonRefactoring.process("UnitToPytest", "test_foo.py")
        captured = capsys.readouterr()
        assert_that(captured.out, contains_string("refactor"))
        assert_that(run_spy.call_count, is_(1))

    # ------------------------------------------------------------------
    # body property
    # ------------------------------------------------------------------

    def test_body_returns_module_level_statements(self, mocker):
        """AI: Verify the body property returns the module's top-level statements."""
        self._patch_factory(
            mocker,
            """
            x = 1
            y = 2
            """,
            "test_foo.py",
        )

        subject = UnitToPytest("test_foo.py")
        assert_that(len(subject.body), is_(2))

    # ------------------------------------------------------------------
    # find_rst_node
    # ------------------------------------------------------------------

    def test_find_rst_node_returns_wrapper_for_raw_ast_node(self, mocker: MockerFixture) -> None:
        """AI: Verify find_rst_node locates the PythonRstNode wrapping a given raw ast.FunctionDef."""
        self._patch_factory(
            mocker,
            """
            def foo():
                pass
            """,
            "test_foo.py",
        )

        subject = UnitToPytest("test_foo.py")
        root = cast("PythonRstNode", cast("object", subject.root))
        module = cast(ast.Module, root.node)
        target = next(node for node in ast.walk(module) if isinstance(node, ast.FunctionDef))

        found = subject.find_rst_node(target)

        assert_that(found.node, is_(target))

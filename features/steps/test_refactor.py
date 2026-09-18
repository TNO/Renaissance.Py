"""AI: Step definitions for the rewrite-semantics BDD feature scenarios."""

from pathlib import Path

import pytest
from pytest_bdd import given, parsers, scenario, then, when

from renaissance.integrations.python.ast.factory import PythonPatternFactory
from renaissance.integrations.python.ast.rst_node import PythonRstNode
from renaissance.syntax_tree import ASTFactory, ASTRewriter
from renaissance.syntax_tree.match_finder import match_pattern
from steps.conftest import FEATURES_BASE_DIR


class Context(dict):
    """AI: Dict subclass exposing its items as attributes, used to share BDD scenario state."""

    def __getattr__(self, name):
        """AI: Return the dict item named `name` as an attribute."""
        return self[name]

    def __setattr__(self, name, value):
        """AI: Set the dict item named `name` as an attribute."""
        self[name] = value


@pytest.fixture
def context():
    """AI: Provide a fresh `Context` instance for a BDD scenario."""
    return Context()


@scenario(
    "refactor-python-file.feature",
    "python code",
    encoding="utf-8",
    features_base_dir=str(FEATURES_BASE_DIR),
)
def test_refactor_python_file():
    """AI: Scenario test for the 'python code' refactor-python-file.feature scenario."""


@given("'python' programming language")
def init_language_factory(context):
    """AI: Initialize the AST factory for the Python programming language."""
    context["factory"] = ASTFactory(PythonRstNode, "")


@given(parsers.parse("'{file}' file written in that programming language"))
def step_given_file_in_language(context, file):
    """AI: Parse the given file into an AST using the scenario's factory."""
    context["atu"] = context["factory"].create(FEATURES_BASE_DIR / Path(file))


@given(parsers.parse("node '{old}' exits within that AST"))
def step_given_node_exists(context, old):
    """AI: Assert that a node matching the given pattern exists in the AST."""
    pattern_factory = PythonPatternFactory(context["factory"])
    find = pattern_factory.create_statements(old)
    context["result"] = match_pattern(context["atu"].children, find)
    assert context["result"]


@given("a sequence of descendant nodes of that node")
def step_given_descendant_nodes(context):
    """AI: Assert that the matched node has descendant children."""
    assert context["result"][0].nodes[0].children


@when(parsers.parse("that node is replaced by '{replacement}'"))
def step_when_node_replaced(context, replacement):
    """AI: Queue a replacement of the matched node with the given text."""
    context["replacement"] = replacement
    context["rewriter"] = ASTRewriter(context["atu"])
    context["rewriter"].replace(replacement, context["result"][0].nodes)


@when("rewrites replace is performed on that sequence of descendant nodes")
def step_when_rewrites_applied(context):
    """AI: Apply the queued rewrite to the AST."""
    context["rewriter"].apply()


@then("in the modified source file that node is replaced by the given text")
def step_then_replaced_in_source(context):
    """AI: Assert the replacement text appears in the rewritten source."""
    assert context["replacement"] in context["rewriter"].apply_to_string()


@then("all rewrites on that sequence of descendant nodes are not performed or hidden")
def step_then_rewrites_not_performed_or_hidden(context):
    """AI: Assert the rewriter reports pending, unapplied changes."""
    assert context["rewriter"].has_changed()

import pytest
from pytest_bdd import scenario, given, when, then

from impl import PythonASTNode
from syntax_tree import ASTFactory, ASTFinder

@pytest.fixture
def context():
    return {"factory": None,
            "atu": None,
            }
@scenario('../refactor-python-file.feature', 'python code')
def test_refactor_python_file():
    pass

@given("'python' programming language")
def step_impl():
    context["factory"] = ASTFactory(PythonASTNode, '')


@given("'example/demo.py' file written in that programming language")
def step_impl():
    context["atu"] = context["factory"].create('example/demo.py')

@given("an AST extracted from that source file without errors")
def step_impl():
    context["atu"].check_diagnostics()


@given("node 'some_old_fun' exits within that AST")
def step_impl():
    result = ASTFinder.find_all(context["atu"], 'some_old_fun')
    assert result is not None

@given("a sequence of descendant nodes of that node")
def step_impl():
    pass # raise NotImplementedError(u'STEP: And	a sequence of descendant nodes of that node')


@when("that node is replaced by a text")
def step_impl():
    pass # raise NotImplementedError(u'STEP: When that node is replaced by a text')


@given("Rewrites replace is performed on that sequence of descendant nodes")
def step_impl():
    pass # raise NotImplementedError(u'STEP: And	Rewrites replace is performed on that sequence of descendant nodes')


@then("in the modified source file that node is replaced by the given text")
def step_impl():
    pass # raise NotImplementedError(u'STEP: Then in the modified source file that node is replaced by the given text')


@given("all rewrites on that sequence of descendant nodes are not performed / hidden")
def step_impl():
    pass # raise NotImplementedError(u'STEP: And all rewrites on that sequence of descendant nodes are not performed / hidden')
@when("rewrites replace is performed on that sequence of descendant nodes")
def step_impl():
    pass # raise NotImplementedError(u'STEP: And all rewrites on that sequence of descendant nodes are not performed / hidden')
@then( "all rewrites on that sequence of descendant nodes are not performed / hidden")
def step_impl():
    pass
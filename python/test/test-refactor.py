from pytest_bdd import scenario, given, when, then

@scenario('../features/refactor-python-file.feature', 'python code')
def test_refactor_python_file():
    pass



@given("'python' programming language")
def step_impl():
    pass # raise NotImplementedError(u'STEP: Given	\'python\' programming language')


@given("a source file written in that programming language")
def step_impl():
    pass # raise NotImplementedError(u'STEP: And	a source file written in that programming language')


@given("an AST extracted from that source file without errors")
def step_impl():
    pass # raise NotImplementedError(u'STEP: And	an AST extracted from that source file without errors')


@given("a node of that AST")
def step_impl():
    pass # raise NotImplementedError(u'STEP: And	a node of that AST')


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
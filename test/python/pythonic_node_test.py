import ast

from hamcrest import assert_that, is_, not_none

from renaissance.impl.python import PythonASTNode


class TestPythonicNode:
    def test_it_can_be_created(self):
        it = PythonASTNode(ast.Pass())
        assert_that(it, is_(not_none()))


    def test_it_has_elements(self):
        it = PythonASTNode(ast.parse('def fun():  pass'))
        assert_that(it[0], is_(it.children[0]))




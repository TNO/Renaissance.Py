import ast

from hamcrest import assert_that, is_, not_none

from renaissance.impl.python import PythonRstNode


class TestPythonicNode:
    def test_it_can_be_created(self):
        it = PythonRstNode(ast.Pass())
        assert_that(it, is_(not_none()))

    def test_it_has_elements(self):
        it = PythonRstNode(ast.parse("def fun():  pass"))
        assert_that(it[0], is_(it.children[0]))

    def test_it_has_multiple_elements(self):
        it = PythonRstNode(ast.parse("def fun():  pass"))
        it = PythonRstNode(ast.parse("0\n1\n2\n3\n4\n5\n6\n7\n8\n9\n"))
        assert_that(it[1:3], is_(it.children[1:3]))

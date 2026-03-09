import hamcrest
from black import Path
from hamcrest import assert_that, is_, contains_string

from renaissance.impl.python import PythonASTNode
from renaissance.syntax_tree import ASTRewriter
from renaissance.refactoring.unit2pytest import remove_class, convert_test_cases

code = '''
class TestExample(TestCase):
    def  test_fun(self):  
        self.arrage_1.prepare()
        arrange('other stuff')

        actual = act()

        assertEqual(expected , actual )
'''


def test_remove_class():
    atu = PythonASTNode.load_from_text(code, Path('unknown.py'),[],None)
    result = remove_class(atu)
    assert_that(result, not contains_string('class TestExample'))

def test_convert_test_cases():
    atu = PythonASTNode.load_from_text(code, Path('unknown.py'),[],None)
    result = convert_test_cases(atu)
    assert_that(result, not contains_string('(TestCase)'))


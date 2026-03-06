import hamcrest
from hamcrest import assert_that, is_

from renaissance.impl.python import PythonASTNode
from renaissance.syntax_tree import ASTRewriter
from renaissance.refactoring.unit2pytest import remove_class


code = '''
class TestExample(TestCase)
:
    def  test_fun(self):  
        self.arrage_1.prepare()
        arrange('other stuff')

        actual = act()

        assertEqual(expected , actual )
'''


def test_remove_class():
    atu = PythonASTNode.load_from_text(code, 'unknown.py')
    result = remove_class(atu)
    assert_that(result, is_('')) #not hamcrest.contains_string('class TestExample'))

def convert(atu):
    rewriter = ASTRewriter(atu)
    pattern_factory = PythonPatternFactory(factory, atu)
    # remove_class(pattern_factory, atu, rewriter)
    convert_test_cases(pattern_factory, atu, rewriter)
    rewriter.apply()
    return rewriter.apply_to_string()
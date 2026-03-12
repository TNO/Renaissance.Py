import hamcrest
import pytest
from black import Path
from hamcrest import assert_that, is_, contains_string, has_length

from renaissance.impl.python import PythonASTNode, PythonPatternFactory
from renaissance.syntax_tree import ASTRewriter, ASTFactory
from renaissance.refactoring.unit2pytest import remove_class, convert_test_cases, convert_assert_equals
from renaissance.syntax_tree.match_finder import match_pattern

code = '''
class TestExample(TestCase):
    def  test_fun(self):  
        self.arrage_1.prepare()
        arrange('other stuff')

        actual = target.act()

        self.assertEqual(expected , actual )
'''

@pytest.mark.skip("was working")
def test_remove_class():
    atu = PythonASTNode.load_from_text(code, Path('unknown.py'),[],None)
    result = remove_class(atu)
    assert_that(result, not contains_string('class TestExample'))

@pytest.mark.skip("was working")
def test_convert_test_cases():
    atu = PythonASTNode.load_from_text(code, Path('unknown.py'),[],None)
    result = convert_test_cases(atu)
    assert_that(result, not contains_string('(TestCase)'))

def test_convert_assert_equals():
    factory = ASTFactory(PythonASTNode, [])
    pattern_factory = PythonPatternFactory(factory, None)
    atu = factory.create_from_text(code, Path('unittest.py'))
    rewriter = ASTRewriter(atu)
    convert_assert_equals(pattern_factory, rewriter, atu)
    assert_that(rewriter.apply_to_string(), contains_string(' assert_that(actual, is_(expected))'))
    print(rewriter.apply_to_string())


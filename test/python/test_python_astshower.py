import pytest
from hamcrest import *

from renaissance.impl.python.rst_node import PythonRstNode
from renaissance.impl.python.factory import PythonFactory, PythonPatternFactory

from renaissance.syntax_tree import ASTFactory, ASTShower


class TestPythonShower:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.factory = PythonFactory(PythonRstNode)
        self.atu = self.factory.create_from_text("ba(55)\nca(555)\nlo(4444)\nna=55", "test.py")
        self.pattern_factory = PythonPatternFactory(self.factory)

    def test_show_call_using_repr(self):
        pattern = self.pattern_factory.create_statement("$pa($55)")
        assert_that(str(pattern), is_("(ExpressionStatement, $pa($55), pattern.py[0:28]): |$pa($55)|\n"))

    def test_show_module(self):
        expected = "(TranslationUnit, test.py, test.py[0:29]):\n    |ba(55)|\n    |ca(555)|\n    |lo(4444)|\n    |na=55|\n"
        assert_that(str(self.atu), is_(expected))

    def test_show_body(self):
        expected = (
            "[(ExpressionStatement, ba(55), test.py[0:6]): |ba(55)|\n, (ExpressionStatement, ca(555), test.py[7:14]): |ca(555)|\n,"
            " (ExpressionStatement, lo(4444), test.py[15:23]): |lo(4444)|\n, (Assign, na, test.py[24:29]): |na=55|\n]"
        )

        assert_that(str(self.atu.children), is_(expected))

    def test_show_ast_filter_implicit_node(self):
        ptext = ASTShower.get_node(self.atu)
        assert_that(ptext, not_(contains_string("(ImplicitNode")))

    def test_show_ast(self):
        text = ASTShower.get_node(self.atu)
        expected = (
            "(TranslationUnit, test.py, test.py[0:29]):\n"
            "    |ba(55)|\n"
            "    |ca(555)|\n"
            "    |lo(4444)|\n"
            "    |na=55|\n"
            "  (ExpressionStatement, ba(55), test.py[0:6]): |ba(55)|\n"
            "    (Call, ba(55), test.py[0:6]): |ba(55)|\n"
            "      (Name, ba, test.py[0:2]): |ba|\n"
            "        (Literal, 55, test.py[3:5]): |55|\n"
            "  (ExpressionStatement, ca(555), test.py[7:14]): |ca(555)|\n"
            "    (Call, ca(555), test.py[7:14]): |ca(555)|\n"
            "      (Name, ca, test.py[7:9]): |ca|\n"
            "        (Literal, 555, test.py[10:13]): |555|\n"
            "  (ExpressionStatement, lo(4444), test.py[15:23]): |lo(4444)|\n"
            "    (Call, lo(4444), test.py[15:23]): |lo(4444)|\n"
            "      (Name, lo, test.py[15:17]): |lo|\n"
            "        (Literal, 4444, test.py[18:22]): |4444|\n"
            "  (Assign, na, test.py[24:29]): |na=55|\n"
            "      (Name, na, test.py[24:26]): |na|\n"
            "      (IndentedBlock, args, test.py[0:0]):\n"
            "    (Literal, 55, test.py[27:29]): |55|\n"
        )
        assert_that(text, is_(expected))

    def test_show_if_else(self):
        factory = PythonFactory(PythonRstNode)
        atu = factory.create_from_text(
            """
if x >y :
    x=1
    call(x)
else:
    y=1
    call(y)    
            """,
            "test.py",
        )
        text = ASTShower.get_node(atu.children[0])
        assert_that(
            text,
            is_(
                "(If, If, test.py[1:56]):\n"
                "    |if x >y :|\n"
                "    |    x=1|\n"
                "    |    call(x)|\n"
                "    |else:|\n"
                "    |    y=1|\n"
                "    |    call(y)|\n"
                "  (Compare, x > y, test.py[4:8]): |x >y|\n"
                "    (Name, x, test.py[4:5]): |x|\n"
                "      (GreaterThan, , test.py[0:0]):\n"
                "      (Name, y, test.py[7:8]): |y|\n"
                "    (Assign, x, test.py[15:18]): |x=1|\n"
                "        (Name, x, test.py[15:16]): |x|\n"
                "      (Literal, 1, test.py[17:18]): |1|\n"
                "    (ExpressionStatement, call(x), test.py[23:30]): |call(x)|\n"
                "      (Call, call(x), test.py[23:30]): |call(x)|\n"
                "        (Name, call, test.py[23:27]): |call|\n"
                "          (Name, x, test.py[28:29]): |x|\n"
                "    (Assign, y, test.py[41:44]): |y=1|\n"
                "        (Name, y, test.py[41:42]): |y|\n"
                "      (Literal, 1, test.py[43:44]): |1|\n"
                "    (ExpressionStatement, call(y), test.py[49:56]): |call(y)|\n"
                "      (Call, call(y), test.py[49:56]): |call(y)|\n"
                "        (Name, call, test.py[49:53]): |call|\n"
                "          (Name, y, test.py[54:55]): |y|\n"
            ),
        )


if __name__ == "__main__":
    pytest.main()

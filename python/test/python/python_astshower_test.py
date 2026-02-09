import unittest

from impl import PythonASTNode, PythonPatternFactory

from syntax_tree import ASTFactory, ASTShower


class PythonShowerTest(unittest.TestCase):
    def setUp(self):
        self.factory = ASTFactory(PythonASTNode, [])
        self.atu = self.factory.create_from_text('ba(55)\nca(555)\nlo(4444)\nna=55', 'test.py')
        self.pattern_factory = PythonPatternFactory(self.factory, self.atu)

    def test_show_call_using_repr(self):
        simple = self.pattern_factory.create('$pa($55)')
        self.assertEqual('(Expr, $pa($55), test.py[0:28]): |_MatchOne__pa(_MatchOne__55)|\n', str(simple))

    def test_show_module(self):
        text = ASTShower.get_node(self.atu)
        expected = ('(Module, Module, test.py[0:29]):\n'
 '    |ba(55)|\n'
 '    |ca(555)|\n'
 '    |lo(4444)|\n'
 '    |na=55|\n')
        self.assertEqual(expected, str(self.atu))
    def test_show_body(self):
        text = ASTShower.get_node(self.atu)
        expected =('[  (Expr, ba(55), test.py[0:6]): |ba(55)|\n'
 ',   (Expr, ca(555), test.py[7:14]): |ca(555)|\n'
 ',   (Expr, lo(4444), test.py[15:23]): |lo(4444)|\n'
 ',   (Assign, na = 55, test.py[24:29]): |na=55|\n'
 ']')

        self.assertEqual(expected, str(self.atu.children))

    def test_show_ast_filter_implicite_Node(self):
        ptext = ASTShower.get_node(self.atu)
        self.assertNotIn("(ImplicitNode,",ptext)

    def test_show_ast(self):
        text = ASTShower.get_node(self.atu)
        expected =('(Module, Module, test.py[0:29]):\n'
 '    |ba(55)|\n'
 '    |ca(555)|\n'
 '    |lo(4444)|\n'
 '    |na=55|\n'
 '  (Expr, ba(55), test.py[0:6]): |ba(55)|\n'
 '    (Call, ba(55), test.py[0:6]): |ba(55)|\n'
 '      (Name, ba, test.py[0:2]): |ba|\n'
 '        (Constant, 55, test.py[3:5]): |55|\n'
 '  (Expr, ca(555), test.py[7:14]): |ca(555)|\n'
 '    (Call, ca(555), test.py[7:14]): |ca(555)|\n'
 '      (Name, ca, test.py[7:9]): |ca|\n'
 '        (Constant, 555, test.py[10:13]): |555|\n'
 '  (Expr, lo(4444), test.py[15:23]): |lo(4444)|\n'
 '    (Call, lo(4444), test.py[15:23]): |lo(4444)|\n'
 '      (Name, lo, test.py[15:17]): |lo|\n'
 '        (Constant, 4444, test.py[18:22]): |4444|\n'
 '  (Assign, na = 55, test.py[24:29]): |na=55|\n'
 '      (Name, na, test.py[24:26]): |na|\n'
 '    (Constant, 55, test.py[27:29]): |55|\n')
        self.assertEqual(expected, text)


    def test_show_if_else(self):

        factory = ASTFactory(PythonASTNode, [])
        atu = factory.create_from_text(
'''
if x >y :
    x=1
    call(x)
else:
    y=1
    call(y)    
''', 'test.py')
        text = ASTShower.get_node(atu.children[0])
        self.assertEqual(('(If, If, test.py[1:56]):\n'
 '    |if x >y :|\n'
 '    |    x=1|\n'
 '    |    call(x)|\n'
 '    |else:|\n'
 '    |    y=1|\n'
 '    |    call(y)|\n'
 '  (Compare, x > y, test.py[4:8]): |x >y|\n'
 '    (Name, x, test.py[4:5]): |x|\n'
 '      (Gt, , test.py[0:0]):\n'
 '      (Name, y, test.py[7:8]): |y|\n'
 '    (Assign, x = 1, test.py[15:18]): |x=1|\n'
 '        (Name, x, test.py[15:16]): |x|\n'
 '      (Constant, 1, test.py[17:18]): |1|\n'
 '    (Expr, call(x), test.py[23:30]): |call(x)|\n'
 '      (Call, call(x), test.py[23:30]): |call(x)|\n'
 '        (Name, call, test.py[23:27]): |call|\n'
 '          (Name, x, test.py[28:29]): |x|\n'
 '    (Assign, y = 1, test.py[41:44]): |y=1|\n'
 '        (Name, y, test.py[41:42]): |y|\n'
 '      (Constant, 1, test.py[43:44]): |1|\n'
 '    (Expr, call(y), test.py[49:56]): |call(y)|\n'
 '      (Call, call(y), test.py[49:56]): |call(y)|\n'
 '        (Name, call, test.py[49:53]): |call|\n'
 '          (Name, y, test.py[54:55]): |y|\n'), text)


if __name__ == '__main__':
    unittest.main()

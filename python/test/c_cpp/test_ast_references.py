from unittest import TestCase
from parameterized import parameterized
from syntax_tree import ASTNode, ASTFinder, ASTShower
from .factories import Factories

class TestASTReference(TestCase):

    @parameterized.expand(Factories.factories)
    def test_call_reference(self, _, factory):
        ast =  factory.create_from_text('void f(){} void f1(){ f();}', "test.c")
        call = ASTFinder.find_kind(ast, '(?i)Decl_?Ref_?Expr').find_first().get()
        assert isinstance(call, ASTNode)
        refs = call.get_references()
        self.assertEqual(len(refs), 1)
        ref = refs[0]
        ref_node = ref.get_node()
        self.assertEqual(ASTFinder.matches_kind(ref_node, '(?i)Function_?Decl'), True)
        self.assertEqual(ref_node.get_name(), 'f')
        referenced_by = ref_node.get_referenced_by()
        self.assertGreater(len(referenced_by), 0)  # clang python return 2 references, clang json 1
        self.assertTrue(call in [r.get_node() for r in referenced_by])

    @parameterized.expand(Factories.extend([
        ('int a = 3; int b = a;',...),
        ('int a = 3; void f() {int b = a;}',...),
        ('void f() {int a = 3; int b = a;}',...),
        ('void f(int a) {int b = a;}',...),
    ]))
    def test_var_reference(self, _, factory, code, *args):
        ast =  factory.create_from_text(code, "test.c")
        using = ASTFinder.find_kind(ast, '(?i)Decl_?Ref_?Expr').find_first().get()
        assert isinstance(using, ASTNode)
        refs = using.get_references()
        self.assertEqual(len(refs), 1)
        ref = refs[0]
        ref_node = ref.get_node()
        self.assertEqual(ASTFinder.matches_kind(ref_node, '(?i)(Parm)?(Var)?_?Decl'), True)
        referenced_by = ref_node.get_referenced_by()
        self.assertGreater(len(referenced_by), 0)  # clang python return 2 references, clang json 1
        self.assertTrue(using in [r.get_node() for r in referenced_by])


    @parameterized.expand(Factories.extend([
        ('typedef int a; a b;','c'),
        ('typedef int a; a b;','cpp'),
        ('typedef struct A_Struct {int x; int y;} a; a b;','cpp'),
        ('class A {}; A a={};','cpp'),
    ]))
    def test_type_reference(self, _, factory, code, language):
        ast =  factory.create_from_text(code, "test." +language)
        # in clang python, there is a TYPE_REF below the VAR_DECL node whereas 
        # in clang json the VarDecl node contains the reference
        # use show_node to understand the difference
        # ASTShower.show_node(ast)
        using = ASTFinder.find_kind(ast, '(?i)(Type)_?Ref').\
            filter(lambda n: len(n.get_references())>0).find_first().or_else(None)
        if not using:
            using = ASTFinder.find_kind(ast, '(?i)(Parm)?(Var)?_?Decl').find_first().get()
        assert isinstance(using, ASTNode)
        refs = using.get_references()
        self.assertEqual(len(refs), 1)
        ref = refs[0]
        ref_node = ref.get_node()
        self.assertEqual(ASTFinder.matches_kind(ref_node, '(?i)(CXXRecord|Typedef|Class)?_?Decl'), True)
        referenced_by = ref_node.get_referenced_by()
        self.assertGreater(len(referenced_by), 0)  # clang python returns 2 references, clang json 1
        self.assertTrue(using in [r.get_node() for r in referenced_by])

    @parameterized.expand(Factories.extend([
        ('class A {}; class B: public A {};','cpp'),
        ('class A {}; class B: private A {};','cpp'),
        ('namespace NS {class A {}; class B: private A {};}','cpp'),
        ('struct A {}; class B: public A {};','cpp'),
        ('struct A {}; struct B: private A {};','cpp'),
        ('namespace NS {struct A {}; class B: private A {};}','cpp'),
    ]))
    def test_baseclass_reference(self, _, factory, code, language):
        ast =  factory.create_from_text(code, "test." +language)

        # in clang python, there is a TYPE_REF below the CLASS_DECL node whereas 
        # in clang json there is a bases/base element 
        # use show_node to understand the difference
        # ASTShower.show_node(ast)
        using = ASTFinder.find_kind(ast, '(?i)(Type)_?Ref').find_first().or_else(None)
        if not using:
            using = ASTFinder.find_kind(ast, '(?i)(CXX_?Record)_?Decl').\
                filter(lambda n: n.get_name() == 'B').\
                find_first().get()
        assert isinstance(using, ASTNode)
        refs = using.get_references()
        self.assertEqual(len(refs), 1)
        ref = refs[0]
        ref_node = ref.get_node()
        self.assertEqual(ASTFinder.matches_kind(ref_node, '(?i)(CXX_?Record|Class|Struct)_?Decl'), True)
        referenced_by = ref_node.get_referenced_by()
        self.assertGreater(len(referenced_by), 0)  # clang python return 2 references, clang json 1
        self.assertTrue(using in [r.get_node() for r in referenced_by])

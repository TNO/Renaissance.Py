from unittest import TestCase
from parameterized import parameterized
from syntax_tree import ASTNode, ASTFinder, ASTShower
from .factories import Factories

class TestASTReference(TestCase):

    @parameterized.expand(Factories.extend([
        # disable failing tests
        # ('class A{ public: A(int x); }; void f(){ A a(3);}',...),
        # ('class A{ public: A(int x); }; A::A(int x){} void f(){ A a(3);}',...),
        ('int a(); void f(){ int x = a();}',...),
        ('int a(); int a(){return 0;} void f(){ int x = a();}',...),
        ('int a(){return 0;} void f(){ int x = a();}',...),
    ]))
    def test_definition_declaration_references(self, _, factory, code, *args):
        ast =  factory.create_from_text(code, "test.cpp")
        ASTShower.store_node('c:/temp/c0.txt', ast)
        call = ASTFinder.find_kind(ast, '(Call|CXXConstruct)Expr').find_first().get()
        assert isinstance(call, ASTNode)
        refs = call.references
        self.assertGreater(len(refs), 0)
        refs = [r for r in refs if ASTFinder.matches_kind(r.node, '.*(Constructor|Function).*')]

        self.assertGreater(len(refs), 0)
        for ref in refs:
            ref_node = ref.node
            self.assertEqual(ref_node.name.lower(), 'a')
            referenced_by = ref_node.referenced_by
            self.assertGreater(len(referenced_by), 0)  # clang python return 2 references, clang json 1
            #clang python has a crosse reference to call clang json to the DeclRefExpr child of the call
            self.assertTrue(call.name in [r.node.name for r in referenced_by] or call.children[0].name in [r.node.name for r in referenced_by])
        declarations = ASTFinder.find_kind(ast, '.*(Constructor|Function_?Decl).*').\
            filter(lambda f: f.name != 'f').\
            to_list()
        self.assertGreater(len(declarations), 0)

    @parameterized.expand(Factories.factories)
    def test_call_reference(self, _, factory):
        ast =  factory.create_from_text('void f(){} void f1(){ f();}', "test.c")
        call = ASTFinder.find_kind(ast, 'Decl_?Ref_?Expr').find_first().get()
        assert isinstance(call, ASTNode)
        refs = call.references
        self.assertEqual(len(refs), 1)
        ref = refs[0]
        ref_node = ref.node
        self.assertEqual(ASTFinder.matches_kind(ref_node, 'Function_?Decl'), True)
        self.assertEqual(ref_node.name, 'f')
        referenced_by = ref_node.referenced_by
        self.assertGreater(len(referenced_by), 0)  # clang python return 2 references, clang json 1
        self.assertEqual(call.name,referenced_by[0].node.children[0].name)

        # self.assertTrue(call in [r.node for r in referenced_by])

    @parameterized.expand(Factories.extend([
        ('const int a = 3; const int b = a;',...),
        ('int a = 3; void f() {int b = a;}',...),
        ('void f() {int a = 3; int b = a;}',...),
        ('void f(int a) {int b = a;}',...),
    ]))
    def test_var_reference(self, _, factory, code, *args):
        ast =  factory.create_from_text(code, "test.c")
        using = ASTFinder.find_kind(ast, 'Decl_?Ref_?Expr').find_first().get()
        assert isinstance(using, ASTNode)
        refs = using.references
        self.assertEqual(len(refs), 1)
        ref = refs[0]
        ref_node = ref.node
        self.assertEqual(ASTFinder.matches_kind(ref_node, '(Parm)?(Var)?_?Decl'), True)
        referenced_by = ref_node.referenced_by
        self.assertGreater(len(referenced_by), 0)  # clang python return 2 references, clang json 1
        self.assertTrue(using.text in [r.node.text for r in referenced_by])



    @parameterized.expand(Factories.extend([
        ('typedef int a; a b;','c'),
        ('typedef int a; a b;','cpp'),
        ('typedef struct A_Struct {int x; int y;} a; a b;','cpp'),
        # diable failing test
        # ('class A {}; A a={};','cpp'),
    ]))
    def test_type_reference(self, _, factory, code, language):
        ast =  factory.create_from_text(code, "test." +language)
        # in clang python, there is a TYPE_REF below the VAR_DECL node whereas 
        # in clang json the VarDecl node contains the reference
        # use show_node to understand the difference
        # ASTShower.show_node(ast)
        using = ASTFinder.find_kind(ast, '(Type)_?Ref').\
            filter(lambda n: len(n.references) > 0).find_first().or_else(None)
        if not using:
            using = ASTFinder.find_kind(ast, '(Parm)?(Var)?_?Decl').find_first().get()
        assert isinstance(using, ASTNode)
        refs = using.references
        self.assertEqual(len(refs), 1)
        ref = refs[0]
        ref_node = ref.node
        self.assertEqual(ASTFinder.matches_kind(ref_node, '(CXXRecord|Typedef|Class)?_?Decl'), True)
        referenced_by = ref_node.referenced_by
        self.assertGreater(len(referenced_by), 0)  # clang python returns 2 references, clang json 1
        self.assertTrue(using.text in [r.node.text for r in referenced_by])

    @parameterized.expand(Factories.extend([
        # disable failing tests
        # ('module NS class A: pass; class B(A): pass','cpp'),
        ('class A {}; class B: public A {};','cpp'),
        ('class A {}; class B: private A {};','cpp'),
        ('struct A {}; class B: public A {};','cpp'),
        ('struct A {}; struct B: private A {};','cpp'),
        ('namespace NS {struct A {}; class B: private A {};}','cpp'),
    ]))
    def test_base_class_reference(self, _, factory, code, language):
        ast =  factory.create_from_text(code, "test." +language)

        # in clang python, there is a TYPE_REF below the CLASS_DECL node whereas 
        # in clang json there is a bases/base element 
        # use show_node to understand the difference
        # ASTShower.show_node(ast)
        using = ASTFinder.find_kind(ast, '(Type)_?Ref').find_first().or_else(None)
        if not using:
            using = ASTFinder.find_kind(ast, '(CXX_?Record)_?Decl').\
                filter(lambda n: n.name == 'B').\
                find_first().get()
        assert isinstance(using, ASTNode)
        ASTShower.show_node(using)
        refs = using.references
        self.assertEqual(len(refs), 1)
        ref = refs[0]
        ref_node = ref.node
        self.assertEqual(ASTFinder.matches_kind(ref_node, '(CXX_?Record|Class|Struct)_?Decl'), True)
        referenced_by = ref_node.referenced_by
        self.assertGreater(len(referenced_by), 0)  # clang python return 2 references, clang json 1
        self.assertEqual(using.name,referenced_by[0].node.children[0].name)
        # self.assertTrue(using in [r.node for r in referenced_by])

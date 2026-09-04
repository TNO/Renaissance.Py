import tempfile

import pytest
from hamcrest import assert_that, contains_exactly, contains_string, greater_than, has_length, is_, is_in
from more_itertools.more import first

from renaissance.integrations.clang import ClangASTNode
from renaissance.integrations.types import *
from renaissance.syntax_tree import ASTNode, ASTShower
from renaissance.syntax_tree.ast_finder import find_ast_type, matches_kind

from .factories import Factories


class TestASTReference:
    @pytest.mark.parametrize(
        "_, factory, code, args",
        Factories.extend(
            [
                ("class A{ public: A(int x); }; void f(){ A a(3);}", ...),
                ("class A{ public: A(int x); }; A::A(int x){} void f(){ A a(3);}", ...),
                ("int a(); void f(){ int x = a();}", ...),
                ("int a(); int a(){return 0;} void f(){ int x = a();}", ...),
                ("int a(){return 0;} void f(){ int x = a();}", ...),
            ],
        ),
    )
    def test_definition_declaration_references(self, _, factory, code, args):
        ast = factory.create_from_text(code, "test.cpp")
        with tempfile.TemporaryDirectory() as temp_dir:
            ASTShower.store_node(f"{temp_dir}/c0.txt", ast)
        call = first(find_ast_type(ast, (Call, ConstructorExpression)))
        assert_that(isinstance(call, ASTNode), is_(True))
        refs = call.references
        assert_that(refs, has_length(greater_than(0)))
        refs = [r for r in refs if isinstance(r.node.ast_type(), FunctionDef)]

        assert_that(refs, has_length(greater_than(0)))
        for ref in refs:
            ref_node = ref.node
            assert_that(ref_node.name.lower(), is_("a"))
            referenced_by = ref_node.referenced_by
            assert_that(referenced_by, has_length(greater_than(0)))  # clang python return 2 references, clang json 1
            # clang python has a crosse reference to call clang json to the DeclRefExpr child of the call
            assert_that(call.name in [r.node.name for r in referenced_by] or call.children[0].name in [r.node.name for r in referenced_by])
        declarations = list(n for n in find_ast_type(ast, FunctionDef) if n.name != "f")
        assert_that(declarations, has_length(greater_than(0)))

    @pytest.mark.parametrize("_, factory", Factories.factories)
    def test_call_reference(self, _, factory):
        ast = factory.create_from_text("void f(){} void f1(){ f();}", "test.c")
        call = first(find_ast_type(ast, DeclarationExpression))
        assert_that(isinstance(call, ASTNode), is_(True))
        refs = call.references
        assert_that(refs, has_length(is_(1)))
        ref = refs[0]
        ref_node = ref.node
        assert_that(matches_kind(ref_node, FunctionDef), is_(True))
        assert_that(ref_node.name, is_("f"))
        referenced_by = ref_node.referenced_by
        assert_that(referenced_by, has_length(greater_than(0)))  # clang python return 2 references, clang json 1
        assert_that(referenced_by[0].node.children[0].name, is_(call.name))

    # self.assertTrue(call in [r.node for r in referenced_by])

    @pytest.mark.parametrize(
        "_, factory, code, args",
        Factories.extend(
            [
                ("const int a = 3; const int b = a;", ...),
                ("int a = 3; void f() {int b = a;}", ...),
                ("void f() {int a = 3; int b = a;}", ...),
                ("void f(int a) {int b = a;}", ...),
            ],
        ),
    )
    def test_var_reference(self, _, factory, code, args):
        ast = factory.create_from_text(code, "test.c")
        using = first(find_ast_type(ast, DeclarationExpression))
        assert_that(isinstance(using, ASTNode), is_(True))
        refs = using.references
        assert_that(refs, has_length(is_(1)))
        ref = refs[0]
        ref_node = ref.node
        assert_that(matches_kind(ref_node, (ParameterDef, VariableDef)), is_(True))
        referenced_by = ref_node.referenced_by
        assert_that(referenced_by, has_length(greater_than(0)))  # clang python return 2 references, clang json 1
        assert_that(using.text in [r.node.text for r in referenced_by])

    @pytest.mark.parametrize(
        "_, factory, code, language",
        Factories.extend(
            [
                ("typedef int a; a b;", "c"),
                ("typedef int a; a b;", "cpp"),
                ("typedef struct A_Struct {int x; int y;} a; a b;", "cpp"),
                # disable failing test
                # ('class A {}; A a={};','cpp'),
            ],
        ),
    )
    def test_type_reference(self, _, factory, code, language):
        ast = factory.create_from_text(code, "test." + language)
        # in clang python, there is a TYPE_REF below the VAR_DECL node whereas
        # in clang json the VarDecl node contains the reference
        # use show_node to understand the difference
        # ASTShower.show_node(ast)
        using = first((n for n in find_ast_type(ast, TypeReference) if len(n.references) > 0), None)
        if not using:
            using = first(find_ast_type(ast, (ParameterDef, VariableDef)))
        assert_that(isinstance(using, ASTNode), is_(True))
        refs = using.references
        assert_that(refs, has_length(is_(1)))
        ref = refs[0]
        ref_node = ref.node
        assert_that(matches_kind(ref_node, (RecordDef, TypedefDef, ClassDef)), is_(True))
        referenced_by = ref_node.referenced_by
        assert_that(referenced_by, has_length(greater_than(0)))  # clang python returns 2 references, clang json 1
        assert_that(using.text in [r.node.text for r in referenced_by])

    @pytest.mark.parametrize(
        "_, factory, code, language",
        Factories.extend(
            [
                ("class A {}; class B: public A {};", "cpp"),
                ("class A {}; class B: private A {};", "cpp"),
                ("struct A {}; class B: public A {};", "cpp"),
                ("struct A {}; struct B: private A {};", "cpp"),
                ("namespace NS {struct A {}; class B: private A {};}", "cpp"),
            ],
        ),
    )
    def test_base_class_reference(self, _, factory, code, language):
        ast = factory.create_from_text(code, "test." + language)

        # in clang python, there is a TYPE_REF below the CLASS_DECL node whereas
        # in clang json there is a bases/base element
        # use show_node to understand the difference
        using = first(find_ast_type(ast, TypeReference), None)
        if not using:
            using = first(n for n in find_ast_type(ast, RecordDef) if n.name == "B")
        assert_that(isinstance(using, ASTNode), is_(True))
        refs = using.references
        assert_that(refs, has_length(is_(1)))
        ref = refs[0]
        ref_node = ref.node
        assert_that(isinstance(ref_node.ast_type(), (RecordDef, ClassDef, StructDef)))
        referenced_by = ref_node.referenced_by
        assert_that(referenced_by, has_length(greater_than(0)))  # clang python return 2 references, clang json 1
        name = referenced_by[0].node.children[0].name if len(referenced_by[0].node.children) else referenced_by[0].node.name
        if isinstance(using, ClangASTNode):
            assert_that(name, is_in(using.name))
            for r in referenced_by:
                assert_that(r.node.signature, contains_string(using.signature))
        else:
            assert_that(name, is_(using.name))
            assert_that([r.node for r in referenced_by], contains_exactly(using))

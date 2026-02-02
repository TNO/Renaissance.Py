from unittest import TestCase
from parameterized import parameterized

from impl import ClangJsonASTNode, ClangASTNode
from syntax_tree import ASTRewriter, CPatternFactory, MatchFinder, ASTFactory, ASTNode, ASTShower
from typing import Callable, Sequence
from utils_for_tests import compress

from syntax_tree.ast_processor import ASTProcessor

from c_cpp.factories import Factories

VERBOSE = False
AST_SHOWER = False
class TestCommentLocation(TestCase):

    @parameterized.expand([
        ("single_line_comment", 0, 50, b"Some code // this is a comment\nMore code", (10, 30)),
        ("double_line_comment", 0, 50, b"Some code// one\n // two\nMore code", (17, 23)),
        ("block_comment", 0, 50, b"Some code /* this is a block comment */ More code", (10, 39)),
        ("hash_comment", 0, 50, b"Some code # this is a hash comment\nMore code", (10, 34)),
        ("no_comment", 0, 50, b"Some code with no comment\nMore code", (-1, -1)),
        ("comment_outside_range", 0, 10, b"Some code // this is a comment\nMore code", (-1, -1)),
        ("multiple_comments", 0, 50, b"Some code // first comment\nMore code /* second comment */", (10, 26)),
    ])
    def test(self, _, start_offset: int, stop_offset: int, content: bytes, expected: tuple[int, int]):
        result = ASTRewriter._get_comment_location(start_offset, stop_offset, content)
        if(result != (-1, -1)):
            print(content[result[0]:result[1]])
        self.assertEqual(result, expected)



class TestRewrites(TestCase):
    def test_passing_case_in_clang(self):
        # action: Callable[[ASTRewriter, str, Sequence[ASTNode], bool, bool], None],
        # factory: ASTFactory,code: str, replacement: str, include_whitespace: bool, include_comments: bool, expected: str):
        factory = ASTFactory(ClangASTNode, [])
        atu = factory.create_from_text("void f() { /* c1 */ /* c2 */ int a=3;\n}", 'test.cpp')
        patternFactory = CPatternFactory(factory)
        declaration_pattern = patternFactory.create_declaration('int a=3;')
        found = MatchFinder.find_all(atu, [declaration_pattern]).to_list()

        rewriter = ASTRewriter(atu)
        for match in found:  # .map(lambda m: m.nodes).to_iterable():
            nodes = match.nodes
            rewriter.insert_before('int b=4;int c=5;', nodes, True, True)
        self.assertEqual('void f() { /* c1 */ int b=4;int c=5;\n /* c2 */ int a=3;\n}', rewriter.apply_to_string())

    def test_failing_case(self):
        # action: Callable[[ASTRewriter, str, Sequence[ASTNode], bool, bool], None],
        # factory: ASTFactory,code: str, replacement: str, include_whitespace: bool, include_comments: bool, expected: str):
        factory = ASTFactory(ClangJsonASTNode, [])
        atu = factory.create_from_text("void f() { /* c1 */ /* c2 */ int a=3;\n}", 'test.cpp')
        patternFactory = CPatternFactory(factory)
        declaration_pattern = patternFactory.create_declaration('int a=3;')
        found = MatchFinder.find_all(atu, [declaration_pattern]).to_list()

        rewriter = ASTRewriter(atu)
        for match in found:  # .map(lambda m: m.nodes).to_iterable():
            nodes = match.nodes
            rewriter.insert_before('int b=4;int c=5;', nodes, True, True)
        self.assertEqual('void f() { /* c1 */ int b=4;int c=5;\n /* c2 */ int a=3;\n}', rewriter.apply_to_string())

    def do_test(self, action: Callable[[ASTRewriter, str, Sequence[ASTNode],bool, bool], None], factory: ASTFactory, code: str, replacement:str, include_whitespace: bool, include_comments: bool, expected: str):
        atu = factory.create_from_text(code, 'test.cpp')
        patternFactory = CPatternFactory(factory)
        declaration_pattern = patternFactory.create_declaration('int a=3;')
        rewriter = ASTRewriter(atu)
        found =MatchFinder.find_all(atu, [declaration_pattern]).to_list()

        for match in found: # .map(lambda m: m.nodes).to_iterable():
            nodes = match.nodes
            action(rewriter,replacement, nodes, include_whitespace, include_comments)
        expected_result = factory.create_from_text(expected, 'test.cpp')
        actual = rewriter.apply_to_string()
        actual_result = factory.create_from_text(rewriter.apply_to_string(), 'test.cpp')
        if AST_SHOWER:
            print("Original:")
            ASTShower.show_node(atu)
            print("Expected:")
            ASTShower.show_node(expected_result)
            print("Actual:")
            ASTShower.show_node(actual_result)
        if VERBOSE:
            print("\nOriginal:" + code.replace('\n', '\\n').replace('\r', '\\r'))
            print("Expected:" + expected.replace('\n', '\\n').replace('\r', '\\r'))
            print("  Actual:" + actual.replace('\n', '\\n').replace('\r', '\\r'))
        
            code_test_input = f'("{code}", {include_whitespace}, {include_comments}, "{actual}"),'.replace('\n', '\\n').replace('\r', '\\r')
            print("\nFull parameterized:" +code_test_input)

        self.assertEqual(expected, rewriter.apply_to_string())

class TestRemove(TestRewrites):

    @parameterized.expand(list(Factories.extend( [
        ("void f() { /* c1 */ int a=3;\n}", True, True, 'void f() { \n}'),
        ("void f() { int x=2; //x cmt\n  int a=3;\n}", True, True, 'void f() { int x=2; //x cmt\n  \n}'),
         ])))   
    def test(self, name, factory: ASTFactory, code: str, include_whitespace, include_comments, expected):
        
        self.do_test(lambda s,_,n,ws,cm: ASTRewriter.remove(s,n,ws,cm), factory, code, 'int aa=4;',include_whitespace, include_comments, expected)


class TestReplace(TestRewrites):

    @parameterized.expand(list(Factories.extend( [
        ("void f() { /* c1 */ int a=3;\n}", True, True, 'void f() { int aa=4;\n}'),
        ("void f() { /* c1 */ /* c2 */ int a=3;\n}", True, True, 'void f() { /* c1 */ int aa=4;\n}'),
        ("void f() { // c1\n int a=3;\n}", True, True, 'void f() { int aa=4;\n}'),
        ("void f() { // c1\n //c2\n int a=3;\n}", True, True, 'void f() { // c1\n int aa=4;\n}'),
        ("void f() { int a=3;    \n}", True, True, 'void f() { int aa=4;\n}'),
        ("void f() { int a=3; //c1    \n}", True, True, 'void f() { int aa=4;\n}'),
        ("void f() { int a=3; /*c1    \n */ }", True, True, 'void f() { int aa=4; }'),
        ("void f() { int a=3; /*c1    \n */ }", False, True, 'void f() { int aa=4; }'),
        ("void f() { int a=3; /*c1    \n */ }", False, False, 'void f() { int aa=4; /*c1    \n */ }'),
        ("/* out scope */ void f() { int a=3; /*c1    \n */ }", True, True, '/* out scope */ void f() { int aa=4; }'),
        ("/* out scope */ void f() { int a=3; /*c1    \n */ }", False, True, '/* out scope */ void f() { int aa=4; }'),
        ("/* out scope */ void f() { int a=3; /*c1    \n */ }", False, False, '/* out scope */ void f() { int aa=4; /*c1    \n */ }'),
        ("void f() { int a=3; /*c1    \n */ }", True, False, 'void f() { int aa=4; /*c1    \n */ }'),
        ("void f() { int a=3; /*c1    \n */ }", False, False, 'void f() { int aa=4; /*c1    \n */ }'),
        #siblings with comments
        ("void f() { int x=2; /* c1 */ int a=3; //c2\n int b=4; }", True, True, 'void f() { int x=2; /* c1 */ int aa=4;\n int b=4; }'),
        ("void f() { //cx\nint x=2; //ca\n int a=3; //caa\n int b=4;//cb \n}", True, True, 'void f() { //cx\nint x=2; //ca\n int aa=4;\n int b=4;//cb \n}'),
        ("void f() { int x=2; /*ca*/ int a=3; /*caa \n nl*/ int b=4; }", True, True, 'void f() { int x=2; /*ca*/ int aa=4; int b=4; }'),

        
         ])))   
    def test(self, name, factory: ASTFactory, code: str, include_whitespace, include_comments, expected):
        self.do_test(ASTRewriter.replace, factory, code, 'int aa=4;',include_whitespace, include_comments, expected)


class TestInsertBeforeSingleLine(TestRewrites):

    @parameterized.expand(list(Factories.extend( [
        ("/* out scope */ void f() { int a=3; /*c1    \n */ }", False, False, "/* out scope */ void f() { int aa=4;int a=3; /*c1    \n */ }"),
        ("/* out scope */ void f() { int a=3; /*c1    \n */ }", False, True, "/* out scope */ void f() { int aa=4;int a=3; /*c1    \n */ }"),
        ("/* out scope */ void f() { int a=3; /*c1    \n */ }", True, True, "/* out scope */ void f() { int aa=4; int a=3; /*c1    \n */ }"),
        ("void f() { /* c1 */ /* c2 */ int a=3;\n}", True, True, "void f() { /* c1 */ int aa=4;\n /* c2 */ int a=3;\n}"),
        ("void f() { /* c1 */ int a=3;\n}", True, True, "void f() { int aa=4;\n /* c1 */ int a=3;\n}"),
        ("void f() { // c1\n //c2\n int a=3;\n}", True, True, "void f() { // c1\n int aa=4;\n //c2\n int a=3;\n}"),
        ("void f() { // c1\n int a=3;\n}", True, True, "void f() { int aa=4;\n // c1\n int a=3;\n}"),
        ("void f() { //cx\n int x=2; //ca\n int a=3; //caa\n int b=4;//cb \n}", True, True, "void f() { //cx\n int x=2; //ca\n int aa=4;\n int a=3; //caa\n int b=4;//cb \n}"),
        ("void f() { int a=3;    \n}", True, True, "void f() { int aa=4;\n int a=3;    \n}"),
        ("void f() { int a=3; /*c1    \n */ }", False, False, "void f() { int aa=4;int a=3; /*c1    \n */ }"),
        ("void f() { int a=3; /*c1    \n */ }", False, True, "void f() { int aa=4;int a=3; /*c1    \n */ }"),
        ("void f() { int a=3; /*c1    \n */ }", True, False, "void f() { int aa=4; int a=3; /*c1    \n */ }"),
        ("void f() { int a=3; /*c1    \n */ }", True, True, "void f() { int aa=4; int a=3; /*c1    \n */ }"),
        ("void f() { int a=3; //c1    \n}", True, True, "void f() { int aa=4;\n int a=3; //c1    \n}"),
        ("void f() { int x=2; /*ca*/ int a=3; /*caa \n nl*/ int b=4; }", True, True, "void f() { int x=2; /*ca*/ int aa=4; int a=3; /*caa \n nl*/ int b=4; }"),
        ("void f() { int x=2; /* c1 */ int a=3; //c2\n int b=4; }", True, True, "void f() { int x=2; /* c1 */ int aa=4;\n int a=3; //c2\n int b=4; }"),
        ("void f() { int x=2; //c1\n int a=3; //caa\n int b=4;//cb \n}", True, True, "void f() { int x=2; //c1\n int aa=4;\n int a=3; //caa\n int b=4;//cb \n}")
         ])))   
    def test(self, name, factory: ASTFactory, code: str, include_whitespace, include_comments, expected):
        self.do_test(ASTRewriter.insert_before, factory, code,'int aa=4;', include_whitespace, include_comments, expected)

class TestInsertBeforeMultiLine(TestRewrites):

    @parameterized.expand(list(Factories.extend( [
        ("/* out scope */ void f() { int a=3; /*c1    \n */ }", False, False, "/* out scope */ void f() { int aa=4;\n int bb=5;int a=3; /*c1    \n */ }"),
        ("/* out scope */ void f() { int a=3; /*c1    \n */ }", False, True, "/* out scope */ void f() { int aa=4;\n int bb=5;int a=3; /*c1    \n */ }"),
        ("/* out scope */ void f() { int a=3; /*c1    \n */ }", True, True, "/* out scope */ void f() { int aa=4;\n int bb=5; int a=3; /*c1    \n */ }"),
        ("/* indent 2 */ void f() {\n  int a=3; /*c1    \n */ }", False, False, "/* indent 2 */ void f() {\n  int aa=4;\n  int bb=5;int a=3; /*c1    \n */ }"),
        ("/* indent 2 */ void f() {\n  int a=3; /*c1    \n */ }", False, True, "/* indent 2 */ void f() {\n  int aa=4;\n  int bb=5;int a=3; /*c1    \n */ }"),
        ("/* indent 2 */ void f() {\n  int a=3; /*c1    \n */ }", True, True, "/* indent 2 */ void f() {\n  int aa=4;\n  int bb=5;  int a=3; /*c1    \n */ }"),
        ("void f() { /* c1 */ /* c2 */ int a=3;\n}", True, True, "void f() { /* c1 */ int aa=4;\n int bb=5;\n /* c2 */ int a=3;\n}"),
        ("void f() { /* c1 */ int a=3;\n}", True, True, "void f() { int aa=4;\n int bb=5;\n /* c1 */ int a=3;\n}"),
        ("void f() { // c1\n //c2\n int a=3;\n}", True, True, "void f() { // c1\n int aa=4;\n int bb=5;\n //c2\n int a=3;\n}"),
        ("void f() { // c1\n int a=3;\n}", True, True, "void f() { int aa=4;\n int bb=5;\n // c1\n int a=3;\n}"),
        ("void f() { //cx\n int x=2; //ca\n int a=3; //caa\n int b=4;//cb \n}", True, True, "void f() { //cx\n int x=2; //ca\n int aa=4;\n int bb=5;\n int a=3; //caa\n int b=4;//cb \n}"),
        ("void f() { int a=3;    \n}", True, True, "void f() { int aa=4;\n int bb=5;\n int a=3;    \n}"),
        ("void f() { int a=3; /*c1    \n */ }", False, False, "void f() { int aa=4;\n int bb=5;int a=3; /*c1    \n */ }"),
        ("void f() { int a=3; /*c1    \n */ }", False, True, "void f() { int aa=4;\n int bb=5;int a=3; /*c1    \n */ }"),
        ("void f() { int a=3; /*c1    \n */ }", True, False, "void f() { int aa=4;\n int bb=5; int a=3; /*c1    \n */ }"),
        ("void f() { int a=3; /*c1    \n */ }", True, True, "void f() { int aa=4;\n int bb=5; int a=3; /*c1    \n */ }"),
        ("void f() { int a=3; //c1    \n}", True, True, "void f() { int aa=4;\n int bb=5;\n int a=3; //c1    \n}"),
        ("void f() { int x=2; /*ca*/ int a=3; /*caa \n nl*/ int b=4; }", True, True, "void f() { int x=2; /*ca*/ int aa=4;\n int bb=5; int a=3; /*caa \n nl*/ int b=4; }"),
        ("void f() { int x=2; /* c1 */ int a=3; //c2\n int b=4; }", True, True, "void f() { int x=2; /* c1 */ int aa=4;\n int bb=5;\n int a=3; //c2\n int b=4; }"),
        ("void f() { int x=2; //c1\n int a=3; //caa\n int b=4;//cb \n}", True, True, "void f() { int x=2; //c1\n int aa=4;\n int bb=5;\n int a=3; //caa\n int b=4;//cb \n}"),

        
         ])))   
    def test(self, name, factory: ASTFactory, code: str, include_whitespace, include_comments, expected):
        self.do_test(ASTRewriter.insert_before, factory, code,'int aa=4;\nint bb=5;', include_whitespace, include_comments, expected)

class TestInsertAfterSingleLine(TestRewrites):

    @parameterized.expand(list(Factories.extend( [
        ("/* out scope */ void f() { int a=3; /*c1    \n */ }", False, False, "/* out scope */ void f() { int a=3;int aa=4; /*c1    \n */ }"),
        ("/* out scope */ void f() { int a=3; /*c1    \n */ }", False, True, "/* out scope */ void f() { int a=3; /*c1    \n */int aa=4; }"),
        ("/* out scope */ void f() { int a=3; /*c1    \n */ }", True, True, "/* out scope */ void f() { int a=3; /*c1    \n */ int aa=4; }"),
        ("void f() { /* c1 */ /* c2 */ int a=3;\n}", True, True, "void f() { /* c1 */ /* c2 */ int a=3;\n int aa=4;\n}"),
        ("void f() { /* c1 */ int a=3;\n}", True, True, "void f() { /* c1 */ int a=3;\n int aa=4;\n}"),
        ("void f() { // c1\n //c2\n int a=3;\n}", True, True, "void f() { // c1\n //c2\n int a=3;\n int aa=4;\n}"),
        ("void f() { // c1\n int a=3;\n}", True, True, "void f() { // c1\n int a=3;\n int aa=4;\n}"),
        ("void f() { //cx\nint x=2; //ca\n int a=3; //caa\n int b=4;//cb \n}", True, True, "void f() { //cx\nint x=2; //ca\n int a=3; //caa\n int aa=4;\n int b=4;//cb \n}"),
        ("void f() { int a=3;    \n}", True, True, "void f() { int a=3;    \n int aa=4;\n}"),
        ("void f() { int a=3; /*c1    \n */ }", False, False, "void f() { int a=3;int aa=4; /*c1    \n */ }"),
        ("void f() { int a=3; /*c1    \n */ }", False, True, "void f() { int a=3; /*c1    \n */int aa=4; }"),
        ("void f() { int a=3; /*c1    \n */ }", True, False, "void f() { int a=3; int aa=4; /*c1    \n */ }"),
        ("void f() { int a=3; /*c1    \n */ }", True, True, "void f() { int a=3; /*c1    \n */ int aa=4; }"),
        ("void f() { int a=3; //c1    \n}", True, True, "void f() { int a=3; //c1    \n int aa=4;\n}"),
        ("void f() { int x=2; /*ca*/ int a=3; /*caa \n nl*/ int b=4; }", True, True, "void f() { int x=2; /*ca*/ int a=3; /*caa \n nl*/ int aa=4; int b=4; }"),
        ("void f() { int x=2; /* c1 */ int a=3; //c2\n int b=4; }", True, True, "void f() { int x=2; /* c1 */ int a=3; //c2\n int aa=4;\n int b=4; }"),
        ("void f() { int x=2; //c1\n int a=3; //caa\n int b=4;//cb \n}", True, True, "void f() { int x=2; //c1\n int a=3; //caa\n int aa=4;\n int b=4;//cb \n}"),
    ])))   
    def test(self, name, factory: ASTFactory, code: str, include_whitespace, include_comments, expected):
        self.do_test(ASTRewriter.insert_after, factory, code,'int aa=4;', include_whitespace, include_comments, expected)

class TestInsertAfterMultiLine(TestRewrites):

    @parameterized.expand(list(Factories.extend( [
        ("/* indent 2 */ void f() {\n  int a=3; /*c1    \n */ }", False, False, "/* indent 2 */ void f() {\n  int a=3;int aa=4;\n  int bb=5; /*c1    \n */ }"),
        ("/* indent 2 */ void f() {\n  int a=3; /*c1    \n */ }", False, True, "/* indent 2 */ void f() {\n  int a=3; /*c1    \n */int aa=4;\n  int bb=5; }"),
        ("/* indent 2 */ void f() {\n  int a=3; /*c1    \n */ }", True, True, "/* indent 2 */ void f() {\n  int a=3; /*c1    \n */  int aa=4;\n  int bb=5; }"),
        ("/* out scope */ void f() { int a=3; /*c1    \n */ }", False, False, "/* out scope */ void f() { int a=3;int aa=4;\n int bb=5; /*c1    \n */ }"),
        ("/* out scope */ void f() { int a=3; /*c1    \n */ }", False, True, "/* out scope */ void f() { int a=3; /*c1    \n */int aa=4;\n int bb=5; }"),
        ("/* out scope */ void f() { int a=3; /*c1    \n */ }", True, True, "/* out scope */ void f() { int a=3; /*c1    \n */ int aa=4;\n int bb=5; }"),
        ("void f() { /* c1 */ /* c2 */ int a=3;\n}", True, True, "void f() { /* c1 */ /* c2 */ int a=3;\n int aa=4;\n int bb=5;\n}"),
        ("void f() { /* c1 */ int a=3;\n}", True, True, "void f() { /* c1 */ int a=3;\n int aa=4;\n int bb=5;\n}"),
        ("void f() { // c1\n //c2\n int a=3;\n}", True, True, "void f() { // c1\n //c2\n int a=3;\n int aa=4;\n int bb=5;\n}"),
        ("void f() { // c1\n int a=3;\n}", True, True, "void f() { // c1\n int a=3;\n int aa=4;\n int bb=5;\n}"),
        ("void f() { //cx\nint x=2; //ca\n int a=3; //caa\n int b=4;//cb \n}", True, True, "void f() { //cx\nint x=2; //ca\n int a=3; //caa\n int aa=4;\n int bb=5;\n int b=4;//cb \n}"),
        ("void f() { int a=3;    \n}", True, True, "void f() { int a=3;    \n int aa=4;\n int bb=5;\n}"),
        ("void f() { int a=3; /*c1    \n */ }", False, False, "void f() { int a=3;int aa=4;\n int bb=5; /*c1    \n */ }"),
        ("void f() { int a=3; /*c1    \n */ }", False, True, "void f() { int a=3; /*c1    \n */int aa=4;\n int bb=5; }"),
        ("void f() { int a=3; /*c1    \n */ }", True, False, "void f() { int a=3; int aa=4;\n int bb=5; /*c1    \n */ }"),
        ("void f() { int a=3; /*c1    \n */ }", True, True, "void f() { int a=3; /*c1    \n */ int aa=4;\n int bb=5; }"),
        ("void f() { int a=3; //c1    \n}", True, True, "void f() { int a=3; //c1    \n int aa=4;\n int bb=5;\n}"),
        ("void f() { int x=2; /*ca*/ int a=3; /*caa \n nl*/ int b=4; }", True, True, "void f() { int x=2; /*ca*/ int a=3; /*caa \n nl*/ int aa=4;\n int bb=5; int b=4; }"),
        ("void f() { int x=2; /* c1 */ int a=3; //c2\n int b=4; }", True, True, "void f() { int x=2; /* c1 */ int a=3; //c2\n int aa=4;\n int bb=5;\n int b=4; }"),
        ("void f() { int x=2; //c1\n int a=3; //caa\n int b=4;//cb \n}", True, True, "void f() { int x=2; //c1\n int a=3; //caa\n int aa=4;\n int bb=5;\n int b=4;//cb \n}"),
    ])))   
    def test(self, name, factory: ASTFactory, code: str, include_whitespace, include_comments, expected):
        self.do_test(ASTRewriter.insert_after, factory, code, 'int aa=4;\nint bb=5;', include_whitespace, include_comments, expected)


class TestComposeReplacement(TestCase):

    @parameterized.expand(Factories.extend([
    ('if($exp){$$before;b=$d1;$$after;}else{$$before;b=$d2;$$after;}',[],{'$$before; b = ($exp) ? $d1:$d2; $$after;': "int a=1;int b=2;int c=3;int d=4;void f(){c++;b=(a==1)?2:3;d++;}"}),   
]))
    def test_args(self, _, factory, statements, extra_declarations, replacement: dict[str, str]):
        code = """
        int a = 1;
        int b = 2;
        int c = 3;
        int d = 4;
        void f(){
            if (a==1) {
                c++;
                b = 2;
                d++;
            }
            else {
                c++;
                b = 3;
                d++;
            }
        }
        """
        atu = factory.create_from_text(code, 'test.cpp')
        stmtNodes = CPatternFactory(factory).create_statements(statements, extra_declarations=extra_declarations)
        matches = MatchFinder.find_all([atu],stmtNodes).\
            filter(lambda match: match.src_nodes[0].is_part_of_translation_unit()).to_list()

        for match, exp in zip(matches, replacement.items()):
            rewriter = ASTRewriter(match.src_nodes[0].root)
            org, expected = exp
            rewriter.replace(org, match)
            actual = rewriter.apply_to_string()
            self.assertEqual(compress(actual), compress(expected))  

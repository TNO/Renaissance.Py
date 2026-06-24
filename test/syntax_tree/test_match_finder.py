from __future__ import annotations

from hamcrest import assert_that, is_, has_length

from renaissance.impl.clang import ClangASTNode, CPatternFactory
from renaissance.syntax_tree import ASTFactory
from renaissance.syntax_tree.match_finder import find_in_list, MatchFinder

VERBOSE = False
DEFAULT_EXCLUDE_KIND = "comment"

code = """
int one(int a);
int two(int a, int b);
int three(int a, int b, int c);
int a,b,c;
void f(){
    one(a);
    two(a,b);
    three(a,b,c);
}
"""
statements = "$f($a, $$all);"
extra_declarations = ["int $f(int,int);"]
result = [
    {"$f": ["one"], "$a": ["a"], "$$all": []},
    {"$f": ["two"], "$a": ["a"], "$$all": ["b"]},
    {"$f": ["three"], "$a": ["a"], "$$all": ["b", "c"]},
]


class TestMatchFinder:
    def test_find_in_tree_one_and_all_params(self):
        factory = ASTFactory(ClangASTNode, [])
        patterns = [CPatternFactory(factory).create_statements(statements, extra_declarations=extra_declarations)]

        atu = factory.create_from_text(code, "test.c")
        src = atu.children[-1].children[-1].children
        found_position = find_in_list(src, patterns[0], {})
        assert_that(found_position, is_(0))

    def test_find_in_tree_one_and_all_params_2(self):
        factory = ASTFactory(ClangASTNode, [])
        patterns = [CPatternFactory(factory).create_statements(statements, extra_declarations=extra_declarations)]

        atu = factory.create_from_text(code, "test.c")
        src = atu.children[-1].children[-1].children
        found_position = find_in_list(src[1:], patterns[0], {})
        assert_that(found_position, is_(0))

    def test_find_in_tree_one_and_all_params_3(self):
        factory = ASTFactory(ClangASTNode, [])
        patterns = [CPatternFactory(factory).create_statements(statements, extra_declarations=extra_declarations)]

        atu = factory.create_from_text(code, "test.c")
        src = atu.children[-1].children[-1].children
        found_position = find_in_list(src[2:], patterns[0], {})
        assert_that(found_position, is_(0))

    def test_match_one_and_all_params(self):
        factory = ASTFactory(ClangASTNode, [])
        patterns = [CPatternFactory(factory).create_statements(statements, extra_declarations=extra_declarations)]

        atu = factory.create_from_text(code, "test.c")
        src = atu.children[-1].children[-1].children
        # find all if and while statements
        matches = MatchFinder.match_pattern(src, patterns[0])
        assert_that(matches, has_length(3))

# This script demonstrates various techniques for refactoring C code using an abstract syntax tree (AST) approach.
# It showcases how to add comments, replace types, and find specific nodes in the AST using different methods.
from renaissance.impl.types import TypeReference
from renaissance.syntax_tree import (
    ASTFactory,
    ASTRewriter,
    ASTShower,
    ASTFinder,
)
from renaissance.impl.clang import ClangASTNode, CPatternFactory
from renaissance.syntax_tree.ast_finder import find_ast_type, matches_kind
from renaissance.syntax_tree.match_finder import match_pattern, find_all

example_code = """
    typedef int fancy_new;
    typedef int old;
    void f(){
        int a = 1;
        old b = 2;
        int c = 3;
        old d = 4;
        old e;
    }
    """
expected_result_old_fancy_new = """
    typedef int fancy_new;
    typedef int old;
    void f(){
        int a = 1;
        fancy_new b = 2;
        int c = 3;
        fancy_new d = 4;
        fancy_new e;
    }
    """.strip()

expected_result_old_with_comment = """
    typedef int fancy_new;
    typedef int old;
    void f(){
        int a = 1;
        // old has become obsolete
        old b = 2;
        int c = 3;
        // old has become obsolete
        old d = 4;
        // old has become obsolete
        old e;
    }
    """.strip()


def example_add_comment_and_commit(factory, pattern_factory):
    # create a pattern that matches the declaration of old
    # please note that we need to help by telling the old is a type and $value is a variable
    pattern1 = pattern_factory.create_declarations(
        "old $name = $value;",
        extra_declarations=["typedef int old;"],
        parameters=["$value"],
    )
    pattern2 = pattern_factory.create_declarations("old $name;", extra_declarations=["typedef int old;"], parameters=["$value"])
    # put the patterns in a matrix because we want to find both statements in one go and not a sequence
    patterns_list = [pattern1, pattern2]

    ASTShower.show_node(pattern1[0])
    # if you want to find both statements in one go, you should pass a list of patterns
    # if you don't do that a sequence of the patterns is searched for

    # create translation unit
    atu = factory.create_from_text(example_code, "test.c")

    ASTShower.show_node(atu)

    # create an ASTRewriter
    rewriter = ASTRewriter(atu)

    # search matches and replace them
    for match in find_all(atu.children, *patterns_list):
        rewriter.insert_before("// old has become obsolete", match)

    def commit():
        rewriter.apply_to_string()
        atu = factory.create_from_text(rewriter.apply_to_string(), rewriter.get_filename())
        return atu, ASTRewriter(atu)

    # commit
    atu, rewriter = commit()

    # look at the print that marks all old declarations with the provided comment
    print("results after adding comments to the obsolete types:")
    result = rewriter.apply_to_string().strip()
    print(result)
    return result, expected_result_old_with_comment


def example_replace_old_by_fancy_new(factory, pattern_factory):
    # using some different techniques to show the possibilities of map and filter
    pattern1 = pattern_factory.create_declarations("$old $name = $value;", types=["$old"], parameters=["$value"])
    pattern2 = pattern_factory.create_declarations("$old $name;", types=["$old"], parameters=["$value"])
    # put the patterns in a matrix because we want to find both statements in one go and not a sequence
    patterns_list = [pattern1, pattern2]

    # an example of how to use a function iso of lambda to filter the nodes
    def matches_old(node):
        if "$old" in node and node["$old"][0].name == "old":
            return True
        return False

    atu = factory.create_from_text(example_code, "test.c")
    rewriter = ASTRewriter(atu)

    [rewriter.replace("fancy_new", match.nodes) for match in match_pattern(atu.children, *patterns_list) if matches_old(match.expansions)]

    print("results after replacing the old type by fancy_new using MatchFinder:")
    result = rewriter.apply_to_string().strip()
    print(result)
    return result, expected_result_old_fancy_new


def example_use_ast_kind_finder(factory, _):
    # Create the translation unit from the provided code or example code
    atu = factory.create_from_text(example_code, "test.c")
    # Create an ASTRewriter for the translation unit
    rewriter = ASTRewriter(atu)

    # Find all nodes of kind TYPE_REF (case-insensitive) and filter those with name 'old'
    [rewriter.replace("fancy_new", node) for node in find_ast_type(atu, TypeReference) if node.name == "old"]

    # Print the results after replacing the old type by fancy_new
    print("results after replacing the old type by fancy_new using find_ast_type")
    result = rewriter.apply_to_string().strip()
    print(result)
    return result, expected_result_old_fancy_new


def example_use_ast_function_finder(factory, _):
    # Create the translation unit from the provided code or example code
    atu = factory.create_from_text(example_code, "test.c")
    # Create an ASTRewriter for the translation unit
    rewriter = ASTRewriter(atu)

    ASTShower.show_node(atu)

    # Define a match function to find nodes of kind TYPE_REF with name 'old'
    def match(node):
        res = matches_kind(node, TypeReference) and node.name == "old"
        return res

    # Use ASTFinder to find all matching nodes and replace 'old' with 'fancy_new'
    [rewriter.replace("fancy_new", node) for node in ASTFinder.find_all(atu, match)]

    # Print the results after replacing the old type by fancy_new
    print("results after replacing the old type by fancy_new using ASTFinder.find_all")
    result = rewriter.apply_to_string().strip()
    print(result)
    return result, expected_result_old_fancy_new


def main(args):
    # the first argument is the code to be parsed
    code = args[1] if len(args) > 1 else ""

    # Create a factory args from the command line are passed to the factory for example -I/usr/include
    factory = ASTFactory(ClangASTNode, args if not code else args[1:])
    # Create a pattern factory (using the factory (hence also its args)
    pattern_factory = CPatternFactory(factory)

    example_add_comment_and_commit(factory, pattern_factory)
    example_replace_old_by_fancy_new(factory, pattern_factory)
    example_use_ast_kind_finder(factory, pattern_factory)
    example_use_ast_function_finder(factory, pattern_factory)


if __name__ == "__main__":
    import sys

    main(sys.argv)

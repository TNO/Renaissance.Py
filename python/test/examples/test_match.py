from syntax_tree.ast_factory import ASTFactory
from syntax_tree.ast_node import ASTNode
from syntax_tree.c_pattern_factory import CPPPatternFactory
from impl.clang.clang_ast_node import ClangASTNode
from syntax_tree.match_finder import MatchFinder, PatternMatch


import ast

# tree = ast.parse("3*(a+b)", mode="exec")
# print(ast.dump(tree, indent=4))


from hypothesis import given
from hypothesis import strategies as st
from hypothesis.strategies import SearchStrategy


# ----------- Basic operator strategies with type hints -----------

# Binary operator kind (not an expr, just its 'op' field)
bin_ops: SearchStrategy[ast.operator] = st.one_of(
    st.builds(ast.Add),
    st.builds(ast.Sub),
    st.builds(ast.Mult),
    st.builds(ast.Div),
    st.builds(ast.FloorDiv),
    st.builds(ast.Pow),        
    )

# Unary operator kind
un_ops: SearchStrategy[ast.unaryop] = st.one_of(
    st.builds(ast.USub),
    st.builds(ast.UAdd),
)


# ----------- Leaf expression strategy -----------

leaf_exprs: SearchStrategy[ast.expr] = st.one_of(
    # Constant integers
    st.builds(ast.Constant, value=st.integers(min_value=-1000, max_value=1000)),
    # Constant integers
    st.builds(ast.Constant, value=st.floats(min_value=-1000.0, max_value=1000.0)),
    # Variable names (read context)
    st.builds(ast.Name, id=st.sampled_from(["x", "y", "z"]), ctx=st.builds(ast.Load)),
)


# ----------- Expansion combinator for recursive expressions -----------


def expand_exprs(child: SearchStrategy[ast.expr]) -> SearchStrategy[ast.expr]:
    """Given a child expression strategy, build bigger expressions from it."""
    return st.one_of(
        # Unary operation: +/- child
        st.builds(ast.UnaryOp, op=un_ops, operand=child),
        
        # Binary operation: left <op> right
        st.builds(ast.BinOp, left=child, op=bin_ops, right=child),
    )


# ----------- Recursive expression strategy -----------

exprs: SearchStrategy[ast.expr] = st.recursive(
    base=leaf_exprs,
    extend=expand_exprs,
    max_leaves=50,
)


@given(exprs)
def test_single_placeholder_expression(expression: ast.expr) -> None:
    factory: ASTFactory = ASTFactory(ClangASTNode)
    pattern_factory: CPPPatternFactory = CPPPatternFactory(factory)
    template: str = "if ({}) ;"

    cond: str = ast.unparse(expression)
    code_str: str = template.format(cond)
    print(code_str)
    code: ASTNode = pattern_factory.create_statement(code_str)

    placeholder: str = "$x"
    pattern_str: str = template.format(placeholder)
    print(pattern_str)
    pattern: ASTNode = pattern_factory.create_statement(pattern_str)

    result = MatchFinder.match_pattern(src_nodes=code, patterns=[pattern])
    assert isinstance(result, PatternMatch)

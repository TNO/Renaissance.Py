# __init__.py
from ..utils.text_utils import TextUtils
from .ast_factory import ASTFactory
from .ast_finder import ASTFinder
from .ast_node import ASTNode, ASTReference, VisitorResult
from .ast_processor import ASTProcessor
from .ast_refactor_actions import ASTRefactorActions
from .ast_rewriter import ASTRewriter
from .ast_shower import ASTShower
from .batch_ast_processor import (
    AST_FACTORY_AND_ATU,
    Action,
    BatchASTProcessor,
    IterableProvider,
)
from .match_finder import MatchFinder, PatternMatch
from .recipe_ast_processor import (
    RecipeASTProcessor,
    after_step,
    final_action,
    recipe_step,
)

# ruff: noqa: I001
# isort: split
# This import must come after the ones above: renaissance.impl.clang (imported via
# cpp_utils) imports back from renaissance.syntax_tree (ASTFinder, ASTNode,
# ASTReference), so those names must already be bound in this module's namespace
# before cpp_utils is loaded, or the circular import fails.
from renaissance.impl.clang.cpp_utils import CPPUtils  # noqa: E402

__all__ = [
    "ASTNode",
    "ASTReference",
    "VisitorResult",
    "ASTFinder",
    "ASTShower",
    "ASTFactory",
    "MatchFinder",
    "PatternMatch",
    "ASTRewriter",
    "CPPUtils",
    "TextUtils",
    "ASTProcessor",
    "BatchASTProcessor",
    "IterableProvider",
    "AST_FACTORY_AND_ATU",
    "Action",
    "ASTRefactorActions",
    "RecipeASTProcessor",
    "after_step",
    "recipe_step",
    "final_action",
]

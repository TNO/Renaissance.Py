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

# isort: split
# This import must come after the ones above: renaissance.integrations.clang (imported via
# cpp_utils) imports back from renaissance.syntax_tree (ASTFinder, ASTNode,
# ASTReference), so those names must already be bound in this module's namespace
# before cpp_utils is loaded, or the circular import fails.
from renaissance.integrations.clang.cpp_utils import CPPUtils

__all__ = [
    "AST_FACTORY_AND_ATU",
    "ASTFactory",
    "ASTFinder",
    "ASTNode",
    "ASTProcessor",
    "ASTRefactorActions",
    "ASTReference",
    "ASTRewriter",
    "ASTShower",
    "Action",
    "BatchASTProcessor",
    "CPPUtils",
    "IterableProvider",
    "MatchFinder",
    "PatternMatch",
    "RecipeASTProcessor",
    "TextUtils",
    "VisitorResult",
    "after_step",
    "final_action",
    "recipe_step",
]

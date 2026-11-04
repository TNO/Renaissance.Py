# Copyright (C) 2024-2026 TNO
#
# Licensed under the terms specified in the LICENSE file in the root directory
# of this repository, also available at:
# https://github.com/TNO/Renaissance.Py/blob/main/LICENSE

"""AI: Language-agnostic AST abstraction layer (finder, rewriter, processor) used by all parser integrations."""

from renaissance.syntax_tree.ast_factory import ASTFactory
from renaissance.syntax_tree.ast_finder import ASTFinder
from renaissance.syntax_tree.ast_node import ASTNode, ASTReference, VisitorResult
from renaissance.syntax_tree.ast_processor import ASTProcessor
from renaissance.syntax_tree.ast_refactor_actions import ASTRefactorActions
from renaissance.syntax_tree.ast_rewriter import ASTRewriter
from renaissance.syntax_tree.ast_shower import ASTShower
from renaissance.syntax_tree.batch_ast_processor import AST_FACTORY_AND_ATU, Action, BatchASTProcessor, IterableProvider
from renaissance.syntax_tree.match_finder import MatchFinder, PatternMatch
from renaissance.syntax_tree.recipe_ast_processor import RecipeASTProcessor, after_step, final_action, recipe_step
from renaissance.utils.text_utils import TextUtils

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

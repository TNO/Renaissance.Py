# Copyright (C) 2024-2026 TNO
#
# Licensed under the terms specified in the LICENSE file in the root directory
# of this repository, also available at:
# https://github.com/TNO/Renaissance.Py/blob/main/LICENSE

"""AI: Clang/libclang-based parser integration for C and C++ source code."""

from renaissance.integrations.clang.c_pattern_factory import CPatternFactory, CPPPatternFactory
from renaissance.integrations.clang.clang_ast_node import ClangASTNode
from renaissance.integrations.clang.clang_compilation_database import CompilationDatabase

__all__ = [
    "CPPPatternFactory",
    "CPatternFactory",
    "ClangASTNode",
    "CompilationDatabase",
]

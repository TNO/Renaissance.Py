"""AI: Clang/libclang-based parser integration for C and C++ source code."""

from .c_pattern_factory import CPatternFactory, CPPPatternFactory
from .clang_ast_node import ClangASTNode
from .clang_compilation_database import CompilationDatabase

__all__ = [
    "CPPPatternFactory",
    "CPatternFactory",
    "ClangASTNode",
    "CompilationDatabase",
]

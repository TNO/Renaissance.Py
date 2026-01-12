from common import Stream
from .python_ast_node import PythonASTNode
from .python_codebase import PythonCodebase
from .python_pattern_factory import PythonPatternFactory

__all__ = [
    'PythonASTNode',
    'PythonCodebase',
    'PythonPatternFactory'
]

def match_pattern( stmts, pattern):
    found = []
    for stmt in stmts:
        if stmt.eq(pattern):
            found.append(pattern)
    return found

def find_all( atu, pattern):
    return Stream(match_pattern( atu.get_children(), pattern))


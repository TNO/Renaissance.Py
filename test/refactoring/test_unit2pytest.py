import pytest
from black import Path
from hamcrest import assert_that, contains_string

from renaissance.impl.python import PythonASTNode, PythonPatternFactory
from renaissance.syntax_tree import ASTRewriter, ASTFactory

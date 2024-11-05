from pathlib import Path
from unittest import TestCase
from impl.gcc.gcc_ast_node import GccAstNode

class TestGimpleModel(TestCase):

    def test_test_cpp(self):
        #read test.cpp from ../../../../c/src/test.cpp
        file = Path(__file__).parent.parent.parent.parent / 'c/src/test.cpp'
        GccAstNode.load(file)

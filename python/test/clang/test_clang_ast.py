from pathlib import Path
from impl.clang import ClangASTNode
import logging
import time

from unittest import TestCase

from syntax_tree import ASTNode

from test.clang.test_model_loader import TestModelLoader

logger = logging.getLogger(__name__)

class TestClangAst(TestCase):
    logger.info("Loading AST")
    model = TestModelLoader.model
    logger.info("Loaded AST")


    def test_rawBinding(self):
        start = time.time()
        rootNode = TestModelLoader.model
        duration2 = time.time() - start
        children = rootNode.get_children()
        for c in children:
            self.assertTrue(c.get_parent() is rootNode)
        count = [0]

        def visitFunction(astNode: ASTNode) -> None:
                count[0] += 1

        rootNode.process(visitFunction)
        logger.info(f"Visited {count[0]} nodes")
        self.assertGreater(count[0], 0, "Visitor should visit at least one node")
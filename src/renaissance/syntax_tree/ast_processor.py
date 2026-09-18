"""AI: Processor that coordinates parsing, pattern matching, and rewriting of a single AST."""

from collections.abc import Callable, Iterator, Sequence
from pathlib import Path

import renaissance.syntax_tree.match_finder
from renaissance.syntax_tree import ASTNode
from renaissance.syntax_tree.ast_factory import ASTFactory
from renaissance.syntax_tree.ast_finder import ASTFinder, find_semantic_kind
from renaissance.syntax_tree.ast_rewriter import ASTRewriter
from renaissance.syntax_tree.match_finder import PatternMatch
from renaissance.syntax_tree.node_protocol import NodeProtocol
from renaissance.syntax_tree.semantic_kind import SemanticKind


class ASTProcessor:
    """AI: Processor that coordinates parsing, pattern matching, and rewriting of a single AST."""

    def __init__(
        self,
        root: ASTNode,
        ast_factory: ASTFactory,
        in_memory: bool = False,
    ) -> None:
        """AI: Prepare a processor that runs refactoring/analysis steps over the given AST."""
        self.__root_node = root
        self.__rewriter = ASTRewriter(root)
        self.__ast_factory = ast_factory
        self.in_memory = in_memory
        self.repeat_step = 0

    @property
    def factory(self) -> ASTFactory:
        """AI: Return the AST factory used to create nodes for this processor."""
        return self.__ast_factory

    @property
    def node(self) -> ASTNode:
        """AI: Return the root AST node this processor operates on."""
        return self.__root_node

    @property
    def filename(self) -> str:
        """AI: Return the filename of the AST this processor operates on."""
        return self.__rewriter.get_filename()

    @property
    def root(self) -> ASTNode:
        """AI: Return the root AST node this processor operates on."""
        return self.__root_node

    def replace(
        self,
        new_content: str,
        target: ASTNode | Sequence[ASTNode] | PatternMatch | Sequence[PatternMatch],
        include_whitespace: bool = True,
        include_comments: bool = True,
    ) -> None:
        """AI: Queue a rewrite replacing target's source text with new_content."""
        self.__rewriter.replace(new_content, target, include_whitespace, include_comments)

    def remove(
        self,
        target: ASTNode | Sequence[ASTNode] | PatternMatch | Sequence[PatternMatch],
        include_whitespace: bool = True,
        include_comments: bool = True,
    ) -> None:
        """AI: Queue a rewrite removing target's source text."""
        self.__rewriter.remove(target, include_whitespace, include_comments)

    def insert_before(
        self,
        new_content: str,
        target: ASTNode | Sequence[ASTNode] | PatternMatch | Sequence[PatternMatch],
        include_whitespace: bool = True,
        include_comments: bool = True,
    ) -> None:
        """AI: Queue a rewrite inserting new_content immediately before target's source text."""
        self.__rewriter.insert_before(new_content, target, include_whitespace, include_comments)

    def insert_after(
        self,
        new_content: str,
        target: ASTNode | Sequence[ASTNode] | PatternMatch | Sequence[PatternMatch],
        include_whitespace: bool = True,
        include_comments: bool = True,
    ) -> None:
        """AI: Queue a rewrite inserting new_content immediately after target's source text."""
        self.__rewriter.insert_after(new_content, target, include_whitespace, include_comments)

    def find_all(self, function: Callable[[ASTNode], Iterator[ASTNode] | bool]) -> Sequence[ASTNode]:
        """AI: Return all descendant nodes of the root for which function returns a truthy value or child iterator."""
        return ASTFinder.find_all(self.__root_node, function)

    def find_semantic_kind(self, kind: SemanticKind) -> Sequence[NodeProtocol]:
        """AI: Return all descendant nodes of the root matching the given semantic kind."""
        return find_semantic_kind(self.__root_node, kind)

    def find_match(self, *patterns_list, recursive: bool = True) -> Sequence[PatternMatch]:
        """AI: Return matches of patterns_list against the root's children."""
        return renaissance.syntax_tree.match_finder.find_all(
            self.__root_node.children,
            *patterns_list,
            recursive=recursive,
        )

    def has_changed(self) -> bool:
        """AI: Return whether any rewrites have been queued."""
        return self.__rewriter.has_changed()

    def apply_to_string(self) -> str:
        """AI: Return the rewritten source as a string, applying all queued rewrites."""
        return self.__rewriter.apply_to_string()

    def commit(self) -> ASTProcessor:
        """Commit the current changes to the AST (Abstract Syntax Tree) and return a new ASTProcessor instance.

        This method applies the current changes to the source code and creates a new ASTProcessor instance
        with the updated AST. If the changes are in-memory, it directly creates the new AST from the updated
        code string. Otherwise, it writes the changes to the file, reloads the file, and then creates the new AST.

        Returns:
            ASTProcessor: A new instance of ASTProcessor with the updated AST.

        Raises:
            IOError: If there is an error writing to the file.

        """
        if not self.__rewriter.has_changed():
            return self
        self.__root_node, self.__rewriter = self._commit(self.__rewriter, self.__ast_factory, self.in_memory)
        return ASTProcessor(self.__root_node, self.__ast_factory, self.in_memory)

    @staticmethod
    def _commit(rewriter: ASTRewriter, factory: ASTFactory, in_memory: bool = False):
        rewriter.apply_to_string()
        if in_memory:
            atu = factory.create_from_text(rewriter.apply_to_string(), rewriter.get_filename())
            return atu, ASTRewriter(atu)
        # save file first then reload it
        with Path(rewriter.get_filename()).open("wb") as f:
            f.write(rewriter.apply())
        atu = factory.create(Path(rewriter.get_filename()))
        return atu, ASTRewriter(atu)


# main
if __name__ == "__main__":

    def test[T](_: str, factory: type[T]) -> T:
        """AI: Smoke-test helper verifying a factory callable returns an instance of its own type."""
        result = factory()
        assert isinstance(result, factory)
        return result

    test("key", str)

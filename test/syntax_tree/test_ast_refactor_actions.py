"""Tests for the ASTRefactorActions helper."""

from hamcrest import assert_that, is_

from renaissance.syntax_tree import ASTRefactorActions
from renaissance.syntax_tree.semantic_kind import SemanticKind


class TestASTRefactorActions:
    """AI: Tests for the ASTRefactorActions helper."""

    def test_it_can_be_created(self, mocker):
        """AI: Verify ASTRefactorActions can be constructed from a processor and factory."""
        proc = mocker.Mock()
        factory = mocker.Mock()
        refactor_actions = ASTRefactorActions(proc, factory)
        assert_that(refactor_actions, not is_(None))

    def test_replace_expr(self, mocker):
        """AI: Verify replace_expr delegates to the processor's find_all method."""
        proc = mocker.Mock()
        proc.find_all.return_value = []
        factory = mocker.Mock()
        refactor_actions = ASTRefactorActions(proc, factory)
        refactor_actions.replace_expr("name", "my_awsome_name", SemanticKind.NAME)
        assert_that(proc.find_all.called)

    def test_replace_name(self, mocker):
        """AI: Verify replace_name finds a matching name node and calls the processor's replace method."""
        node = mocker.Mock()
        node.offset = 1
        node.semantic_kind = SemanticKind.NAME
        node.name = "name"
        proc = mocker.Mock()
        factory = mocker.Mock()
        proc.find_all.return_value = [node]
        refactor_actions = ASTRefactorActions(proc, factory)

        refactor_actions.replace_name("name", "my_awsome_name", SemanticKind.NAME, SemanticKind.CALL)

        assert_that(proc.replace.called)

    def test_replace_text(self, mocker):
        """AI: Verify replace_text finds matching literal nodes and calls the processor's replace method."""
        node = mocker.Mock()
        node.semantic_kind = SemanticKind.LITERAL
        node.text = "text"
        node.name = "text"
        proc = mocker.Mock()
        factory = mocker.Mock()
        refactor_actions = ASTRefactorActions(proc, factory)
        proc.find_all.return_value = [node, node]

        refactor_actions.replace_text("text", "my_awsome_text", SemanticKind.LITERAL, SemanticKind.CALL)

        assert_that(proc.replace.called)

    def test_replace_declaration(self, mocker):
        """AI: Verify replace_declaration finds the declaration and calls the processor's replace method."""
        node = mocker.Mock()
        proc = mocker.Mock()
        factory = mocker.Mock()
        refactor_actions = ASTRefactorActions(proc, factory)
        refactor_actions.find_declaration = lambda decl: [node]

        refactor_actions.replace_declaration("decl", "my_awsome_decl")

        assert_that(proc.replace.called)

    def test_replace_patterns(self, mocker):
        """AI: Verify _replace_patterns matches the pattern and calls the processor's replace method."""
        node = mocker.Mock()
        proc = mocker.Mock()
        factory = mocker.Mock()
        is_match_mock = mocker.patch("renaissance.syntax_tree.match_finder.find_in_list", return_value=True)
        refactor_actions = ASTRefactorActions(proc, factory)

        refactor_actions._replace_patterns(node, "my_awsome_text", [[node]], "Call")

        assert_that(proc.replace.called)
        assert_that(is_match_mock.called)

    def test_find_declaration(self, mocker):
        """AI: Verify find_declaration delegates to the processor's find_match method."""
        proc = mocker.Mock()
        factory = mocker.Mock()
        refactor_actions = ASTRefactorActions(proc, factory)
        refactor_actions.find_declaration("decl_pattern")
        assert_that(proc.find_match.called)

    def test_collect(self, mocker):
        """AI: Verify collect delegates to the processor's find_match method."""
        proc = mocker.Mock()
        proc.find_match.return_value = []
        factory = mocker.Mock()
        refactor_actions = ASTRefactorActions(proc, factory)
        refactor_actions.collect("pattern", "pattern_kind")
        assert_that(proc.find_match.called, is_(1))

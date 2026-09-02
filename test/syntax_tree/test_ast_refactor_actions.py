from hamcrest import assert_that, is_

from renaissance.impl.types import Name
from renaissance.syntax_tree import ASTRefactorActions


class TestASTRefactorActions:
    def test_it_can_be_created(self, mocker):
        proc = mocker.Mock()
        factory = mocker.Mock()
        refactor_actions = ASTRefactorActions(proc, factory)
        assert_that(refactor_actions, not is_(None))

    def test_replace_expr(self, mocker):
        proc = mocker.Mock()
        proc.find_all.return_value = []
        factory = mocker.Mock()
        refactor_actions = ASTRefactorActions(proc, factory)
        refactor_actions.replace_expr("name", "my_awsome_name", Name)
        assert_that(proc.find_all.called)

    def test_replace_name(self, mocker):
        node = mocker.Mock()
        node.offset = 1
        proc = mocker.Mock()
        factory = mocker.Mock()
        proc.find_all.return_value = [node]
        refactor_actions = ASTRefactorActions(proc, factory)

        refactor_actions.replace_name("name", "my_awsome_name", "Name", "Call")

        assert_that(proc.replace.called)

    def test_replace_text(self, mocker):
        node = mocker.Mock()
        proc = mocker.Mock()
        factory = mocker.Mock()
        refactor_actions = ASTRefactorActions(proc, factory)
        proc.find_all.return_value = [node, node]

        refactor_actions.replace_text("text", "my_awsome_text", "StringLiteral", "Call")

        assert_that(proc.replace.called)

    def test_replace_declaration(self, mocker):
        node = mocker.Mock()
        proc = mocker.Mock()
        factory = mocker.Mock()
        refactor_actions = ASTRefactorActions(proc, factory)
        refactor_actions.find_declaration = lambda decl: [node]

        refactor_actions.replace_declaration("decl", "my_awsome_decl")

        assert_that(proc.replace.called)

    def test_replace_patterns(self, mocker):
        node = mocker.Mock()
        proc = mocker.Mock()
        factory = mocker.Mock()
        is_match_mock = mocker.patch("renaissance.syntax_tree.match_finder.find_in_list", return_value=True)
        refactor_actions = ASTRefactorActions(proc, factory)

        refactor_actions._replace_patterns(node, "my_awsome_text", [[node]], "Call")

        assert_that(proc.replace.called)
        assert_that(is_match_mock.called)

    def test_find_declaration(self, mocker):
        proc = mocker.Mock()
        factory = mocker.Mock()
        refactor_actions = ASTRefactorActions(proc, factory)
        refactor_actions.find_declaration("decl_pattern")
        assert_that(proc.find_match.called)

    def test_collect(self, mocker):
        proc = mocker.Mock()
        proc.find_match.return_value = []
        factory = mocker.Mock()
        refactor_actions = ASTRefactorActions(proc, factory)
        refactor_actions.collect("pattern", "pattern_kind")
        assert_that(proc.find_match.called, is_(1))

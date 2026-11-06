# Copyright (C) 2024-2026 TNO
#
# Licensed under the terms specified in the LICENSE file in the root directory
# of this repository, also available at:
# https://github.com/TNO/Renaissance.Py/blob/main/LICENSE

"""Tests for the BatchASTProcessor."""

from collections.abc import Callable, Iterator

import pytest
from hamcrest import assert_that, equal_to, has_length, is_
from pytest_mock import MockerFixture

import renaissance.syntax_tree.batch_ast_processor as bap
from renaissance.core.model import SemanticKind
from renaissance.integrations.clang import ClangASTNode
from renaissance.recipes import CleanupRefactoring
from renaissance.syntax_tree.ast_factory import ASTFactory
from renaissance.syntax_tree.ast_processor import ASTProcessor
from renaissance.syntax_tree.batch_ast_processor import BatchASTProcessor


class TestBatchASTProcessor:
    """AI: Tests for the BatchASTProcessor."""

    def test_it(self) -> None:
        """AI: Verify BatchASTProcessor stores its in_memory flag and max_processes count."""
        it = BatchASTProcessor(True, 8)
        assert_that(it.in_memory)
        assert_that(it.max_processes, is_(8))

    def test_once(self, mocker: MockerFixture) -> None:
        """AI: Verify once() invokes the processor's internal __process method."""
        processor = BatchASTProcessor(True, 8)
        iterable_items = [mocker.Mock()]
        actions_mock = mocker.Mock()
        process_method_spy = mocker.patch.object(processor, "_BatchASTProcessor__process")
        processor.once(lambda: iterable_items, actions_mock)
        assert_that(process_method_spy.called)

    def test_repeat(self, mocker: MockerFixture) -> None:
        """AI: Verify repeat() invokes the processor's internal __process method."""
        processor = BatchASTProcessor(True, 8)
        iterable_items = [mocker.Mock()]
        actions_mock = mocker.Mock()
        process_method_spy = mocker.patch.object(processor, "_BatchASTProcessor__process")

        processor.repeat(lambda: iterable_items, actions_mock)

        assert_that(process_method_spy.called)

    def test__process(self, mocker: MockerFixture) -> None:
        """AI: Verify the internal __process method invokes process_atu for each item."""
        processor = BatchASTProcessor(True, 8)
        dummy_atu_item = (mocker.Mock(), mocker.Mock())
        atu_items = [dummy_atu_item]
        actions_list = [mocker.Mock()]
        process_atu_spy = mocker.patch("renaissance.syntax_tree.batch_ast_processor.process_atu", return_value=[])
        processor._BatchASTProcessor__process(atu_items, actions_list)
        assert_that(process_atu_spy.called)

    def test_replace_if_in_memory(self, mocker: MockerFixture) -> None:
        """AI: Verify _replace_if_in_memory swaps in in-memory file content when registered, and passes through otherwise."""
        processor = BatchASTProcessor(True, 8)
        fake_factory = mocker.Mock()
        fake_node = mocker.Mock()
        fake_node.filename = "a.c"
        atu_item = (fake_factory, fake_node)

        result_no_in_memory = processor._replace_if_in_memory(atu_item)
        assert_that(result_no_in_memory, is_(atu_item))

        in_memory_content = "int x = 0;"
        processor.in_memory_files[fake_node.filename] = in_memory_content
        sentinel_atu = mocker.Mock()
        fake_factory.create_from_text = mocker.Mock(return_value=sentinel_atu)

        result_with_in_memory = processor._replace_if_in_memory(atu_item)
        assert_that(result_with_in_memory, has_length(2))
        assert_that(result_with_in_memory[0], is_(fake_factory))
        assert_that(result_with_in_memory[1], is_(sentinel_atu))
        fake_factory.create_from_text.assert_called_with(in_memory_content, fake_node.filename)

    def test_process_atu(self, mocker: MockerFixture) -> None:
        """AI: Verify process_atu runs the given action on the ASTProcessor and returns its results."""
        processor = BatchASTProcessor(True, 8)

        dummy_factory = mocker.Mock()
        dummy_node = mocker.Mock()
        atu = (dummy_factory, dummy_node)

        action_result = mocker.Mock()

        def action(ast_proc):
            return action_result

        mock_ast_proc = mocker.Mock()
        mock_ast_proc.has_changed.return_value = False
        mock_ast_proc.commit.return_value = mock_ast_proc
        mock_ast_proc.filename.return_value = "file"
        mock_ast_proc.apply_to_string.return_value = "content"
        mocker.patch(
            "renaissance.syntax_tree.batch_ast_processor.ASTProcessor",
            return_value=mock_ast_proc,
        )

        results = bap.process_atu(atu, processor, [action], in_memory=False, max_repeat=1)

        assert_that(results, has_length(1))
        assert_that(results[0], is_(action_result))


SOURCE = "void g(int a);\nvoid f() {\n    int unused = 1;\n    int used = 2;\n    g(used);\n}\n"


def clang_files(files: dict[str, str]) -> bap.IterableProvider:
    """Return a provider that parses each (filename, source) pair with Clang."""

    def provider() -> Iterator[bap.AST_FACTORY_AND_ATU]:
        factory = ASTFactory(ClangASTNode)
        for filename, source in files.items():
            yield factory, factory.create_from_text(source, filename)

    return provider


def comment_out_calls(ast_processor: ASTProcessor) -> None:
    """Prefix every call with a line comment marker."""
    for call in ast_processor.find_semantic_kind(SemanticKind.CALL):
        ast_processor.insert_before("// ", call, include_whitespace=False, include_comments=False)


class TestBatchASTProcessorOnClangCode:
    """BatchASTProcessor rewrites real C code in memory."""

    @pytest.mark.parametrize(
        ("method", "expected"),
        [
            pytest.param(
                BatchASTProcessor.once,
                "void g(int a);\nvoid f() {\n    int used = 2;\n    // g(used);\n}\n",
                id="once",
            ),
            pytest.param(
                BatchASTProcessor.repeat,
                "void g(int a);\nvoid f() {\n    // g(used);\n}\n",
                id="repeat-until-nothing-changes",
            ),
        ],
    )
    def test_rewrites_until_nothing_changes(self, method: Callable[..., None], expected: str) -> None:
        """Once applies the actions in one pass; repeat also removes the variable that the first pass left unused."""
        processor = BatchASTProcessor(in_memory=True)

        method(processor, clang_files({"a.c": SOURCE}), [CleanupRefactoring.remove_unused_variables, comment_out_calls])

        assert_that(processor.in_memory_files, equal_to({"a.c": expected}))

    def test_file_filter_limits_the_rewritten_files(self) -> None:
        """Only files whose name matches the filter are processed."""
        processor = BatchASTProcessor(in_memory=True)

        processor.once(clang_files({"a.c": SOURCE, "b.c": SOURCE}), CleanupRefactoring.remove_unused_variables, r"a\.c")

        assert_that(list(processor.in_memory_files), equal_to(["a.c"]))

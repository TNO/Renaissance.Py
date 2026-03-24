from hamcrest import assert_that, is_, has_length

from renaissance.syntax_tree import BatchASTProcessor


class TestBatchASTProcessor:

    def test_it(self):
        it = BatchASTProcessor(True, 8)
        assert_that(it.in_memory)
        assert_that(it.max_processes, is_(8))

    def test_once(self, mocker):
        processor = BatchASTProcessor(True, 8)
        iterable_items = [mocker.Mock()]
        actions_mock = mocker.Mock()
        process_method_spy = mocker.patch.object(processor, "_BatchASTProcessor__process")
        processor.once(lambda: iterable_items, actions_mock)
        assert_that(process_method_spy.called)

    def test_repeat(self, mocker):
        processor = BatchASTProcessor(True, 8)
        iterable_items = [mocker.Mock()]
        actions_mock = mocker.Mock()
        process_method_spy = mocker.patch.object(processor, "_BatchASTProcessor__process")

        processor.repeat(lambda: iterable_items, actions_mock)

        assert_that(process_method_spy.called)

    def test__process(self, mocker):
        processor = BatchASTProcessor(True, 8)
        dummy_atu_item = (mocker.Mock(), mocker.Mock())
        atu_items = [dummy_atu_item]
        actions_list = [mocker.Mock()]
        process_atu_spy = mocker.patch("renaissance.syntax_tree.batch_ast_processor.process_atu", return_value=[])
        processor._BatchASTProcessor__process(atu_items, actions_list)
        assert_that(process_atu_spy.called)

    def test_replace_if_in_memory(self, mocker):
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

    def test_process_atu(self, mocker):
        from renaissance.syntax_tree import batch_ast_processor as bap

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

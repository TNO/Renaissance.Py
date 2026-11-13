# Copyright (C) 2024-2026 TNO
#
# Licensed under the terms specified in the LICENSE file in the root directory
# of this repository, also available at:
# https://github.com/TNO/Renaissance.Py/blob/main/LICENSE

"""Tests for the RecipeASTProcessor and its decorator helpers."""

from collections.abc import Callable, Iterator

import pytest
from hamcrest import assert_that, equal_to, has_length, is_
from pytest_mock import MockerFixture

from renaissance.core.model import ASTFactory, SemanticKind
from renaissance.integrations.clang import ClangASTNode
from renaissance.syntax_tree.ast_processor import ASTProcessor
from renaissance.syntax_tree.batch_ast_processor import AST_FACTORY_AND_ATU, IterableProvider
from renaissance.syntax_tree.recipe_ast_processor import (
    BatchASTProcessor,
    RecipeASTProcessor,
    after_step,
    annotate_decorator,
    final_action,
    get_methods_with_decorator,
    recipe_step,
)


class TestRecipeASTProcessor:
    """AI: Tests for the RecipeASTProcessor and its decorator helpers."""

    def test_receipe_proc(self) -> None:
        """AI: Verify RecipeASTProcessor can be constructed from a recipe, iterable provider, and path."""
        it = RecipeASTProcessor(lambda n: n, lambda: (), "")
        assert_that(it, is_(RecipeASTProcessor))

    def test_run(self, mocker: MockerFixture) -> None:
        """AI: Verify run() invokes each recipe_step-decorated method via BatchASTProcessor.repeat."""

        # define a simple recipe class with one recipe_step
        class SimpleRecipe:
            def __init__(self) -> None:
                self.ran = []

            @recipe_step(order=0)
            def do_step(self, _):
                def work() -> None:
                    self.ran.append("done")

                return work

        # patch BatchASTProcessor.repeat to immediately invoke actions with a dummy ASTProcessor
        def fake_repeat(_, _1, actions, _2) -> None:
            dummy = mocker.Mock()
            dummy.repeat_step = 0
            for action in actions:
                action(dummy)

        recipe = SimpleRecipe()
        iterable_provider = list

        mocker.patch.object(BatchASTProcessor, "repeat", new=fake_repeat)

        processor = RecipeASTProcessor(recipe, iterable_provider, "")
        processor.run()

        assert_that(recipe.ran, is_(["done"]))

    def test_annotate_decorator(self) -> None:
        """AI: Verify annotate_decorator preserves the wrapped decorator's name and attaches a recipe_action name."""

        def foreign(f):
            return f

        decorator = annotate_decorator(foreign, "test_decorator")
        # the returned decorator keeps the foreign decorator's __name__
        assert_that(decorator.__name__, is_(foreign.__name__))

        # when applied to a function, the decorator attaches the recipe_action name
        @decorator
        def sample() -> int:
            return 1

        assert_that(sample.recipe_action, is_("test_decorator"))

    def test_get_methods_with_decorator(self) -> None:
        """AI: Verify get_methods_with_decorator finds methods decorated with @recipe_step."""

        class Sample:
            @recipe_step()
            def step1(self) -> None:
                pass

        methods = list(get_methods_with_decorator(Sample, recipe_step))
        assert_that(methods, has_length(1))
        assert_that(methods[0].__name__, is_("step1"))

    def test_final_action(self) -> None:
        """AI: Verify get_methods_with_decorator finds methods decorated with @final_action."""

        class Sample:
            @final_action()
            def final(self) -> None:
                pass

        methods = list(get_methods_with_decorator(Sample, final_action))
        assert_that(methods, has_length(1))
        assert_that(methods[0].__name__, is_("final"))


def clang_files(files: dict[str, str]) -> IterableProvider:
    """Return a provider that parses each (filename, source) pair with Clang."""

    def provider() -> Iterator[AST_FACTORY_AND_ATU]:
        factory = ASTFactory(ClangASTNode)
        for filename, source in files.items():
            yield factory, factory.create_from_text(source, filename)

    return provider


class CallCounter:
    """Recipe that counts the calls in each file, then records its after_step and final_action."""

    def __init__(self) -> None:
        """Start with an empty log."""
        self.log: list[tuple[str, ...]] = []

    @recipe_step(order=0)
    def count_calls(self, ast_processor: ASTProcessor) -> Callable[[], None]:
        """Queue the number of calls in this file for the log."""
        count = len(list(ast_processor.find_semantic_kind(SemanticKind.CALL)))
        return lambda: self.log.append(("count_calls", ast_processor.filename, str(count)))

    @after_step("count_calls")
    def after_counting(self) -> None:
        """Record that count_calls has run."""
        self.log.append(("after_counting",))

    @final_action()
    def finish(self) -> None:
        """Record the end of the recipe."""
        self.log.append(("finish",))


class TwoSteps:
    """Recipe with two steps that only record their own name."""

    def __init__(self) -> None:
        """Start with an empty log."""
        self.log: list[str] = []

    @recipe_step(order=0)
    def first(self, _: ASTProcessor) -> Callable[[], None]:
        """Queue the name of the first step."""
        return lambda: self.log.append("first")

    @recipe_step(order=1)
    def second(self, _: ASTProcessor) -> Callable[[], None]:
        """Queue the name of the second step."""
        return lambda: self.log.append("second")

    @final_action()
    def finish(self) -> None:
        """Record the end of the recipe."""
        self.log.append("finish")


class TestRecipeASTProcessorOnClangCode:
    """RecipeASTProcessor runs a recipe over real C files."""

    def test_runs_step_then_after_step_then_final_action(self) -> None:
        """The step runs for every file, then the after_step, then the final_action."""
        recipe = CallCounter()
        files = {"a.c": "void g();\nvoid f() {\n    g();\n    g();\n}\n", "b.c": "void g();\nvoid h() {\n    g();\n}\n"}

        RecipeASTProcessor(recipe, clang_files(files), r".*", in_memory=True).run()

        assert_that(
            recipe.log,
            equal_to([("count_calls", "a.c", "2"), ("count_calls", "b.c", "1"), ("after_counting",), ("finish",)]),
        )

    @pytest.mark.xfail(
        reason="RecipeASTProcessor.run builds its step actions in a loop whose closures read the loop variable late, "
        "so every action calls the last recipe_step method.",
        strict=True,
    )
    def test_runs_steps_in_order(self) -> None:
        """Steps run in the order of their order argument, then the final_action."""
        recipe = TwoSteps()

        RecipeASTProcessor(recipe, clang_files({"a.c": "void f() {}\n"}), r".*", in_memory=True).run()

        assert_that(recipe.log, equal_to(["first", "second", "finish"]))

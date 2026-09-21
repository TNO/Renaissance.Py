"""AI: Decorator support for annotating recipe actions on AST processors."""

import functools
from collections.abc import Callable, Sequence
from typing import Any, TypeVar

from .ast_processor import ASTProcessor
from .batch_ast_processor import BatchASTProcessor, IterableProvider

TRecipe = TypeVar("TRecipe")
TFunc = Callable[..., Any]


def annotate_decorator(foreign_decorator: TFunc, name: str):
    """AI: Wrap foreign_decorator so the decorated function also records its own decorator and recipe-action name."""

    def new_decorator(func: TFunc) -> TFunc:
        r = foreign_decorator(func)  # apply foreignDecorator, like call to foreignDecorator(method) would have done
        r.decorator = new_decorator  # keep track of decorator
        r.recipe_action = name
        return r

    new_decorator.__name__ = foreign_decorator.__name__
    new_decorator.__doc__ = foreign_decorator.__doc__
    return new_decorator


def get_methods_with_decorator(cls: Any, decorator: TFunc):
    """AI: Yield all methods of cls that were annotated with the given recipe-action decorator."""
    for maybe_decorated in cls.__dict__.values():
        if hasattr(maybe_decorated, "recipe_action") and maybe_decorated.recipe_action == decorator.__name__:
            yield maybe_decorated


# Decorators


def final_action() -> TFunc:
    """AI: Decorator marking a recipe method as a final action, run once after all steps complete."""

    def final_action_decorator(func: TFunc) -> TFunc:
        @functools.wraps(func)
        def final_action_wrapper(recipe: TFunc):
            func(recipe)

        return final_action_wrapper

    return annotate_decorator(final_action_decorator, final_action.__name__)


def recipe_step(order: int = 0, repeat: bool = False) -> TFunc:
    """AI: Decorator marking a recipe method as a numbered step, optionally repeatable, in the recipe's workflow."""

    def recipe_step_decorator(func: TFunc) -> TFunc:
        @functools.wraps(func)
        def recipe_step_wrapper(step: int, recipe: TFunc, ast_processor: ASTProcessor):
            if step == order and (repeat or ast_processor.repeat_step == 0):
                result = func(recipe, ast_processor)

                def callable_result():
                    if result:
                        result()
                    return func.__name__

                return callable_result()
            return None

        return recipe_step_wrapper

    return annotate_decorator(recipe_step_decorator, recipe_step.__name__)


def after_step(step: str) -> TFunc:
    """AI: Decorator marking a recipe method to run only after the named step has already executed."""

    def after_step_decorator(func: TFunc) -> TFunc:
        @functools.wraps(func)
        def after_step_wrapper(preceding_methods: Sequence[str], recipe: TFunc):
            if step in preceding_methods:
                func(recipe)

        return after_step_wrapper

    return annotate_decorator(after_step_decorator, after_step.__name__)


class RecipeASTProcessor[TRecipe]:
    """AI: Processor that runs a recipe's steps across a batch of files, optionally in parallel."""

    def __init__(
        self,
        recipe: TRecipe,
        iterable_provider: IterableProvider,
        file_filter: str,
        in_memory: bool = False,
        max_processes: int = 4,
    ):
        """AI: Prepare a processor that runs a recipe's steps across a batch of files, optionally in parallel."""
        self.__recipe: TRecipe = recipe
        self.__batch_processor = BatchASTProcessor(in_memory=in_memory, max_processes=max_processes)
        self.__iterableProvider = iterable_provider
        self.__file_filter = file_filter

    def run(self):
        """AI: Run each of the recipe's decorated steps across the batch of files and return the collected results."""
        actions: list[TFunc] = []
        results: list[Any] = []
        for idx, recipe_step_method in enumerate(get_methods_with_decorator(type(self.__recipe), recipe_step)):
            results.append(None)

            def recipe_action(ast_processor: ASTProcessor):
                result = recipe_step_method(step, self.__recipe, ast_processor)
                if result:
                    results[idx] = result

            actions.append(recipe_action)

        after_step_actions: list[TFunc] = []
        for after_step_method in get_methods_with_decorator(self.__recipe.__class__, after_step):

            def after_step_action():
                after_step_method(results, self.__recipe)

            after_step_actions.append(after_step_action)

        step = 0
        while len(actions) > 0:
            for idx in range(len(results)):
                results[idx] = None
            self.__batch_processor.repeat(self.__iterableProvider, actions, self.__file_filter)
            if all(result is None for result in results):
                break
            for after_step_action in after_step_actions:
                after_step_action()
            step += 1

        for method in get_methods_with_decorator(self.__recipe.__class__, final_action):
            method(self.__recipe)

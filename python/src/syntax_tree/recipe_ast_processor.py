
import functools
from typing import TypeVar

from .ast_processor import ASTProcessor
from .batch_ast_processor import BatchASTProcessor, IterableProvider

T = TypeVar('T')

def annotate_decorator(foreignDecorator, name:str):
    def newDecorator(func):
        R = foreignDecorator(func) # apply foreignDecorator, like call to foreignDecorator(method) would have done
        R.decorator = newDecorator # keep track of decorator
        R.recipe_action = name
        return R

    newDecorator.__name__ = foreignDecorator.__name__
    newDecorator.__doc__ = foreignDecorator.__doc__
    return newDecorator

def get_methods_with_decorator(cls, decorator):
    for maybeDecorated in cls.__dict__.values():
        if hasattr(maybeDecorated, 'recipe_action'):
            if maybeDecorated.recipe_action == decorator.__name__:
                yield maybeDecorated

# Decorators

def final_action():
    def final_action_decorator(func):
        @functools.wraps(func)
        def final_action_wrapper(recipe, *args, **kwargs):
            func(recipe)
        return final_action_wrapper
    return annotate_decorator(final_action_decorator, final_action.__name__)

def recipe_step(order=0, repeat=False):
    def recipe_step_decorator(func):
        @functools.wraps(func)
        def recipe_step_wrapper(step: int, recipe, ast_processor: ASTProcessor,  *args, **kwargs):
            if step == order:
                if repeat or ast_processor.repeat_step == 0:
                    result = func(recipe, ast_processor)
                    def callable_result():
                        if result: 
                            result()
                        return func.__name__
                    return callable_result()
            return None
        return recipe_step_wrapper
    return annotate_decorator(recipe_step_decorator, recipe_step.__name__)

def after_step(step:str):
    def after_step_decorator(func):
        @functools.wraps(func)
        def after_step_wrapper(preceding_methods, recipe, *args, **kwargs):
            if step in preceding_methods:
                func(recipe)
        return after_step_wrapper
    return annotate_decorator(after_step_decorator, after_step.__name__)


class RecipeASTProcessor():

    def __init__(self, recipe, iterableProvider: IterableProvider, file_filter:str,in_memory: bool = False, max_processes=4):
        self.__recipe = recipe
        self.__batch_processor = BatchASTProcessor(in_memory=in_memory, max_processes=max_processes)
        self.__iterableProvider = iterableProvider
        self.__file_filter = file_filter

    def run(self):
        actions = []
        results = []
        for idx, recipe_step_method in enumerate(get_methods_with_decorator(self.__recipe.__class__, recipe_step)):
            results.append(None)
            def recipe_action(ast_processor):
                result = recipe_step_method(step, self.__recipe, ast_processor)
                if result:
                    results[idx] = result
            actions.append(recipe_action)
        after_step_actions = []
        for after_step_method in get_methods_with_decorator(self.__recipe.__class__, after_step):
            def after_step_action():
                after_step_method(results, self.__recipe)
            after_step_actions.append(after_step_action)


        step = 0
        while len(actions) > 0:
            for idx in range(len(results)):
                results[idx] = None
            self.__batch_processor.repeat(self.__iterableProvider, actions, self.__file_filter)
            if all([result == None for result in results]):
                break
            for after_step_action in after_step_actions:
                after_step_action()
            step += 1

        for method in get_methods_with_decorator(self.__recipe.__class__, final_action):
            method(self.__recipe)


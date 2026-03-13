from hamcrest import assert_that, is_, has_length

from renaissance.syntax_tree.recipe_ast_processor import (
    RecipeASTProcessor,
    recipe_step,
    final_action,
    BatchASTProcessor, annotate_decorator, get_methods_with_decorator,
)


class TestRecipeASTProcessor:
    def test_receipe_proc(self):
        it = RecipeASTProcessor(lambda n:n, lambda : (), '')
        assert_that(it, is_(RecipeASTProcessor))

    def test_run(self, mocker):
        # define a simple recipe class with one recipe_step
        class SimpleRecipe:
            def __init__(self):
                self.ran = []

            @recipe_step(order=0)
            def do_step(self, _):
                def work():
                    self.ran.append('done')

                return work
        # patch BatchASTProcessor.repeat to immediately invoke actions with a dummy ASTProcessor
        def fake_repeat(_, _1, actions, _2):
            dummy = mocker.Mock()
            dummy.repeat_step = 0
            for action in actions:
                action(dummy)

        recipe = SimpleRecipe()
        iterable_provider = lambda: []

        mocker.patch.object(BatchASTProcessor, 'repeat', new=fake_repeat)

        processor = RecipeASTProcessor(recipe, iterable_provider, '')
        processor.run()

        assert_that(recipe.ran, is_(['done']))


def test_annotate_decorator():
    foreign = lambda f: f
    decorator = annotate_decorator(foreign, 'test_decorator')
    # the returned decorator keeps the foreign decorator's __name__
    assert_that(decorator.__name__, is_(foreign.__name__))

    # when applied to a function, the decorator attaches the recipe_action name
    @decorator
    def sample():
        return 1

    assert_that(sample.recipe_action, is_('test_decorator'))


def test_get_methods_with_decorator():
    class Sample:
        @recipe_step()
        def step1(self):
            pass

    methods = get_methods_with_decorator(Sample, recipe_step)
    assert_that(methods, has_length(1))
    assert_that(methods[0].__name__, is_('step1'))


def test_final_action():
    class Sample:
        @final_action()
        def final(self):
            pass

    methods = get_methods_with_decorator(Sample, final_action)
    assert_that(methods, has_length(1))
    assert_that(methods[0].__name__, is_('final'))

import textwrap
from types import SimpleNamespace
from unittest.mock import MagicMock, mock_open, patch

from hamcrest import assert_that, contains_string, has_length, is_

from renaissance.impl.python import PythonASTNode, PythonPatternFactory
from renaissance.refactoring import unit2pytest as mod
from renaissance.refactoring.unit2pytest import Unit2Pytest
from renaissance.syntax_tree import ASTFactory
from renaissance.syntax_tree.match_finder import match_pattern


def _subject(file_name: str = "/tmp/my_parser_test.py", stmts=None):
    subject = Unit2Pytest.__new__(Unit2Pytest)
    subject.file = file_name
    subject.factory = MagicMock()
    subject.pattern_factory = MagicMock()
    subject.atu = SimpleNamespace(children=stmts or [])
    subject.stmts = stmts or []
    subject.rewriter = MagicMock()
    return subject


def _sig(signature: str, kind: str = "Name"):
    return SimpleNamespace(signature=signature, kind=kind)


def _match(expansions, nodes):
    return SimpleNamespace(expansions=expansions, nodes=nodes)


def test_init_sets_factory_pattern_and_rewriter(mocker):
    fake_atu = SimpleNamespace(children=["stmt"])
    create = mocker.patch("renaissance.refactoring.unit2pytest.ASTFactory.create", return_value=fake_atu)
    pattern_ctor = mocker.patch("renaissance.refactoring.unit2pytest.PythonPatternFactory")
    rewriter_ctor = mocker.patch("renaissance.refactoring.unit2pytest.ASTRewriter", return_value=MagicMock())

    subject = Unit2Pytest("x.py")

    create.assert_called_once_with("x.py")
    pattern_ctor.assert_called_once()
    rewriter_ctor.assert_called_once_with(fake_atu)
    assert subject.stmts == ["stmt"]


def test_raw_renders_nodes_as_indented_block():
    subject = _subject()
    rendered = subject.raw([SimpleNamespace(text="alpha"), SimpleNamespace(text="beta")])
    assert_that(rendered, is_("\n\n    alpha\n\n    beta\n    "))


def test_convert_pytest_invokes_expected_pipeline_steps():
    subject = _subject()
    subject.rewriter.has_changed.side_effect = [True, False]
    subject.convert_test_class = MagicMock()
    subject.restructure_module = MagicMock()
    subject.replace = MagicMock()
    subject.commit = MagicMock()
    subject.convert_parameterized_test = MagicMock()
    subject.convert_test_setup = MagicMock()
    subject.remove_print = MagicMock()
    subject.convert_plain_assert_same_length = MagicMock()
    subject.convert_assert = MagicMock()
    subject.swap_expected_and_actual = MagicMock()
    subject.convert_skip_test = MagicMock()

    subject.convert_pytest()

    subject.convert_test_class.assert_called_once()
    subject.restructure_module.assert_called_once()
    subject.convert_parameterized_test.assert_called_once()
    subject.convert_test_setup.assert_called_once()
    subject.remove_print.assert_called_once()
    subject.convert_plain_assert_same_length.assert_called_once()
    subject.swap_expected_and_actual.assert_called_once()
    subject.convert_skip_test.assert_called_once()
    assert subject.convert_assert.call_count == 6
    assert subject.replace.call_count >= 10


def test_commit_writes_and_rebuilds_when_changed():
    subject = _subject()
    subject.rewriter.has_changed.return_value = True
    subject.rewriter.apply_to_string.return_value = "updated"
    new_atu = SimpleNamespace(children=["next"])
    subject.factory.create_from_text.return_value = new_atu

    with patch("builtins.open", mock_open()):
        with patch("renaissance.refactoring.unit2pytest.ASTRewriter", return_value="next-rewriter"):
            subject.commit()

    subject.factory.create_from_text.assert_called_once_with("updated", subject.file)
    assert subject.atu is new_atu
    assert subject.stmts == ["next"]
    assert subject.rewriter == "next-rewriter"


def test_commit_does_nothing_when_not_changed():
    subject = _subject()
    subject.rewriter.has_changed.return_value = False
    subject.commit()
    subject.factory.create_from_text.assert_not_called()


def test_convert_test_class_updates_only_testcase_bases(mocker):
    subject = _subject()
    subject.pattern_factory.create_statements.return_value = "pattern"
    match_a = _match(
        {"$klass": ["FindThingTest"], "$test_class": [_sig("unittest.TestCase")]},
        [SimpleNamespace(signature="class FindThingTest(unittest.TestCase):")],
    )
    match_b = _match(
        {"$klass": ["OtherClass"], "$test_class": [_sig("BaseClass")]},
        [SimpleNamespace(signature="class OtherClass(BaseClass):")],
    )
    mocker.patch("renaissance.refactoring.unit2pytest.match_pattern", return_value=[match_a, match_b])

    subject.convert_test_class()

    subject.rewriter.replace.assert_called_once()


def test_convert_test_class_removes_testcase_base_for_non_test_suffix(mocker):
    subject = _subject()
    subject.pattern_factory.create_statements.return_value = "pattern"
    match_a = _match(
        {"$klass": ["FindThing"], "$test_class": [_sig("unittest.TestCase")]},
        [SimpleNamespace(signature="class FindThing(unittest.TestCase):")],
    )
    mocker.patch("renaissance.refactoring.unit2pytest.match_pattern", return_value=[match_a])

    subject.convert_test_class()

    replacement = subject.rewriter.replace.call_args.args[0]
    assert_that(replacement, is_("class FindThing:"))


def test_convert_test_setup_adds_pytest_fixture_decorator(mocker):
    subject = _subject()
    subject.pattern_factory.create_statements.return_value = "pattern"
    node = SimpleNamespace(signature="def setUp(self):\n    pass")
    mocker.patch("renaissance.refactoring.unit2pytest.match_pattern", return_value=[_match({}, [node])])

    subject.convert_test_setup()

    replacement = subject.rewriter.replace.call_args.args[0]
    assert_that(replacement, contains_string("@pytest.fixture(autouse=True)"))


def test_convert_assert_swaps_constant_expected_and_actual(mocker):
    subject = _subject()
    subject.pattern_factory.create_statements.return_value = "pattern"
    m = _match({"$exp": [_sig("1", "Constant")], "$act": [_sig("value")]}, ["node"])
    mocker.patch("renaissance.refactoring.unit2pytest.match_pattern", return_value=[m])

    subject.convert_assert("p", "assert_that($exp, is_($act))")

    subject.rewriter.replace.assert_called_once_with("assert_that(value, is_(1))", ["node"], False, False)


def test_convert_assert_keeps_non_constant_order(mocker):
    subject = _subject()
    subject.pattern_factory.create_statements.return_value = "pattern"
    m = _match({"$exp": [_sig("expected")], "$act": [_sig("actual")]}, ["node"])
    mocker.patch("renaissance.refactoring.unit2pytest.match_pattern", return_value=[m])

    subject.convert_assert("p", "assert_that($exp, is_($act))")

    subject.rewriter.replace.assert_called_once_with("assert_that(expected, is_(actual))", ["node"], False, False)


def test_replace_substitutes_expansions_and_cleans_trailing_commas(mocker):
    subject = _subject()
    subject.pattern_factory.create_statements.return_value = "pattern"
    m = _match({"$arg": [SimpleNamespace(signature="X")], "$$more": ["a", "b"]}, ["node"])
    mocker.patch("renaissance.refactoring.unit2pytest.match_pattern", return_value=[m])

    subject.replace("find", "f($arg, $$more ,)")

    subject.rewriter.replace.assert_called_once_with("f(X, a, b)", ["node"], False, False)


def test_to_str_prefers_signature_else_stringifies():
    subject = _subject()
    assert_that(subject.to_str(SimpleNamespace(signature="sig")), is_("sig"))
    assert_that(subject.to_str(42), is_("42"))


def test_convert_parameterized_test_rewrites_decorators(mocker):
    subject = _subject()
    subject.pattern_factory.create_statements.return_value = "pattern"
    arg_self = SimpleNamespace(node=SimpleNamespace(arg="self"))
    arg_factory = SimpleNamespace(node=SimpleNamespace(arg="factory"))
    fun = SimpleNamespace(signature="@parameterized.expand(x)\n@unittest.skip('n')\ndef t(self, factory):\n    pass")
    m = _match({"$$args": [arg_self, arg_factory], "$$varg": []}, [fun])
    mocker.patch("renaissance.refactoring.unit2pytest.match_pattern", return_value=[m])

    subject.convert_parameterized_test()

    replacement = subject.rewriter.replace.call_args.args[0]
    assert_that(replacement, contains_string("@pytest.mark.parametrize"))
    assert_that(replacement, contains_string("@pytest.mark.skip"))


def test_convert_parameterized_test_handles_vararg_and_indented_signature(mocker):
    subject = _subject()
    subject.pattern_factory.create_statements.return_value = "pattern"
    arg_self = SimpleNamespace(node=SimpleNamespace(arg="self"))
    arg_factory = SimpleNamespace(node=SimpleNamespace(arg="factory"))
    fun = SimpleNamespace(
        signature="    @parameterized.expand(x)\n@unittest.skip('n')\n    def t(self, factory, *args):\n        pass"
    )
    m = _match({"$$args": [arg_self, arg_factory], "$$varg": [SimpleNamespace(signature="args")]}, [fun])
    mocker.patch("renaissance.refactoring.unit2pytest.match_pattern", return_value=[m])

    subject.convert_parameterized_test()

    replacement = subject.rewriter.replace.call_args.args[0]
    assert_that(replacement, contains_string('@pytest.mark.parametrize("factory, *args"'))


def test_remove_print_removes_parent_function_when_print_is_only_stmt(mocker):
    subject = _subject()
    subject.pattern_factory.create_statements.return_value = "pattern"
    only_body = SimpleNamespace(body=[1])
    print_node = SimpleNamespace(parent=SimpleNamespace(parent=only_body))
    m = _match({}, [print_node])
    mocker.patch("renaissance.refactoring.unit2pytest.match_pattern", return_value=[m])

    subject.remove_print()

    subject.rewriter.remove.assert_called_once_with([only_body], False, False)


def test_remove_print_removes_print_node_when_function_has_other_statements(mocker):
    subject = _subject()
    subject.pattern_factory.create_statements.return_value = "pattern"
    container = SimpleNamespace(body=[1, 2])
    print_node = SimpleNamespace(parent=SimpleNamespace(parent=container))
    m = _match({}, [print_node])
    mocker.patch("renaissance.refactoring.unit2pytest.match_pattern", return_value=[m])

    subject.remove_print()

    subject.rewriter.remove.assert_called_once_with([print_node], False, False)


def test_convert_plain_assert_same_length_rewrites_to_has_length(mocker):
    code = textwrap.dedent('''
    def test_asert():
        results = ['1']
        count: int = len(results)
        assert 1 == count, "count = " + str(count)
    ''')
    mocker.patch("renaissance.syntax_tree.ast_factory.ASTFactory.create", return_value=PythonASTNode.load_from_text(code))

    expected = textwrap.dedent('''
    def test_asert():
        results = ['1']
        assert_that(results, has_length(1), f"length of results = {len(results)}")
    ''')

    subject = Unit2Pytest('file.py')
    subject.convert_plain_assert_same_length()
    assert_that(subject.rewriter.apply_to_string(), is_(expected))


def test_convert_plain_assert_same_length_uses_act_when_expected_not_constant(mocker):
    subject = _subject()
    subject.pattern_factory.create_statements.return_value = "pattern"
    m = _match(
        {
            "$real": [_sig("rows")],
            "$exp": [_sig("expected", "Name")],
            "$act": [_sig("actual_count")],
        },
        ["node"],
    )
    mocker.patch("renaissance.refactoring.unit2pytest.match_pattern", return_value=[m])

    subject.convert_plain_assert_same_length()

    subject.rewriter.replace.assert_called_once_with(
        'assert_that(rows, has_length(actual_count), f"length of rows = {len(rows)}")',
        ["node"],
        False,
        False,
    )


def test_convert_skip_test_replaces_unittest_skip_attribute(mocker):
    subject = _subject()
    found = SimpleNamespace(to_iterable=lambda: [SimpleNamespace(signature="unittest.skip")])
    mocker.patch("renaissance.refactoring.unit2pytest.ASTFinder.find_kind", return_value=found)

    subject.convert_skip_test()

    subject.rewriter.replace.assert_called_once()


def test_swap_expected_and_actual_when_expected_is_constant(mocker):
    subject = _subject()
    subject.pattern_factory.create_statements.return_value = "pattern"
    m = _match({"$exp": [_sig("7", "Constant")], "$act": [_sig("actual")]}, ["node"])
    mocker.patch("renaissance.refactoring.unit2pytest.match_pattern", return_value=[m])

    subject.swap_expected_and_actual()

    subject.rewriter.replace.assert_called_once_with("assert_that(actual, is_(7))", ["node"], False, False)


def test_restructure_module_wraps_functions_when_module_has_no_class():
    fun = SimpleNamespace(
        kind="FunctionDef",
        signature="def parse(a):\n    return a",
        name="parse",
        node=SimpleNamespace(args=SimpleNamespace(args=[1])),
    )
    subject = _subject(stmts=[fun])

    subject.restructure_module()

    replacement = subject.rewriter.replace.call_args.args[0]
    assert_that(replacement, contains_string("class TestMyParser"))
    assert_that(replacement, contains_string("def parse(self,a):"))


def test_restructure_module_injects_methods_when_class_exists():
    fun = SimpleNamespace(
        kind="FunctionDef",
        signature="def parse(a):\n    return a",
        name="parse",
        node=SimpleNamespace(args=SimpleNamespace(args=[1])),
    )
    cls = SimpleNamespace(kind="ClassDef")
    subject = _subject(stmts=[cls, fun])

    subject.restructure_module()

    replacement = subject.rewriter.replace.call_args.args[0]
    assert_that(replacement, contains_string("def parse(self,a):"))
    assert subject.rewriter.replace.call_args.args[1] == fun


def test_convert_function_adds_self_to_function_signature():
    fun = SimpleNamespace(
        signature="def parse():\n    return 1",
        name="parse",
        node=SimpleNamespace(args=SimpleNamespace(args=[])),
    )
    subject = _subject()

    rendered = subject.convert_function(fun)

    assert_that(rendered, contains_string("def parse(self):"))


def test_convert_file_to_test_class_uses_filename_convention():
    subject = _subject("/tmp/my_parser_test.py")
    assert_that(subject.convert_file_to_test_class(), is_("TestMyParser"))


def test_match_pattern_for_parameterized_finds_one_match():
    code = textwrap.dedent('''
    from parameterized import parameterized

    class TestASTReference:

        @parameterized.expand(Factories.extend())
        def test_definition_declaration_references(self, _, factory, code, *args):
            pass
    ''')
    factory = ASTFactory(PythonASTNode, [])
    pattern_factory = PythonPatternFactory(factory)
    atu = PythonASTNode.load_from_text(code)
    unittest = pattern_factory.create_statements(
        '@parameterized.expand($$parameters)\ndef $fun($$args, *$$vargs):\n    $$stmts')
    found = list(match_pattern(atu.children, unittest))
    assert_that(found, has_length(1))



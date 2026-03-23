import re
from datetime import datetime

from renaissance.impl.python import PythonASTNode, PythonPatternFactory
from renaissance.syntax_tree import ASTProcessor, MatchFinder, ASTRewriter, ASTFactory
from renaissance.syntax_tree.match_finder import match_pattern
from renaissance.utils.refactor_utils import adjust_indent, get_indentation_level

_factory = None
PYUNIT_REPLACEMENT = ""


def _get_factory() -> ASTFactory:
    global _factory
    if _factory is None:
        _factory = ASTFactory(PythonASTNode, [])
    return _factory


def _setup_cli(file):
    factory = _get_factory()
    atu = factory.create(file)
    rewriter = ASTRewriter(atu)
    return atu, rewriter, factory


def _setup(input_code: str, match_str: str):
    factory = _get_factory()
    atu = factory.create_from_text(input_code, "temp.py")
    rewriter = ASTRewriter(atu)
    pattern = PythonPatternFactory(factory).create_python_pattern(match_str)
    return atu, rewriter, pattern


def _apply(rewriter: ASTRewriter) -> str:
    rewriter.apply()
    return rewriter.apply_to_string()


def raw(nodes):
    res = ""
    for node in nodes:
        res += "\n\n    " + node.text
    return res + "\n    "


def convert_taut_to_unittest(file, output_file):
    atu, rewriter, factory = _setup_cli(file)
    py_pattern_factory = PythonPatternFactory(factory, atu)
    ast_refactor = ASTProcessor(atu, factory, in_memory=True)

    # start with smaller items
    replace_taut(ast_refactor)
    remove_decorator(ast_refactor)
    add_self(ast_refactor)
    convert_assert(ast_refactor)
    result = ast_refactor.apply_to_string()

    result = replace_log_emrwxtl(result)
    result = replace_mock_import(result)
    result = convert_tds(result)
    # result = convert_setup_common(pattern_factory, result)
    test_atu2 = factory.create_from_text(result, file)
    rewriter = ASTRewriter(test_atu2)
    pattern = py_pattern_factory.create_python_pattern("def tearDownCommon(self):\n    $$aa")
    if match_pattern(test_atu2.children, [pattern]):
        result = convert_teardown_common(py_pattern_factory, rewriter, test_atu2)
        result = convert_add_patcher(py_pattern_factory, result)
    test_atu3 = factory.create_from_text(result, file)
    rewriter = ASTRewriter(test_atu3)
    convert_import_verify(py_pattern_factory, rewriter, test_atu2)

    result = rewriter.apply_to_string()

    # then migrate bigger scope like class
    # test_atu2 = factory.create(output_file)
    # rewriter2 = ASTRewriter(test_atu2)
    # convert_test_import(pattern_factory, rewriter, test_atu2)
    # print(rewriter2.apply_to_string())
    return rewriter.apply_to_string()


def convert_tds(input):
    tds = "self.tds.append(TestDoubles($a, $b=$c))"
    repl = "self.add_patcher($a, '$b', $c)"
    result = refactor_replace(input, tds, repl)

    tds2 = "self.tds.append(TestDoubles($a=ImprovedStub($b)))"
    repl2 = "self.$a = ImprovedStub($b)"
    return refactor_replace(result, tds2, repl2)
    ### not working, replacement is wrong.
    # tds_pattern = pattern_factory.create_statements('self.tds.append(TestDoubles($a, $b=$c))')
    # for match in match_pattern(test_atu.children, tds_pattern):
    # a = match.expansions["$a"][0].text
    # b = match.expansions["$b"][0]
    # c = match.expansions["$c"][0].text
    # repl = f'self.add_patcher({match.expansions["$a"][0].text}, \'{match.expansions["$b"][0]}\', {match.expansions["$c"][0].text})'
    # rewriter.replace(repl, match.nodes, True, True)


def convert_test_import(pattern_factory, rewriter, test_atu):
    taut_import = pattern_factory.create_statements("import TAUT")
    for match in match_pattern(test_atu.children, taut_import):
        rewriter.remove(match.nodes, False, False)


def convert_import_verify(pattern_factory, rewriter, test_atu):
    import_verify = pattern_factory.create_python_pattern("self.import_and_verify_module('$a')")
    for match in match_pattern(test_atu.children, [import_verify]):
        repl = f'import {match.expansions["$a"][0]}\nself.assertIsNotNone({match.expansions["$a"][0]})'
        rewriter.replace(repl, match.nodes, False, False)


def convert_setup_common(pattern_factory, input):
    test_atu = _get_factory().create_from_text(input, "temp.py")
    insert_code = """# Reset class-level state from OOXA.Stub to ensure clean call counts between tests.
# These dictionaries accumulate across all ImprovedStub instances and persist between tests.
ImprovedStub.ret_vals = {}
ImprovedStub.ret_vals_ex = {}
ImprovedStub.call_logs = {}
ImprovedStub.store_args = {}"""
    replace_str = """self.tds = [
    TestDoubles($a=ImprovedStub($b)),
    TestDoubles($c=ImprovedStub($d)),
    TestDoubles($e=ImprovedStub($f)),
    TestDoubles($g=ImprovedStub($h)),
    TestDoubles($i=ImprovedStub($j))]
"""
    doubles_pattern = pattern_factory.create_python_pattern("self.tds = [$$aa]")
    if match_pattern(test_atu.children, [doubles_pattern]):
        test_doubles = pattern_factory.create_python_pattern(replace_str)
        repl = ""
        list = match_pattern(test_atu.children, [test_doubles])
        for match in match_pattern(test_atu.children, [test_doubles]):
            repl += f'self.{match.expansions["$a"][0]} = ImprovedStub({match.expansions["$b"][0]})\n'
        return refactor_insert_after(input, repl, doubles_pattern)
    return input


def convert_teardown_common(pattern_factory, rewriter, test_atu):
    pattern = pattern_factory.create_python_pattern("def tearDownCommon(self):\n    $$aa")
    repl = """def tearDownCommon(self):
    for p in self.patchers:
        try:
            p.stop()
        except RuntimeError:
            pass
"""
    for match in match_pattern(test_atu.children, [pattern]):
        rewriter.replace(repl, match.nodes, False, False)
    return rewriter.apply_to_string()


def convert_add_patcher(pattern_factory, input):
    pattern = pattern_factory.create_python_pattern("def tearDownCommon(self):\n    $$aa")
    insert_add_patcher = """
def add_patcher(self, target, name, replacement):
    p = patch.object(target, name, replacement)
    p.start()
    self.patchers.append(p)"""
    return refactor_insert_after(input, insert_add_patcher, "def tearDownCommon(self):\n    $$aa")


def insert_doc(content: str, date):
    pattern = r"# -+(#)?\n(#\s+#\n)?#\s+Copyright \(c\) \d{4}, ASML"
    match = re.search(pattern, content)

    if not match:
        print("Comment block not found.")
        return content

    # Find the beginning of the line containing the comment
    position = match.start()
    line_start = content.rfind("\n", 0, position) + 1
    if line_start == 0:  # If comment is at the beginning of the file
        line_start = 0

    # Insert the new line before the comment block
    print(get_change_comment(date))
    modified_content = content[:line_start] + get_change_comment(date) + "\n" + content[line_start:]
    return modified_content


def remove_import_taut(ast_refactor: ASTProcessor) -> None:
    """
    Removes import TAUT
    """
    ast_refactor.find_kind("Import").filter(lambda node: node.name.find("TAUT") > 0).for_each(
        lambda node: ast_refactor.remove(node, True, True)
    )


def replace_taut_skip(ast_refactor):
    """
    replace @TAUT.skip_test by @unittest.skip
    """
    ast_refactor.find_kind("Attribute").filter(lambda node: node.name == "TAUT.skip_test").for_each(
        lambda node: ast_refactor.replace("@unittest.skip", node)
    )


def add_self(ast_refactor):
    """
    replace mock by unittest.mock and using patch
    """
    matching = [
        "emrwxread",
        "emrwxwidxread",
        "emrwxviprxinterface",
        "whxstream2",
        "gtaaxtxmark",
        "mark_upd_q",
    ]
    list = ast_refactor.find_kind("Name").filter(lambda node: node.name in matching).to_list()
    ast_refactor.find_kind("Name").filter(lambda node: node.name in matching).for_each(
        lambda node: ast_refactor.replace("self." + node.name, node, False, False)
    )


def remove_decorator(ast_refactor):
    ast_refactor.find_kind("Attribute").filter(lambda node: node.name == "TAUT.log_stub").for_each(
        lambda node: ast_refactor.remove(node, False, False)
    )


def convert_assert(ast_refactor):
    ast_refactor.find_kind("Attribute").filter(lambda node: node.name == "self.assert_equal").for_each(
        lambda node: ast_refactor.replace("self.assertEqual", node, False, False)
    )


def insert_doc_func(input_code, date):
    pattern = """# -----------------------------------------------------------------------------#
#                                                                             #
#                   Copyright (c) 2016, ASML Netherlands B.V.                 #
"""
    insert_code = get_change_comment()
    return refactor_insert_before(input_code, insert_code, pattern)


def remove_taut_import(input_code):
    return refactor_remove(input_code, "import TAUT")


def replace_taut(ast_refactor):
    """
    replace TAUT.TestCase by unittest.TestCase
    """
    ast_refactor.find_kind("Attribute").filter(lambda node: node.name == "TAUT.TestCase").for_each(
        lambda node: ast_refactor.replace("unittest.TestCase", node, False, False)
    )
    ast_refactor.find_kind("Name").filter(lambda node: node.name == "TestCase").for_each(
        lambda node: ast_refactor.replace("unittest.TestCase", node, False, False)
    )


def replace_mock_import(input_code):
    """
    replace mock by unittest.mock and using patch
    """
    pattern1 = "import mock\n"
    result = refactor_remove(input_code, pattern1)
    pattern2 = "from TAUT import TestCase, TestDoubles"
    replacement = "try:\n    from unittest.mock import patch\nexcept ImportError:\n    from mock import patch\n"
    return refactor_replace(result, pattern2, replacement)


def replace_log_emrwxtl(input_code):
    pattern1 = "with TAUT.TestDoubles(emrwxtl=FakeEMRWxTL(None)):\n    log = TAUT.Logger()\n    $$aa"
    replace_pattern = "fake_emrwxtl = FakeEMRWxTL(None)\n$$aa"
    result = refactor_replace(input_code, pattern1, replace_pattern)

    pattern2 = "emrwxtl.$a($$bb)"
    result2 = refactor_replace(result, pattern2, "fake_emrwxtl.$a($$bb)")

    pattern3 = "$c = emrwxtl.$a($$bb)"
    return refactor_replace(result2, pattern3, "$c = fake_emrwxtl.$a($$bb)")


def insert_class(input_code, insert_code):
    insert_pattern = "def b():\n    $$bb"
    return refactor_insert_after(input_code, insert_code, insert_pattern)


def refactor_teardown(input_code):
    pattern1 = "for double in self.doubles:\n    double.exit()"
    replace_pattern = "patch.stopall()"
    result = refactor_replace(input_code, pattern1, replace_pattern)

    insert_code = """EMRWxCONTEXT.emrmxcontext.reset_method_attributes("start_wafer")
EMRWxCONTEXT.emrmxcontext.reset_method_attributes("finish_wafer")
EMRWxCONTEXT.emrmxcontext.reset_method_attributes("start_lot")
EMRWxCONTEXT.emrmxcontext.reset_method_attributes("finish_lot")
"""
    pattern2 = "self._patch_readout_data_filler.stop()"
    return refactor_insert_before(result, insert_code, pattern2)


def refactor_setup(input_code):
    # add self. at front of interface EMRMxCONTEXT
    pattern1 = "context_stub = $c"
    replace_pattern = "self.context_stub = $c"
    result = refactor_replace(input_code, pattern1, replace_pattern)

    pattern2 = """self.doubles.append(
    TAUT.TestDoubles(module=EMRMxAPxData.data.rep, context=context_stub)
)"""
    replace_pattern2 = """self.patches.append(patch.object(EMRMxAPxData.data.rep, 'context', self.context_stub))"""
    result2 = refactor_replace(result, pattern2, replace_pattern2)
    # should able to replace all context_stub with self.context_stub

    # remove self.doubles
    pattern2 = "self.doubles = $aa"
    result3 = refactor_remove(result2, pattern2)

    # insert self.patches
    insert_code = "self.patches = []"
    pattern3 = "self.context_stub = EMRMxCONTEXT.EMRMxCONTEXTStub()"
    result4 = refactor_insert_after(result3, insert_code, pattern3)

    # replace doubles with patches
    pattern4 = """self.doubles.append(TAUT.TestDoubles(emrmxcontext=context_stub))"""
    replace_pattern2 = """self.patches.append(patch('EMRMxCONTEXT.emrmxcontext', self.context_stub))"""
    result5 = refactor_replace(result4, pattern4, replace_pattern2)
    pattern5 = """self.doubles.append(
                TAUT.TestDoubles(
                    module=$mod, $e=$f
                )
            )
        """
    replace_pattern3 = """self.patches.append(patch.object($mod, '$e', $f))"""
    result6 = refactor_replace(result5, pattern5, replace_pattern3)

    insert_code = """for p in self.patches:
    p.start()
"""
    pattern6 = "EMRMxAPxData.data.adv_wp = EMRMxADVxWP.input()"
    return refactor_insert_before(result6, insert_code, pattern6)


def refactor_testdoubles_fun(input_code):
    """refactor cannot use standard replace method, because it needs to fix the indentation"""
    pattern1 = """def $a($$b):
    self.doubles.append(
        TAUT.TestDoubles(
            module=$mod, $e=$f
        )
    )
    $$c
"""
    replace_pattern = """def $a($$b):
    with patch.object($mod, '$e', $f):
        $$c
"""
    return refactor_replace(input_code, pattern1, replace_pattern)


def refactor_testdoubles_class(input_code):
    match_pattern = """class $a(TAUT.TestCase):
    
    def setUp(self):
        $$bb
        self.doubles = []
        $$cc
        self.doubles.append(
            TAUT.TestDoubles(
                module=$mod1, 
                $e1=$f1,
            )
        )
        self.doubles.append(
            TAUT.TestDoubles(
                module=$mod2, 
                $e2=$f2,
            )
        )
        $$dd
        
    def tearDown(self):
        $$gg
        for double in self.doubles:
            double.exit()"""
    replace_pattern = """class $a(unittest.TestCase):
    
    def setUp(self):
        $$bb
        $$cc
        self.patches = [
            patch.object($mod1, '$e1', $f1),
            patch.object($mod2, '$e2', $f2),
        ]
        for p in self.patches:
            p.start()

        $$dd
        
    def tearDown(self):
        $$gg
        for p in self.patches:
            p.stop()"""
    return refactor_replace(input_code, match_pattern, replace_pattern)


def refactor_replace(input_code: str, before: str, after: str):
    atu, rewriter, before_pattern = _setup(input_code, before)

    for match in match_pattern(atu.children, [before_pattern]):
        replacement = after
        for snippets in match.expansions:
            raw = raw_text(match.expansions[snippets], snippets)
            # indentation adjustment may need
            if snippets.count("$") == 2:
                before_level = get_indentation_level(before, snippets)
                after_level = get_indentation_level(after, snippets)
                if before_level != after_level:
                    raw = adjust_indent(raw, after_level - before_level)
            replacement = replacement.replace(snippets, raw)
        rewriter.replace(replacement, match.nodes)
    return _apply(rewriter)


def refactor_remove(input_code: str, match_str: str):
    atu, rewriter, matched_pattern = _setup(input_code, match_str)

    for ma in match_pattern(atu.children, [matched_pattern]):
        rewriter.remove(ma.nodes)
    return _apply(rewriter)


def refactor_insert_after(input_code: str, insert_code: str, match_str: str):
    atu, rewriter, matched_pattern = _setup(input_code, match_str)
    matches = match_pattern(atu.children, [matched_pattern])
    if not matches:
        return input_code  # No matches found, return original code
    matched = matches[0]
    rewriter.insert_after(insert_code, matched.nodes)
    return _apply(rewriter)


def refactor_insert_before(input_code: str, insert_code: str, match_str: str):
    atu, rewriter, matched_pattern = _setup(input_code, match_str)
    matches = match_pattern(atu.children, [matched_pattern])
    if not matches:
        return input_code  # No matches found, return original code
    matched = matches[0]
    rewriter.insert_before(insert_code, matched.nodes)
    return _apply(rewriter)


def get_change_comment(date=None):
    """
    Generate a formatted change comment with today's date.

    Args:
        change_id (str): The change ID (e.g., 'SWCHGxxxxxxxx')
        description (str): The description of the change

    Returns:
        str: Formatted change comment string
    """
    change_id = "SWCHGxxxxxxxx"
    description = "Add assert_raises method to Asserter class."
    if date is None:
        # No date provided, use today
        formatted_date = datetime.now()
    else:
        formatted_date = datetime.strptime(date, "%m-%d-%Y")
    return f"# {formatted_date.strftime('%m-%d-%Y')} : {change_id} SBYN {description}"


def raw_text(nodes, snippets) -> str:
    res = ""
    start_offset = 0
    end_offset = 0
    if "$$" in snippets:
        for node in nodes:
            if isinstance(node, PythonASTNode):
                if start_offset == 0 or node.offset < start_offset:
                    start_offset = node.offset
                if end_offset == 0 or node.end_offset > end_offset:
                    end_offset = node.end_offset
        return node.root.signature[start_offset:end_offset]
    else:
        for node in nodes:
            if isinstance(node, PythonASTNode):
                res += node.text
            else:
                res += str(node)
    return res  # + '\n'

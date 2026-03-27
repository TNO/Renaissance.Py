import os
import re
import textwrap
from datetime import datetime
from pathlib import Path
from typing import Dict

from renaissance.impl.python import PythonASTNode, PythonPatternFactory
from renaissance.refactoring.python_refactoring import PythonRefactoring
from renaissance.syntax_tree import ASTProcessor, MatchFinder, ASTRewriter, ASTFactory
from renaissance.syntax_tree.match_finder import match_pattern

_factory = None

class Taut2Pyunit(PythonRefactoring):

    def __init__(self, file):
        super().__init__(file)
        self.white_list_pattern = 'EMRWxTL_unittest'
        self.black_list_pattern = '_migrated'

    def run(self):
        if (self.black_list_pattern in self.filename
         or self.white_list_pattern not in self.filename):
            print(f"skipping:         {Path(self.filename).resolve()}")
            return
        print(f"Taut to pyunit migration: {Path(self.filename).resolve()}")

        self.replace_taut()
        self.remove_decorator()
        self.add_self()
        self.convert_assert()
        self.remove_stubserver()
        self.replace_mock()
        self.commit()

        self.replace_log_emrwxtl()

        try:
            # result = insert_doc(result, "01-22-2026")
            with open(self.get_migrated_path(self.filename), "w") as f:
                f.write(self.apply_to_string())
        except FileNotFoundError:
            print(f"Error: File '{self.filename}' not found.")

    def get_migrated_path(self, file_path):
        """
        Convert a file path to add '_migrated' before the extension.

        Example: 'taut.py' -> 'taut_migrated.py'
        """
        # Split the path into filename and extension
        base, ext = os.path.splitext(file_path)

        # Create the new path with '_migrated' added
        new_path = f"{base}_migrated{ext}"

        return new_path



    def replace_taut(self):
        """
        replace TAUT.TestCase by unittest.TestCase
        """
        [self.replace("unittest.TestCase", node, False, False)
         for node in self.find_kind("Attribute") if node.name == "TAUT.TestCase"]
        [self.replace("unittest.TestCase", node, False, False)
         for node in self.find_kind("Name") if node.name == "TestCase"]

    def remove_decorator(self):
        [self.remove(node, False, False)
         for node in self.find_kind("Attribute") if node.name == "TAUT.log_stub"]

    def add_self(self):
        matching = [
            "emrwxread",
            "emrwxwidxread",
            "emrwxviprxinterface",
            "whxstream2",
            "gtaaxtxmark",
            "mark_upd_q",
            "gtaaxtxmark",
            "gtaaxtxmrkxadv",
            "emrwxwidxcfg",
            "wlxload",
            "wlxclear",
            "gtmwxtxws",
            "emtlxt",
            "emtlxtxmc",
            "emtlxtxwid",
            "emrwxviprxtestlog",
            "emrwxviprxwh",
        ]
        parent_func = [
            "setUpCommon",
            "setUp"
        ]
        # list = ast_refactor.find_kind("Name").filter(lambda node: node.name in matching).to_list()
        [self.replace("self." + node.name, node, False, False)
         for node in self.find_kind("Name") if node.name in matching]

        matching2 = ['EMRWxREAD.emrwxread']
        [self.replace('self.' + node.name.split('.')[1], node, False, False)
         for node in self.find_kind("Attribute") if
         node.name in matching2 and node.get_ancestor("FunctionDef").name not in parent_func]

    def convert_assert(self):
        [self.replace("self.assertFalse", node, False, False)
         for node in self.find_kind("Attribute") if node.name == "self.assert_false"]
        [self.replace("self.assertTrue", node, False, False)
         for node in self.find_kind("Attribute") if node.name == "self.assert_true"]
        [self.replace("self.assertEqual", node, False, False)
         for node in self.find_kind("Attribute") if node.name == "self.assert_equal"]

    def remove_stubserver(self):
        [self.remove(node, False, False)
         for node in self.find_kind("Attribute") if node.name == "TAUT.StubServer"]

    def replace_mock(self):
        [self.replace("patch", node, False, False)
         for node in self.find_kind("Attribute") if
         node.name == "mock.patch" and node.parent.parent.name == "decorator_list"]

    def replace_log_emrwxtl(self):
        taut_test_doubles = self.pattern_factory.create_statements("with TAUT.TestDoubles(emrwxtl=FakeEMRWxTL(None)):\n    log = TAUT.Logger()\n    $$aa")
        for match in match_pattern(self.root.children, taut_test_doubles):
            repl = f"fake_emrwxtl = FakeEMRWxTL(None)\n{match["$$aa"]}"
            self.replace(repl, match.nodes, False, False)
            self.commit()
            print(self.apply_to_string())

            func_call = self.pattern_factory.create_statements("emrwxtl.$a($$bb)")
            for call in match_pattern(match.nodes, func_call):
                repl = call.signature.replace("emrwxtl", "fake_emrwxtl")
                #self.replace(repl, call.nodes, False, False)
                #self.commit()
            # result = self.apply_to_string()
        assign = self.pattern_factory.create_statements("$c = emrwxtl.$a($$bb)")
        for match in match_pattern(self.root.children, assign):
            repl = call.signature.replace("emrwxtl", "fake_emrwxtl")
            #self.replace(repl, match.nodes, False, False)
            #self.commit()

def convert_taut_to_unittest(file, output_file):
    atu, rewriter, factory = _setup_cli(file)
    py_pattern_factory = PythonPatternFactory(factory)
    ast_refactor = ASTProcessor(atu, factory, in_memory=True)

    # start with smaller items
    #replace_taut(ast_refactor)
    # remove_decorator(ast_refactor)
    # add_self(ast_refactor)
    # convert_assert(ast_refactor)
    #remove_stubserver(ast_refactor)
    #replace_mock(ast_refactor)
    result = ast_refactor.apply_to_string()

    #result = replace_log_emrwxtl(result)
    result = replace_mock_import(result)
    result = convert_tds(result)
    result = replace_taut_import(result)

    test_atu2 = factory.create_from_text(result, file)
    rewriter = ASTRewriter(test_atu2)
    pattern = py_pattern_factory.create_python_pattern("def tearDownCommon(self):\n    $$aa")
    if match_pattern(test_atu2.children, [pattern]):
        result = convert_setup_common(py_pattern_factory, rewriter, test_atu2, ast_refactor)
    test_atu3 = factory.create_from_text(result, file)
    rewriter = ASTRewriter(test_atu3)
    pattern = py_pattern_factory.create_python_pattern("def tearDownCommon(self):\n    $$aa")
    if match_pattern(test_atu3.children, [pattern]):
        result = convert_teardown_common(py_pattern_factory, rewriter, test_atu3)
        result = convert_add_patcher(py_pattern_factory, result)

    result = convert_setup(result)
    result = convert_teardown(result)
    if result.find("self.patches = []") > 0:
        result = insert_patch_import(result)
    result = refactor_testdoubles_fun(result)
    test_atu5 = factory.create_from_text(result, file)
    rewriter = ASTRewriter(test_atu5)
    convert_import_verify(py_pattern_factory, rewriter, test_atu5)
    result = rewriter.apply_to_string()

    # then migrate bigger scope like class
    #test_atu2 = factory.create(output_file)
    #rewriter2 = ASTRewriter(test_atu2)
    #convert_test_import(pattern_factory, rewriter, test_atu2)
    #print(rewriter2.apply_to_string())
    return rewriter.apply_to_string()

def convert_tds(input):
    tds = "self.tds.append(TestDoubles($a, $b=$c))"
    repl = "self.add_patcher($a, '$b', $c)"
    result = refactor_replace(input, tds, repl)

    tds2 = "self.tds.append(TestDoubles($a=ImprovedStub($b)))"
    repl2 = "self.$a = ImprovedStub($b)"
    return refactor_replace(result, tds2, repl2)
    ### not working, replacement is wrong.
    #tds_pattern = pattern_factory.create_statements('self.tds.append(TestDoubles($a, $b=$c))')
    #for match in match_pattern(test_atu.children, tds_pattern):
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


def convert_setup_common(pattern_factory, rewriter, test_atu, ast_refactor):
    insert_code = """ImprovedStub.ret_vals = {}
ImprovedStub.ret_vals_ex = {}
ImprovedStub.call_logs = {}
ImprovedStub.store_args = {}

"""
    tds_pattern = pattern_factory.create_python_pattern('self.tds = [$$aa]')
    for match in match_pattern(test_atu.children, [tds_pattern]):
        init_stubs = ''
        repl = 'self.patchers = [\n'
        doubles_pattern = pattern_factory.create_expression('TestDoubles($a=ImprovedStub($b))')
        for matched_doubles in match_pattern(match.expansions["$$aa"], [doubles_pattern]):
            init_stubs += f'self.{matched_doubles.expansions["$a"][0]} = ImprovedStub({matched_doubles.expansions["$b"][0].signature})\n'
            interface_stub = find_import_interface(matched_doubles.expansions["$b"][0].signature, ast_refactor)
            repl += f'    patch.object({interface_stub}, \'{matched_doubles.expansions["$a"][0]}\', self.{matched_doubles.expansions["$a"][0]}),\n'
        repl += ']\n\n'
    p_start = """for p in self.patchers:
    p.start()
"""
    repl = insert_code + init_stubs + repl + p_start
    result = refactor_replace(test_atu.signature, 'self.tds = [$$aa]', repl)

    return result

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
    [ast_refactor.remove(node, True, True)
    for node in ast_refactor.find_kind("Import") if node.name == "TAUT"]


def replace_taut_skip(ast_refactor):
    """
    replace @TAUT.skip_test by @unittest.skip
    """
    [ast_refactor.replace("@unittest.skip", node)
     for node in ast_refactor.find_kind("Attribute") if node.name == "TAUT.skip_test"]

    #ast_refactor.find_kind('Attribute'). \
        #filter(lambda node: node.name in matching2). \
        #for_each(lambda node: ast_refactor.replace('self.' + node.name.split('.')[1], node, False, False))
def in_setupcommon(node):
    if node.get_ancestor('FunctionDef') and node.get_ancestor('FunctionDef').name == 'setUpCommon':
        return True
    return False




def insert_doc_func(input_code, date):
    pattern = """# -----------------------------------------------------------------------------#
#                                                                             #
#                   Copyright (c) 2016, ASML Netherlands B.V.                 #
"""
    insert_code = get_change_comment()
    return refactor_insert_before(input_code, insert_code, pattern)


def remove_taut_import(input_code):
    return refactor_remove(input_code, "import TAUT")




def replace_mock_import(input_code):
    """
    replace mock by unittest.mock and using patch
    """
    pattern1 = "import mock\n"
    result = refactor_remove(input_code, pattern1)
    pattern2 = "from TAUT import TestCase, TestDoubles"
    replacement = "try:\n    from unittest.mock import patch\nexcept ImportError:\n    from mock import patch\n"
    return refactor_replace(result, pattern2, replacement)

def replace_taut_import(input_code):
    pattern1 = "import TAUT\n"
    result = refactor_remove(input_code, pattern1)
    pattern2 = "from TAUT import TestCase"
    result2 = refactor_remove(result, pattern2)
    pattern3 =  "from TAUT import TestDoubles"
    replacement = "try:\n    from unittest.mock import patch\nexcept ImportError:\n    from mock import patch\n"
    return refactor_replace(result2, pattern3, replacement)

def insert_patch_import(input_code):
    insert = "try:\n    from unittest.mock import patch\nexcept ImportError:\n    from mock import patch\n"
    pattern = "import unittest"
    return refactor_insert_after(input_code, insert, pattern)

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

def convert_teardown(input_code):
    matched_pattern = """for double in self.doubles:
    double.exit()"""
    repl_pattern = """for p in self.patches:
    p.stop()"""
    return refactor_replace(input_code, matched_pattern, repl_pattern)

def convert_setup(input_code):
    # remove doubles init
    pattern1 = 'doubles = []'
    replacement = 'self.patches = []'
    result = refactor_replace(input_code, pattern1, replacement)

    pattern2 = 'self.doubles = []'
    result = refactor_replace(result, pattern2, replacement)

    # init atu rewriter for match pattern
    test_atu = _get_factory().create_from_text(result, 'file.py')
    rewriter = ASTRewriter(test_atu)
    pattern_factory = PythonPatternFactory(_get_factory())

    # convert doubles to patch
    convert_test_doubles("doubles.append(TAUT.TestDoubles($a=$b))", test_atu, rewriter)
    convert_test_doubles("self.doubles.append(TAUT.TestDoubles($a=$b))", test_atu, rewriter)

    # convert doubles to patch.object
    insert_node = None
    pattern_outer = pattern_factory.create_statements("def setUp(self):\n    $$aa")
    for setup_func in match_pattern(test_atu.children, pattern_outer):
        
        pattern4 = pattern_factory.create_statements('doubles.append(TAUT.TestDoubles(module=$mod, $b=$c))')
        matched_pattern = match_pattern(setup_func.nodes, pattern4)
        for index, match in enumerate(matched_pattern):
            repl_pattern = f'self.patches.append(patch.object({match.expansions['$mod'][0].name}, \'{match.expansions['$b'][0]}\', {match.expansions['$c'][0].signature}))'
            rewriter.replace(repl_pattern, match.nodes, False, False)
            if index == len(matched_pattern) - 1:
                insert_node = match.nodes[-1]
                insert_code = """\nfor p in self.patches:
    p.start()"""
                rewriter.insert_after(insert_code, insert_node, False, False)

        pattern4_1 = pattern_factory.create_statements('self.doubles.append(TAUT.TestDoubles(module=$mod, $b=$c))')
        matched_pattern_1 = match_pattern(setup_func.nodes, pattern4_1)
        for index, match in enumerate(matched_pattern_1):
            repl_pattern = f'self.patches.append(patch.object({match.expansions['$mod'][0].name}, \'{match.expansions['$b'][0]}\', {match.expansions['$c'][0].signature}))'
            rewriter.replace(repl_pattern, match.nodes, False, False)
            if index == len(matched_pattern_1) - 1:
                insert_node = match.nodes[-1]
                insert_code = """\nfor p in self.patches:
    p.start()\n"""
                rewriter.insert_after(insert_code, insert_node, False, False)

    pattern5 = pattern_factory.create_statements('self.doubles = doubles')
    for match in match_pattern(test_atu.children, pattern5):
        rewriter.remove(match.nodes, False, False)
    return rewriter.apply_to_string()

def insert_p_start(test_atu, rewriter, pattern_factory):
    insert_code = """\nfor p in self.patches:
    p.start()"""
    pattern = pattern_factory.create_statements("def setUp(self):\n    $$aa\n    self.patches.append($b)\n    $$cc")
    for match in match_pattern(test_atu.children, pattern):
        insert_node = match.expansions['$$cc'][0]
        rewriter.insert_before(insert_code, insert_node, False, False)
    pattern = pattern_factory.create_statements("def setUp(self):\n    $$aa\n    self.patches.append($b)\n    $$cc")
    for match in match_pattern(test_atu.children, pattern):
        insert_node = match.expansions['$$cc'][0]
        rewriter.insert_before(insert_code, insert_node, False, False)
    # rewriter.insert_after(insert_code,, False, False)
    # not all setup need p.start. only
def convert_test_doubles(doubles: str, test_atu, rewriter):
    mappings: Dict[str, str] = {
        'emrmxcontext': 'EMRMxCONTEXT',
        # Add more mappings here
    }
    pattern_factory = PythonPatternFactory(_get_factory())
    doubles_pattern = pattern_factory.create_statements(doubles)
    for match in match_pattern(test_atu.children, doubles_pattern):
        keyword = match.expansions['$a'][0]
        if match.expansions['$a'][0] in mappings.keys():
            keyword = mappings[match.expansions['$a'][0]]
        repl_pattern = f'self.patches.append(patch(\'{keyword}.{match.expansions['$a'][0]}\', {match.expansions['$b'][0].name}))'
        rewriter.replace(repl_pattern, match.nodes, False, False)

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
    return refactor_replace_indent(input_code, pattern1, replace_pattern)

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

def find_import_interface(name: str, ast_refactor):
    interface = name
    if name.islower():
        node_list = [ node for node in ast_refactor.find_kind("Import(?:From)") if node.name == name ]
        if node_list:
            if node_list[0].kind == 'ImportFrom':
                interface = node_list[0].properties['module']
            else:
                interface = node_list[0].name if node_list else name
    return interface.split('.')[0]

def refactor_replace_dedent(input_code: str, before: str, after: str):
    atu, rewriter, before_pattern = _setup(input_code, before)

    for match in match_pattern(atu.children, [before_pattern]):
        replacement = after
        for snippets in match.expansions:
            raw_code = "\n".join([node.signature for node in match.expansions[snippets]])
            replacement = replacement.replace(snippets, raw_code)
        rewriter.replace(replacement, match.nodes, False, False)
    return _apply(rewriter)

def refactor_replace_indent(input_code: str, before: str, after: str):
    atu, rewriter, before_pattern = _setup(input_code, before)

    for match in match_pattern(atu.children, [before_pattern]):
        replacement = after
        for snippets in match.expansions:
            raw_code = textwrap.indent("\n".join([node.signature for node in match.expansions[snippets] if type(node).__name__ == "PythonASTNode"] ), "    ")
            replacement = replacement.replace(snippets, raw_code)
        rewriter.replace(replacement, match.nodes, False, False)
    return _apply(rewriter)

def refactor_replace(input_code: str, before: str, after: str):
    atu, rewriter, before_pattern = _setup(input_code, before)

    for match in match_pattern(atu.children, [before_pattern]):
        replacement = after
        for snippets in match.expansions:
            raw_code = raw_text(match.expansions[snippets], snippets) # read $$c textwrap.indent
            replacement = replacement.replace(snippets, raw_code)
        rewriter.replace(replacement, match.nodes, False, False)
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
    if nodes:
        if "$$" in snippets:
            for node in nodes:
                if isinstance(node, PythonASTNode):
                    if start_offset == 0 or node.offset < start_offset:
                        start_offset = node.offset
                    if end_offset == 0 or node.end_offset > end_offset:
                        end_offset = node.end_offset
            return nodes[0].root.signature[start_offset:end_offset]
        else:
            for node in nodes:
                if isinstance(node, PythonASTNode):
                    res += node.text
                else:
                    res += str(node)
        return res  # + '\n'
    return res

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
    atu = factory.create_from_text(input_code, 'temp.py')
    rewriter = ASTRewriter(atu)
    pattern = PythonPatternFactory(factory).create_python_pattern(match_str)
    return atu, rewriter, pattern

def _apply(rewriter: ASTRewriter) -> str:
    rewriter.apply()
    return rewriter.apply_to_string()

def convert_except_x(s):
    return ''.join([char if char == 'x' else char.upper() for char in s])
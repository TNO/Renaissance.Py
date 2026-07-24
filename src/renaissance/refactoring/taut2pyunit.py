import os
import re
import textwrap
from datetime import datetime
from pathlib import Path
from typing import Dict

import test_data.test_insert as tst_insert
import test_data.test_class as tst_class
from renaissance.impl.types import Name, Attribute, FunctionDef, ImportStatement, ImportFrom
from renaissance.refactoring.python_refactoring import PythonRefactoring
from renaissance.syntax_tree.match_finder import match_pattern


class Taut2Pyunit(PythonRefactoring):

    def __init__(self, file):
        super().__init__(file)
        self.white_list_reg = r"_test|_unittest|_tests"
        self.black_list_reg = r"_migrated|_after|_original"
        self.comp = "ABCD"

    def run(self):
        # if re.search(self.black_list_reg, self.filename):
        #     print(f"skipping:         {Path(self.filename).resolve()}")
        #     return
        # if not re.search(self.white_list_reg, self.filename):
        #     print(f"skipping:         {Path(self.filename).resolve()}")
        #     return
        print(f"Taut to pyunit migration: {Path(self.filename).resolve()}")

        # conditional refactor
        if "AP_core_functionality_test" in self.filename:
            self.insert_asserter()
            self.remove_assert_func()
            self.replace_unittest_with_asserter()
            self.assert_func()
            self.commit()

        self.replace_mock()
        self.remove_stubserver()
        self.replace_taut()
        self.remove_decorator()
        self.add_self()
        self.convert_assert()
        self.convert_testdoubles_fun()

        self.replace_log_compxtl("emrw")
        self.replace_log_compxtl("abcd")
        self.remove_taut_import()
        self.remove_testoob_import()
        self.replace_taut_import()
        self.convert_setup_common()
        self.convert_teardown_common()
        self.convert_add_patcher()
        self.convert_teardown()
        self.convert_setup()
        self.convert_import_verify()
        self.shared_setup()
        self.commit()
        self.with_testdoubles()
        self.commit()

        if self.root.signature.find("self.patches = []") > 0 or self.root.signature.find("patch.object") > 0:
            self.insert_patch_import()
        self.commit()

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
        for index in range(self.find_ast_type(Attribute).__len__()):
            node = self.find_ast_type(Attribute)[index]
            if node.name == "TAUT.TestCase":
                self.replace("unittest.TestCase", node, False, False)
        for index in range(self.find_ast_type(Name).__len__()):
            node = self.find_ast_type(Name)[index]
            if node.name == "TestCase":
                self.replace("unittest.TestCase", node, False, False)
        # [(self.replace("unittest.TestCase", node, False, False), self.commit()) for node in self.find_ast_type(Attribute) if node.name == "TAUT.TestCase"]
        # [(self.replace("unittest.TestCase", node, False, False), self.commit()) for node in self.find_ast_type(Name) if node.name == "TestCase"]

    def remove_decorator(self):
        [self.remove(node, False, False) for node in self.find_ast_type(Attribute) if node.name == "TAUT.log_stub"]

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
        parent_func = ["setUpCommon", "setUp"]
        [self.replace("self." + node.name, node, False, False) for node in self.find_ast_type(Name) if node.name in matching]

        matching2 = ["EMRWxREAD.emrwxread"]
        [
            self.replace("self." + node.name.split(".")[1], node, False, False)
            for node in self.find_ast_type(Attribute)
            if node.name in matching2 and node.get_ancestor("FunctionDef").name not in parent_func
        ]

    def convert_assert(self):
        [self.replace("self.assertFalse", node, False, False) for node in self.find_ast_type(Attribute) if node.name == "self.assert_false"]
        [self.replace("self.assertTrue", node, False, False) for node in self.find_ast_type(Attribute) if node.name == "self.assert_true"]
        [self.replace("self.assertEqual", node, False, False) for node in self.find_ast_type(Attribute) if node.name == "self.assert_equal"]
        [self.replace("self.assertRaises", node, False, False) for node in self.find_ast_type(Attribute) if node.name == "self.assert_raises"]

    def remove_stubserver(self):
        [self.remove(node, False, False) for node in self.find_ast_type(Attribute) if node.name == "TAUT.StubServer"]

    def replace_mock(self):
        [
            self.replace("patch", node, False, False)
            for node in self.find_ast_type(Attribute)
            if node.name == "mock.patch" and node.parent.parent.name == "decorator_list"
        ]

    def replace_log_compxtl(self, comp):
        func_call = self.pattern_factory.create_statements(f"{comp}xtl.$a($$bb)")
        for call in match_pattern(self.root.children, func_call):
            repl = call.signature.replace(f"{comp}xtl", f"fake_{comp}xtl")
            self.replace(repl, call.nodes, False, False)

        assign = self.pattern_factory.create_statements(f"$c = {comp}xtl.$a($$bb)")
        for match in match_pattern(self.root.children, assign):
            repl = match.signature.replace(f"{comp}xtl", f"fake_{comp}xtl")
            self.replace(repl, match.nodes, False, False)
        self.commit()
        taut_test_doubles = self.pattern_factory.create_statements(
            f"with TAUT.TestDoubles({comp}xtl=Fake{comp.upper()}xTL(None)):\n    log = TAUT.Logger()\n    $$aa"
        )
        for match in match_pattern(self.root.children, taut_test_doubles):
            repl = f"fake_{comp}xtl = Fake{comp.upper()}xTL(None)\n{match["$$aa"]}"
            self.replace(repl, match.nodes, False, False)
        self.commit()

    def remove_testoob_import(self):
        testoob_import = self.pattern_factory.create_statements(
            "try:\n    import testoob as unittest\nexcept ImportError:\n    import unittest\n"
        )
        matches = match_pattern(self.root.children, testoob_import)
        if not matches:
            return
        for match in matches:
            self.remove(match.nodes, False, False)
        self.commit()
        if "import unittest\n" not in self.root.signature:
            anchor = self._first_top_level_import_node() or self.root.children[0]
            self.insert_before("import unittest\n", anchor, False, False)

    def _first_top_level_import_node(self):
        """Return the first direct child of root that is a top-level import."""
        for imp in self.find_ast_type(ImportStatement):
            node = imp
            while node.parent is not None and node.parent is not self.root:
                node = node.parent
            if node.parent is self.root:
                return node
        return None

    def remove_taut_import(self):
        taut_import = self.pattern_factory.create_statements("import TAUT\n")
        for match in match_pattern(self.root.children, taut_import):
            self.remove(match.nodes, False, False)

    def replace_taut_import(self):
        """
        replace mock by unittest.mock and using patch
        """
        mock = self.pattern_factory.create_statements("import mock\n")
        for match in match_pattern(self.root.children, mock):
            self.remove(match.nodes, False, False)

        test_case = self.pattern_factory.create_statements("from TAUT import TestCase")
        for match in match_pattern(self.root.children, test_case):
            self.remove(match.nodes, False, False)
        import_taut = self.pattern_factory.create_statements("from TAUT import TestCase, TestDoubles")
        for match in match_pattern(self.root.children, import_taut):
            repl = "try:\n    from unittest.mock import patch\nexcept ImportError:\n    from mock import patch\n"
            self.replace(repl, match.nodes, False, False)
        import_doubles = self.pattern_factory.create_statements("from TAUT import TestDoubles")
        for match in match_pattern(self.root.children, import_doubles):
            repl = "try:\n    from unittest.mock import patch\nexcept ImportError:\n    from mock import patch\n"
            self.replace(repl, match.nodes, False, False)

    def convert_tds(self):
        tds = self.pattern_factory.create_statements("self.tds.append(TestDoubles($a, $b=$c))")
        for match in match_pattern(self.root.children, tds):
            repl = f"self.add_patcher({match["$a"]}, '{match["$b"]}', {match["$c"]})"
            self.replace(repl, match.nodes, False, False)

        tds2 = self.pattern_factory.create_statements("self.tds.append(TestDoubles($a=ImprovedStub($b)))")
        for match in match_pattern(self.root.children, tds2):
            repl = f"self.{match["$a"]} = ImprovedStub({match["$b"]})"
            self.replace(repl, match.nodes, False, False)

    def convert_setup_common(self):
        insert_code = """ImprovedStub.ret_vals = {}
ImprovedStub.ret_vals_ex = {}
ImprovedStub.call_logs = {}
ImprovedStub.store_args = {}

"""
        p_start = """for p in self.patchers:
    p.start()
"""
        tds_pattern = self.pattern_factory.create_statements("self.tds = [$$aa]")
        for match in match_pattern(self.root.children, tds_pattern):
            init_stubs = ""
            repl = "self.patchers = [\n"
            doubles_pattern = self.pattern_factory.create_expression("TestDoubles($a=ImprovedStub($b))")
            for matched_doubles in match_pattern(match.expansions["$$aa"], [doubles_pattern]):
                init_stubs += (
                    f'self.{matched_doubles.expansions["$a"][0]} = ImprovedStub({matched_doubles.expansions["$b"][0].signature})\n'
                )
                interface_stub = self.find_import_interface(matched_doubles.expansions["$b"][0].signature)
                repl += f'    patch.object({interface_stub}, \'{matched_doubles.expansions["$a"][0]}\', self.{matched_doubles.expansions["$a"][0]}),\n'
            repl += "]\n\n"
            repl = insert_code + init_stubs + repl + p_start
            self.replace(repl, match.nodes, False, False)

    def convert_teardown_common(self):
        teardown_common = self.pattern_factory.create_statements("def tearDownCommon(self):\n    $$aa")
        repl = """def tearDownCommon(self):
    for p in self.patchers:
        try:
            p.stop()
        except RuntimeError:
            pass
"""
        for match in match_pattern(self.root.children, teardown_common):
            self.replace(repl, match.nodes, False, False)

    def convert_add_patcher(self):
        pattern = self.pattern_factory.create_statements("def tearDownCommon(self):\n    $$aa")
        for match in match_pattern(self.root.children, pattern):
            patcher_pattern = [node for node in self.find_ast_type(FunctionDef) if node.name == "add_patcher"]
            if len(patcher_pattern) == 0:
                self.insert_after(tst_class.insert_add_patcher, match.nodes)

    def find_import_interface(self, name: str):
        interface = name
        if name.islower():
            node_list = [node for node in self.find_ast_type(ImportStatement) if node.name == name]
            if node_list:
                if node_list[0].ast_type == ImportFrom:
                    interface = node_list[0].properties["module"]
                else:
                    interface = node_list[0].name if node_list else name
        return interface.split(".")[0]

    def convert_setup(self):
        # remove doubles init
        pattern1 = self.pattern_factory.create_statements("doubles = []")
        replacement = "self.patches = []"
        for match in match_pattern(self.root.children, pattern1):
            self.replace(replacement, match.nodes, False, False)

        pattern2 = self.pattern_factory.create_statements("self.doubles = []")
        for match in match_pattern(self.root.children, pattern2):
            self.replace(replacement, match.nodes, False, False)

        # convert doubles to patch
        self.convert_test_doubles("doubles.append(TAUT.TestDoubles($a=$b))")
        self.convert_test_doubles("self.doubles.append(TAUT.TestDoubles($a=$b))")

        # convert doubles to patch.object
        insert_node = None
        pattern_outer = self.pattern_factory.create_statements("def setUp(self):\n    $$aa")
        for setup_func in match_pattern(self.root.children, pattern_outer):

            pattern4 = self.pattern_factory.create_statements("doubles.append(TAUT.TestDoubles(module=$mod, $b=$c))")
            matched_pattern = match_pattern(setup_func.nodes, pattern4)
            for index, match in enumerate(matched_pattern):
                repl_pattern = f"self.patches.append(patch.object({match.expansions['$mod'][0].name}, '{match.expansions['$b'][0]}', {match.expansions['$c'][0].signature}))"
                repl_pattern = repl_pattern.replace("context_stub", "self.context_stub")
                self.replace(repl_pattern, match.nodes, False, False)
                if index == len(matched_pattern) - 1:
                    insert_node = match.nodes[-1]
                    insert_code = """\nfor p in self.patches:
    p.start()"""
                    self.insert_after(insert_code, insert_node, False, False)

            pattern4_1 = self.pattern_factory.create_statements("self.doubles.append(TAUT.TestDoubles(module=$mod, $b=$c))")
            matched_pattern_1 = match_pattern(setup_func.nodes, pattern4_1)
            for index, match in enumerate(matched_pattern_1):
                repl_pattern = f"self.patches.append(patch.object({match.expansions['$mod'][0].name}, '{match.expansions['$b'][0]}', {match.expansions['$c'][0].signature}))"
                repl_pattern = repl_pattern.replace("context_stub", "self.context_stub")
                self.replace(repl_pattern, match.nodes, False, False)
                if index == len(matched_pattern_1) - 1:
                    insert_node = match.nodes[-1]
                    insert_code = """\nfor p in self.patches:
    p.start()"""
                    self.insert_after(insert_code, insert_node, False, False)

        pattern5 = self.pattern_factory.create_statements("self.doubles = doubles")
        for match in match_pattern(self.root.children, pattern5):
            self.remove(match.nodes, False, False)
        self.commit()
        [self.replace("self.context_stub", node, False, False) for node in self.find_ast_type(Name) if node.name == "context_stub"]

    def convert_teardown(self):
        matched_pattern = self.pattern_factory.create_statements("def tearDown(self):\n    $$aa")
        repl_pattern = """def tearDown(self):
    for p in self.patches:
        p.stop()"""
        for match in match_pattern(self.root.children, matched_pattern):
            self.replace(repl_pattern, match.nodes, False, False)

    def refactor_teardown(self):
        self.comp = "abcd"
        pattern1 = self.pattern_factory.create_statements("for double in self.doubles:\n    double.exit()")
        replace_pattern = "patch.stopall()"
        for match in match_pattern(self.root.children, pattern1):
            self.replace(replace_pattern, match.nodes, False, False)

        insert_code = f"""{self.comp.upper()}xCONTEXT.{self.comp}xcontext.reset_method_attributes("start_wafer")
{self.comp.upper()}xCONTEXT.{self.comp}xcontext.reset_method_attributes("finish_wafer")
{self.comp.upper()}xCONTEXT.{self.comp}xcontext.reset_method_attributes("start_lot")
{self.comp.upper()}xCONTEXT.{self.comp}xcontext.reset_method_attributes("finish_lot")

"""
        pattern2 = self.pattern_factory.create_statements("self._patch_readout_data_filler.stop()")
        for match in match_pattern(self.root.children, pattern2):
            self.insert_before(insert_code, match.nodes, False, False)

    def convert_test_doubles(self, doubles: str):
        mappings: Dict[str, str] = {
            "emrmxcontext": "EMRMxCONTEXT",
            "acbdxcontext": "ACBDxCONTEXT",
            # Add more mappings here
        }
        doubles_pattern = self.pattern_factory.create_statements(doubles)
        for match in match_pattern(self.root.children, doubles_pattern):
            keyword = match.expansions["$a"][0]
            if match.expansions["$a"][0] in mappings.keys():
                keyword = mappings[match.expansions["$a"][0]]
            repl_pattern = f"self.patches.append(patch('{keyword}.{match.expansions['$a'][0]}', {match.expansions['$b'][0].name}))"
            repl_pattern = repl_pattern.replace("context_stub", "self.context_stub")
            self.replace(repl_pattern, match.nodes, False, False)

    def insert_patch_import(self):
        insert = "\ntry:\n    from unittest.mock import patch\nexcept ImportError:\n    from mock import patch"
        insert_pattern = self.pattern_factory.create_statements(insert)
        if len(match_pattern(self.root.children, insert_pattern)) == 0:
            pattern = self.pattern_factory.create_statements("import unittest\n")
            for match in match_pattern(self.root.children, pattern):
                self.insert_after(insert, match.nodes, False, False)

    def replace_taut_skip(self):
        """
        replace @TAUT.skip_test by @unittest.skip
        """
        [self.replace("@unittest.skip", node) for node in self.find_ast_type(Attribute) if node.name == "TAUT.skip_test"]

    def convert_import_verify(self):
        import_verify = self.pattern_factory.create_statements("self.import_and_verify_module('$a')")
        for match in match_pattern(self.root.children, import_verify):
            repl = f'import {match.expansions["$a"][0]}\nself.assertIsNotNone({match.expansions["$a"][0]})'
            self.replace(repl, match.nodes, False, False)

    def with_testdoubles(self):
        pattern1 = self.pattern_factory.create_statements("with TAUT.TestDoubles(module=$a, $b=$c):\n    $$ee")
        for match in match_pattern(self.root.children, pattern1):
            repl_pattern = f"with patch.object({match["$a"]}, '{match["$b"]}', new={match["$c"]}):\n    {match["$$ee"]}"
            self.replace(repl_pattern, match.nodes, False, False)

    def shared_setup(self):
        setup_function = self.pattern_factory.create_statements("def sharedSetUp(self):\n    $$stmts")
        for match in match_pattern(self.root.children, setup_function):
            repl = match.signature.replace("def sharedSetUp", "    def setUp")
            self.replace(textwrap.dedent(repl), match.nodes, False, False)

    def insert_class(self):
        class_pattern = self.pattern_factory.create_statements("class Asserter(unittest.TestCase):\n    $$aa")
        if len(match_pattern(self.root.children, class_pattern)) == 0:
            insert_pattern = self.pattern_factory.create_statements("def b():\n    $$bb")
            insert_code = tst_insert.insert_code
            for match in match_pattern(self.root.children, insert_pattern):
                self.insert_after(insert_code, match.nodes, False, False)

    def insert_asserter(self):
        insert_pattern = self.pattern_factory.create_statements("def assert_double_equal($$arg, $$other=$$value):\n    $$bb")
        insert_code = tst_insert.insert_code
        for match in match_pattern(self.root.children, insert_pattern):
            self.insert_after(insert_code, match.nodes, False, False)

    def remove_assert_func(self):
        pattern = self.pattern_factory.create_statements("def assert_double_equal($$arg, $$other=$$value):\n    $$bb")
        for match in match_pattern(self.root.children, pattern):
            self.remove(match.nodes, False, False)
            self.commit()

    def replace_unittest_with_asserter(self):
        pattern = self.pattern_factory.create_statements("class $a(TAUT.TestCase):\n    $$bb")
        for match in match_pattern(self.root.children, pattern):
            if not match["$a"] == "Asserter":
                if "assert_raises" in match["$$bb"] or "assert_double_equal" in match["$$bb"]:
                    repl = f"{match.signature.replace("TAUT.TestCase", "Asserter")}"
                    self.replace(repl, match.nodes, False, False)
        self.commit()

    def assert_func(self):
        matching = [
            "assert_raises",
            "assert_double_equal",
        ]
        [self.replace("self." + node.name, node, False, False) for node in self.find_ast_type(Name) if node.name in matching]

    def move_indent(self, indent):
        pattern1 = self.pattern_factory.create_statements("""def $a($$b):
    self.doubles.append(TAUT.TestDoubles($mod, $e, $f))
    $$c""")
        for match in match_pattern(self.root.children, pattern1):
            double_pattern = f"        self.doubles.append(TAUT.TestDoubles({match["$mod"]}, {match["$e"]}, {match["$f"]}))\n"
            func_header_index = match.signature.index("):\n")
            repl = f"""    with patch.object({match["$mod"]}, '{match["$e"]}', {match["$f"]}):\n"""
            replace_pattern = (
                match.signature[: func_header_index + 3] + repl + textwrap.indent(match.signature[func_header_index + 3 :], indent)
            )
            replace_pattern = replace_pattern.replace(double_pattern, "")
            self.replace(replace_pattern, match.nodes, False, False)

    def convert_testdoubles_fun(self):
        """this is used for taut migration, where the function pattern is found in a class"""
        # case1 two TestDoubles are defined
        pattern1 = self.pattern_factory.create_statements("""def $a($$b):
        self.doubles.append(
            TAUT.TestDoubles(
                module=$mod1, $e1=$f1
            )
        )
        self.doubles.append(
            TAUT.TestDoubles(
                module=$mod2, $e2=$f2
            )
        )
        $$c
    """)
        for match in match_pattern(self.root.children, pattern1):
            double_pattern = f"""    self.doubles.append(
        TAUT.TestDoubles(
            module={match["$mod1"]},
            {match["$e1"]}={match["$f1"]},
        )
    )
    self.doubles.append(
        TAUT.TestDoubles(
            module={match["$mod2"]},
            {match["$e2"]}={match["$f2"]},
        )
    )
"""
            func_header_index = match.signature.index("):\n")
            repl = f"""with patch.object({match["$mod1"]}, '{match["$e1"]}', {match["$f1"]}), \\
        patch.object({match["$mod2"]}, '{match["$e2"]}', {match["$f2"]}):\n"""
            replace_pattern = (
                match.signature[: func_header_index + 3] + textwrap.indent(repl, "    ") + match.signature[func_header_index + 3 :]
            )
            replace_pattern = replace_pattern.replace(textwrap.indent(double_pattern, "    "), "")
            self.replace(replace_pattern, match.nodes, False, False)
            self.commit()

        pattern2 = self.pattern_factory.create_statements("""def $a($$b):
        self.doubles.append(
            TAUT.TestDoubles(
                module=$mod, $e=$f
            )
        )
        $$c
    """)
        for match in match_pattern(self.root.children, pattern2):
            double_pattern = f"""    self.doubles.append(
        TAUT.TestDoubles(
            module={match["$mod"]}, {match["$e"]}={match["$f"]}
        )
    )
"""
            double_pattern1 = f"""    self.doubles.append(
        TAUT.TestDoubles(
            module={match["$mod"]},
            {match["$e"]}={match["$f"]},
        )
    )
"""
            func_header_index = match.signature.index("):\n")
            repl = f"""with patch.object({match["$mod"]}, '{match["$e"]}', {match["$f"]}):\n"""
            replace_pattern = (
                match.signature[: func_header_index + 3] + textwrap.indent(repl, "    ") + match.signature[func_header_index + 3 :]
            )
            double_pattern2 = f"    self.doubles.append(TAUT.TestDoubles(module={match['$mod']}, {match['$e']}={match['$f']}))\n"
            replace_pattern = replace_pattern.replace(textwrap.indent(double_pattern, "    "), "")
            replace_pattern = replace_pattern.replace(textwrap.indent(double_pattern1, "    "), "")
            replace_pattern = replace_pattern.replace(textwrap.indent(double_pattern2, "    "), "")
            self.replace(replace_pattern, match.nodes, False, False)
        self.commit()

    def refactor_testdoubles_fun(self):
        """this is used for unittest, where the function pattern is not found in a class"""
        # case1 two TestDoubles are defined
        pattern1 = self.pattern_factory.create_statements("""def $a($$b):
    self.doubles.append(
        TAUT.TestDoubles(
            module=$mod1, $e1=$f1
        )
    )
    self.doubles.append(
        TAUT.TestDoubles(
            module=$mod2, $e2=$f2
        )
    )
    $$c""")
        for match in match_pattern(self.root.children, pattern1):
            double_pattern = f"""    self.doubles.append(
        TAUT.TestDoubles(
            module={match["$mod1"]}, {match["$e1"]}={match["$f1"]}
        )
    )
    self.doubles.append(
        TAUT.TestDoubles(
            module={match["$mod2"]}, {match["$e2"]}={match["$f2"]}
        )
    )
"""
            func_header_index = match.signature.index("):\n")
            repl = f"""with patch.object({match["$mod1"]}, '{match["$e1"]}', {match["$f1"]}), \\
                        patch.object({match["$mod2"]}, '{match["$e2"]}', {match["$f2"]}):
            """
            replace_pattern = match.signature[: func_header_index + 3] + textwrap.indent(
                repl + match.signature[func_header_index + 3 :], "    "
            )
            replace_pattern = replace_pattern.replace(double_pattern, "")
            replace_pattern = replace_pattern.replace(textwrap.indent(double_pattern, "    "), "")
            self.replace(replace_pattern, match.nodes, False, False)
            self.commit()
        pattern2 = self.pattern_factory.create_statements("""def $a($$b):
    self.doubles.append(
        TAUT.TestDoubles(
            module=$mod, $e=$f
        )
    )
    $$c
""")
        for match in match_pattern(self.root.children, pattern2):
            double_pattern = f"""    self.doubles.append(
        TAUT.TestDoubles(
            module={match["$mod"]}, {match["$e"]}={match["$f"]}
        )
    )
"""
            func_header_index = match.signature.index("):\n")
            repl = f"""with patch.object({match["$mod"]}, '{match["$e"]}', {match["$f"]}):\n"""
            replace_pattern = match.signature[: func_header_index + 3] + textwrap.indent(
                repl + match.signature[func_header_index + 3 :], "    "
            )
            replace_pattern = replace_pattern.replace(double_pattern, "")
            replace_pattern = replace_pattern.replace(textwrap.indent(double_pattern, "    "), "")
            self.replace(replace_pattern, match.nodes, False, False)

    def refactor_testdoubles_class(self):
        pattern = self.pattern_factory.create_statements("""class $a(TAUT.TestCase):

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
                double.exit()""")

        for match in match_pattern(self.root.children, pattern):
            replace_pattern = f"""class {match["$a"]}(unittest.TestCase):

    def setUp(self):
{textwrap.indent(match["$$bb"], "        ")}
{textwrap.indent(match["$$cc"], "        ")}
        self.patches = [
            patch.object({match["$mod1"]}, '{match["$e1"]}', {match["$f1"]}),
            patch.object({match["$mod2"]}, '{match["$e2"]}', {match["$f2"]}),
        ]
        for p in self.patches:
            p.start()

{textwrap.indent(match["$$dd"], "        ")}

    def tearDown(self):
{textwrap.indent(match["$$gg"], "        ")}
        for p in self.patches:
            p.stop()"""
            self.replace(replace_pattern, match.nodes, False, False)

    def insert_doc_func(self):
        pattern = self.pattern_factory.create_statements("""# -----------------------------------------------------------------------------#
#                                                                             #
#                   Copyright (c) 2016, XXXX Netherlands B.V.                 #
""")
        insert_code = get_change_comment()
        for match in match_pattern(self.root.children, pattern):
            self.insert_before(insert_code, match.nodes, False, False)


def insert_doc(content: str, date):
    pattern = r"# -+(#)?\n(#\s+#\n)?#\s+Copyright \(c\) \d{4}, XXXX"
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

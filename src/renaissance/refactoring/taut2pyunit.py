from renaissance.utils.refactor_utils import fix_indent, add_indent, is_block_statement

from renaissance.impl.python import PythonASTNode, PythonPatternFactory
from renaissance.syntax_tree import ASTShower, ASTProcessor, MatchFinder, ASTRewriter, ASTFactory

factory = ASTFactory(PythonASTNode, [])
PYUNIT_REPLACEMENT = ''

class TautRefactoring:
    def __init__(self, atu):
        raise  Exception('This class should not be instantiated')

    @staticmethod
    def remove_import_taut(ast_refactor: ASTProcessor) -> None:
        """
        Removes import TAUT
        """
        ast_refactor.find_kind('Import'). \
            filter(lambda node: node.name.find('TAUT') > 0). \
            for_each(lambda node: ast_refactor.remove(node, True, True))

    @staticmethod
    def replace_taut_skip(ast_refactor):
        """
        replace @TAUT.skip_test by @unittest.skip
        """
        ast_refactor.find_kind('Attribute'). \
            filter(lambda node: node.name == 'TAUT.skip_test'). \
            for_each(lambda node: ast_refactor.replace('@unittest.skip', node))

    @staticmethod
    def add_self(ast_refactor):
        """
        replace mock by unittest.mock and using patch
        """
        matching = ['emrwxread', 'emrwxwidxread', 'emrwxviprxinterface', 'whxstream2']
        ast_refactor.find_kind('Name'). \
            filter(lambda node: node.name in matching). \
            for_each(lambda node: ast_refactor.replace('self.' + node.name, node))

    @staticmethod
    def remove_decorator(ast_refactor):
        ast_refactor.find_kind('Attribute'). \
            filter(lambda node: node.name == 'TAUT.log_stub'). \
            for_each(lambda node: ast_refactor.remove(node))

    @staticmethod
    def convert_test_cases(input_code):
        return TautRefactoring.refactor_remove(input_code,'import TAUT')

    @staticmethod
    def replace_taut(input_code):
        """
        replace TAUT.TestCase by unittest.TestCase
        """
        match_pattern = 'class $test_case(TAUT.TestCase):\n    $$aaa'
        replacement = 'class $test_case(unittest.TestCase):\n    $$aaa'
        return TautRefactoring.refactor_replace(input_code, match_pattern, replacement)

    @staticmethod
    def replace_mock_import(input_code):
        """
        replace mock by unittest.mock and using patch
        """
        pattern1 = 'import mock\n'
        result = TautRefactoring.refactor_remove(input_code, pattern1)
        pattern2 = 'from TAUT import TestCase, TestDoubles'
        replacement = 'try:\n    from unittest.mock import patch\nexcept ImportError:\n    from mock import patch\n'
        return TautRefactoring.refactor_replace(result, pattern2, replacement)

    @staticmethod
    def replace_log_emrwxtl(input_code):
        pattern1 = 'with TAUT.TestDoubles(emrwxtl=FakeEMRWxTL(None)):\n    log = TAUT.Logger()\n    $$aa'
        replace_pattern = 'fake_emrwxtl = FakeEMRWxTL(None)\n$$aa'
        result = TautRefactoring.refactor_replace(input_code, pattern1, replace_pattern)
        formatted_code = fix_indent(result)

        pattern2 = 'emrwxtl.$a($$bb)'
        result2 = TautRefactoring.refactor_replace(formatted_code, pattern2, 'fake_emrwxtl.$a($$bb)')

        pattern3 = '$c = emrwxtl.$a($$bb)'
        return TautRefactoring.refactor_replace(result2, pattern3, '$c = fake_emrwxtl.$a($$bb)')

    @staticmethod
    def insert_class(input_code, insert_code):
        insert_pattern = 'def b():\n    $$bb'
        return TautRefactoring.refactor_insert_after(input_code, insert_code, insert_pattern)

    @staticmethod
    def refactor_teardown(input_code):
        pattern1 = 'for double in self.doubles:\n    double.exit()'
        replace_pattern = 'patch.stopall()'
        result = TautRefactoring.refactor_replace(input_code, pattern1, replace_pattern)

        insert_code = """EMRWxCONTEXT.emrmxcontext.reset_method_attributes("start_wafer")
EMRWxCONTEXT.emrmxcontext.reset_method_attributes("finish_wafer")
EMRWxCONTEXT.emrmxcontext.reset_method_attributes("start_lot")
EMRWxCONTEXT.emrmxcontext.reset_method_attributes("finish_lot")
"""
        pattern2 = 'self._patch_readout_data_filler.stop()'
        return TautRefactoring.refactor_insert_before(result, insert_code, pattern2)

    @staticmethod
    def refactor_setup(input_code):
        #add self. at front of interface EMRMxCONTEXT
        pattern1 = 'context_stub = $c'
        replace_pattern = 'self.context_stub = $c'
        result = TautRefactoring.refactor_replace(input_code, pattern1, replace_pattern)

        pattern2 = """self.doubles.append(
    TAUT.TestDoubles(module=EMRMxAPxData.data.rep, context=context_stub)
)"""
        replace_pattern2 = """self.patches.append(patch.object(EMRMxAPxData.data.rep, 'context', self.context_stub))"""
        result2 = TautRefactoring.refactor_replace(result, pattern2, replace_pattern2)
        # should able to replace all context_stub with self.context_stub

        # remove self.doubles
        pattern2 = 'self.doubles = $aa'
        result3 = TautRefactoring.refactor_remove(result2, pattern2)

        # insert self.patches
        insert_code = 'self.patches = []'
        pattern3 = 'self.context_stub = EMRMxCONTEXT.EMRMxCONTEXTStub()'
        result4 = TautRefactoring.refactor_insert_after(result3, insert_code, pattern3)

        # replace doubles with patches
        pattern4 = """self.doubles.append(TAUT.TestDoubles(emrmxcontext=context_stub))"""
        replace_pattern2 = """self.patches.append(patch('EMRMxCONTEXT.emrmxcontext', self.context_stub))"""
        result5 = TautRefactoring.refactor_replace(result4, pattern4, replace_pattern2)
        pattern5 = """self.doubles.append(
                TAUT.TestDoubles(
                    module=$mod, $e=$f
                )
            )
        """
        replace_pattern3 = """self.patches.append(patch.object($mod, '$e', $f))"""
        result6 = TautRefactoring.refactor_replace(result5, pattern5, replace_pattern3)

        insert_code = """for p in self.patches:
    p.start()
"""
        pattern6 = 'EMRMxAPxData.data.adv_wp = EMRMxADVxWP.input()'
        return TautRefactoring.refactor_insert_before(result6, insert_code, pattern6)

    @staticmethod
    def refactor_testdoubles_fun(input_code):
        """refactor cannot use standard replace method, because it needs to fix the indentation"""
        atu = factory.create_from_text(input_code, 'temp.py')
        rewriter = ASTRewriter(atu)
        pattern_factory = PythonPatternFactory(factory, atu)
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
        match_pattern = pattern_factory.create_python_pattern(pattern1)
        test_cases = MatchFinder.find_all([atu], [match_pattern]).to_iterable()
        for test_case in test_cases:
            replacement = replace_pattern
            for snippets in test_case.expansions:
                if snippets == '$$c':
                    replacement = replacement.replace(snippets, add_indent(TautRefactoring.raw(test_case.expansions[snippets], snippets)))
                else:
                    replacement = replacement.replace(snippets,
                                                      TautRefactoring.raw(test_case.expansions[snippets], snippets))
            rewriter.replace(replacement, test_case.nodes)
        rewriter.apply()
        return rewriter.apply_to_string()

    @staticmethod
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
        return TautRefactoring.refactor_replace(input_code, match_pattern, replace_pattern)

    @classmethod
    def refactor_replace(self, input_code: str, before: str, after: str):
        atu = factory.create_from_text(input_code, 'temp.py')
        rewriter = ASTRewriter(atu)
        pattern_factory = PythonPatternFactory(factory, atu)
        before_pattern = pattern_factory.create_python_pattern(before)

        test_cases = MatchFinder.find_all([atu], [before_pattern]).to_iterable()
        for test_case in test_cases:
            replacement = after
            for snippets in test_case.expansions:
                # by replacing if, try, with statements move the body to left
                if is_block_statement(before_pattern):
                    pass
                else:
                    replacement = replacement.replace(snippets, TautRefactoring.raw(test_case.expansions[snippets], snippets))
            rewriter.replace(replacement, test_case.nodes)
        rewriter.apply()
        return rewriter.apply_to_string()

    @classmethod
    def refactor_remove(self, input_code: str, match_str: str):
        atu = factory.create_from_text(input_code, 'temp.py')
        rewriter = ASTRewriter(atu)
        pattern_factory = PythonPatternFactory(factory, atu)
        match_pattern = pattern_factory.create_python_pattern(match_str)

        matched = MatchFinder.find_all([atu], [match_pattern]).to_iterable()
        for ma in matched:
            rewriter.remove(ma.nodes)
        rewriter.apply()
        return rewriter.apply_to_string()

    @classmethod
    def refactor_insert_after(self, input_code: str, insert_code: str, match_str: str):
        atu = factory.create_from_text(input_code, 'temp.py')
        rewriter = ASTRewriter(atu)
        pattern_factory = PythonPatternFactory(factory, atu)
        match_pattern = pattern_factory.create_python_pattern(match_str)

        matched = MatchFinder.find_all([atu], [match_pattern]).to_iterable()[0]
        rewriter.insert_after(insert_code, matched.nodes)
        rewriter.apply()
        return rewriter.apply_to_string()

    @classmethod
    def refactor_insert_before(self, input_code: str, insert_code: str, match_str: str):
        atu = factory.create_from_text(input_code, 'temp.py')
        rewriter = ASTRewriter(atu)
        pattern_factory = PythonPatternFactory(factory, atu)
        match_pattern = pattern_factory.create_python_pattern(match_str)

        matched = MatchFinder.find_all([atu], [match_pattern]).to_iterable()[0]
        rewriter.insert_before(insert_code, matched.nodes)
        rewriter.apply()
        return rewriter.apply_to_string()

    @classmethod
    def raw(self, nodes, snippets) -> str:
        res = ''
        start_offset = 0
        end_offset = 0
        if '$$' in snippets:
            for node in nodes:
                if isinstance(node, PythonASTNode):
                    if start_offset == 0 or node.offset < start_offset:
                        start_offset = node.offset
                    if end_offset == 0 or node.end_offset > end_offset:
                        end_offset = node.end_offset
            return node.root.content(start_offset, end_offset)
        else:
            for node in nodes:
                if isinstance(node, PythonASTNode):
                    match node.kind:
                        case 'Pass':
                            res += 'pass'
                        case _:
                            res += node.signature
                else:
                    res += str(node)
        return res  # + '\n'

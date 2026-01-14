import ast
import unittest
from _ast import AST
from typing import Sequence

from impl import PythonASTNode, PythonPatternFactory
from impl.python import match_pattern, find_all, match
from syntax_tree import ASTFactory, MatchFinder, ASTShower
def dump(
    node, annotate_fields=True, include_attributes=False,
    *,
    indent=None, show_empty=False,
):
    """
    Return a formatted dump of the tree in node.  This is mainly useful for
    debugging purposes.  If annotate_fields is true (by default),
    the returned string will show the names and the values for fields.
    If annotate_fields is false, the result string will be more compact by
    omitting unambiguous field names.  Attributes such as line
    numbers and column offsets are not dumped by default.  If this is wanted,
    include_attributes can be set to true.  If indent is a non-negative
    integer or string, then the tree will be pretty-printed with that indent
    level. None (the default) selects the single line representation.
    If show_empty is False, then empty lists and fields that are None
    will be omitted from the output for better readability.
    """
def _format(node, level=0):
    prefix = ''
    sep = ', '
    annotate_fields =False
    show_empty=False
    include_attributes=[]
    if isinstance(node, AST):
        cls = type(node)
        args = []
        args_buffer = []
        allsimple = True
        keywords = annotate_fields
        for name in node._fields:
            try:
                value = getattr(node, name)
            except AttributeError:
                keywords = True
                continue
            if value is None and getattr(cls, name, ...) is None:
                keywords = True
                continue
            if not show_empty:
                if value == []:
                    field_type = cls._field_types.get(name, object)
                    if getattr(field_type, '__origin__', ...) is list:
                        if not keywords:
                            args_buffer.append(repr(value))
                        continue
                if not keywords:
                    args.extend(args_buffer)
                    args_buffer = []
            value, simple = _format(value, level)
            allsimple = allsimple and simple
            if keywords:
                args.append('%s=%s' % (name, value))
            else:
                args.append(value)
        if include_attributes and node._attributes:
            for name in node._attributes:
                try:
                    value = getattr(node, name)
                except AttributeError:
                    continue
                if value is None and getattr(cls, name, ...) is None:
                    continue
                value, simple = _format(value, level)
                allsimple = allsimple and simple
                args.append('%s=%s' % (name, value))
        if allsimple and len(args) <= 3:
            return '%s(%s)' % (node.__class__.__name__, ', '.join(args)), not args
        return '%s(%s%s)' % (node.__class__.__name__, prefix, sep.join(args)), False
    elif isinstance(node, list):
        if not node:
            return '[]', True
        return '[%s%s]' % (prefix, sep.join(_format(x, level)[0] for x in node)), False
    return repr(node), True



class PythonShowerTest(unittest.TestCase):
    def test_not_equal_nodes(self):
        factory = ASTFactory(PythonASTNode, [])
        atu = factory.create_from_text('ba(55)\nca(555)\nlo(4444)\nna=55', 'test.py')
        # create a pattern factory atu is passed to the pattern factory for use of all # includes, #defines and declarations
        pattern_factory = PythonPatternFactory(factory, atu)
        simple = pattern_factory.create('$pa($55)')
        print(_format(simple.node))
        text = ASTShower.get_node(simple)
        text2 = ast.dump(simple.node)
        self.assertEqual(text2,text)

if __name__ == '__main__':
    unittest.main()

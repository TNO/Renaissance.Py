import ast
from _ast import Call

from common import Stream

from .python_ast_node import PythonASTNode, MATCH_ONE, MATCH_ALL
from .python_codebase import PythonCodebase
from .python_pattern_factory import PythonPatternFactory

__all__ = [
    'PythonASTNode',
    'PythonCodebase',
    'PythonPatternFactory'
]
#
# def match(node, other):
#     # def is_match_one(node, other):
#     if (type(other) == ast.Name and other.id.startswith(MATCH_ONE)):
#         if not other in expansion:
#             expansion[other] = node
#             return True
#         else:
#             other = expansion[other]
#     match type(node):
#         # case Add(__ast.operator):
#         # case And(__ast.boolop):
#         # case AnnAssign(__ast.stmt):
#         # case Assert(__ast.stmt):
#         # case ast.Assign:
#         # case AsyncFor(__ast.stmt):
#         # case AsyncFunctionDef(__ast.stmt):
#         # case AsyncWith(__ast.stmt):
#         # case Attribute(__ast.expr):
#         # case AugAssign(__ast.stmt):
#         # case Await(__ast.expr):
#         # case BinOp(__ast.expr):
#         # case ast.BitAnd:
#         # case BitOr(__ast.operator):
#         # case BitXor(__ast.operator):
#         # case BoolOp(__ast.expr):
#         # case Break(__ast.stmt):
#         case ast.Call:
#             return isinstance(other, type(node)) and match_call(node, other)
#         # case ClassDef(__ast.stmt):
#         # case ast.Compare:
#         #     pass
#         case ast.Constant:
#             return isinstance(other, type(node)) and match(node.value, other.value)
#         # case Continue(__ast.stmt):
#         # case Del(__ast.expr_context):
#         # case Delete(__ast.stmt):
#         # case Dict(__ast.expr):
#         # case DictComp(__ast.expr):
#         # case Div(__ast.operator):
#         # case Eq(__ast.cmpop):
#         # case ExceptHandler(__ast.excepthandler):
#         case ast.Expr:
#             return isinstance(other, type(node)) and match(node.value, other.value)
#         # case Expression(__ast.mod):
#         # case FloorDiv(__ast.operator):
#         # case For(__ast.stmt):
#         # case FormattedValue(__ast.expr):
#         # case FunctionDef(__ast.stmt):
#         # case FunctionType(__ast.mod):
#         # case GeneratorExp(__ast.expr):
#         # case Global(__ast.stmt):
#         # case Gt(__ast.cmpop):
#         # case GtE(__ast.cmpop):
#         case ast.If:
#             return match_if(node, other)
#         # case IfExp(__ast.expr):
#         # case Import(__ast.stmt):
#         # case ImportFrom(__ast.stmt):
#         # case In(__ast.cmpop):
#         # case Interactive(__ast.mod):
#         # case Invert(__ast.unaryop):
#         # case Is(__ast.cmpop):
#         # case IsNot(__ast.cmpop):
#         # case JoinedStr(__ast.expr):
#         # case LShift(__ast.operator):
#         # case Lambda(__ast.expr):
#         # case List(__ast.expr):
#         # case ListComp(__ast.expr):
#         # case Load(__ast.expr_context):
#         # case Lt(__ast.cmpop):
#         # case LtE(__ast.cmpop):
#         # case MatMult(__ast.operator):
#         # case Match(__ast.stmt):
#         # case MatchAs(__ast.pattern):
#         # case MatchClass(__ast.pattern):
#         # case MatchMapping(__ast.pattern):
#         # case MatchOr(__ast.pattern):
#         # case MatchSequence(__ast.pattern):
#         # case MatchSingleton(__ast.pattern):
#         # case MatchStar(__ast.pattern):
#         # case MatchValue(__ast.pattern):
#         # case Mod(__ast.operator):
#         # case Module(__ast.mod):
#         # case Mult(__ast.operator):
#         case ast.Name:
#             return isinstance(other, type(node)) and match(node.id, other.id)
#         # case NamedExpr(__ast.expr):
#         # case Nonlocal(__ast.stmt):
#         # case Not(__ast.unaryop):
#         # case NotEq(__ast.cmpop):
#         # case NotIn(__ast.cmpop):
#         # case Or(__ast.boolop):
#         # case ParamSpec(__ast.type_param):
#         # case Pass(__ast.stmt):
#         # case Pow(__ast.operator):
#         # case RShift(__ast.operator):
#         # case Raise(__ast.stmt):
#         # case Return(__ast.stmt):
#         # case Set(__ast.expr):
#         # case SetComp(__ast.expr):
#         # case Slice(__ast.expr):
#         # case Starred(__ast.expr):
#         # case Store(__ast.expr_context):
#         # case Sub(__ast.operator):
#         # case Subscript(__ast.expr):
#         # case Try(__ast.stmt):
#         # case TryStar(__ast.stmt):
#         # case Tuple(__ast.expr):
#         # case TypeAlias(__ast.stmt):
#         # case TypeIgnore(__ast.type_ignore):
#         # case TypeVar(__ast.type_param):
#         # case TypeVarTuple(__ast.type_param):
#         # case UAdd(__ast.unaryop):
#         # case USub(__ast.unaryop):
#         # case UnaryOp(__ast.expr):
#         # case While(__ast.stmt):
#         # case With(__ast.stmt):
#         # case Yield(__ast.expr):
#         # case YieldFrom(__ast.expr):
#         case _:
#             # str or int
#             return node == other
#         # compare type if not arguments, compare the same type
#

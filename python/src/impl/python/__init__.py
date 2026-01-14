import ast
from _ast import Call

from common import Stream

from .python_ast_node import PythonASTNode
from .python_codebase import PythonCodebase
from .python_pattern_factory import PythonPatternFactory, MATCH_ALL, MATCH_ONE

__all__ = [
    'PythonASTNode',
    'PythonCodebase',
    'PythonPatternFactory'
]


def find_all(atu, pattern):
    return Stream(match_pattern(atu.get_children(), pattern))


ANY_ID = "\\$\\w+(\\(\\$\\))?";
STRING_ANY = "\"\\$\\w+\"";
DONT_CARE = "$$"
WILDLIST = "[$$"
expandArgList = {}
expansionList = {}
expansion = {}
foundStatements = []


def match_pattern(statements, pattern):
    resetExpansions()

    find_matching_pattern(statements, pattern)
    return foundStatements


def find_matching_pattern(statements, pattern):
    greedy = False
    foundPosition = 0
    foundPositionInExpandedList=0
    for i in range(len(statements)):
        node = statements[i]
        current_name = pattern[foundPosition].get_name()
        if current_name.startswith(MATCH_ALL):
            if foundPosition==0:
                start=i
            if current_name in expansionList:
                if match(expansionList[current_name][foundPositionInExpandedList], node.node):
                    foundPositionInExpandedList = foundPositionInExpandedList + 1
                else:
                    foundPosition = 0
            else:
                foundPosition = foundPosition + 1
                foundPositionInExpandedList = 0
                expansion_start = i
                greedy = True
        elif match(node.node, pattern[foundPosition].node):
            if foundPosition==0:
                start=i
            if greedy == True:
                greedy = False
                last_name = pattern[foundPosition-1].get_name()
                if not last_name in expansionList:
                    expansionList[last_name] = statements[expansion_start:i+1]
                    foundPositionInExpandedList=0
            foundPosition = foundPosition + 1

        elif node.get_children():
            find_matching_pattern(node.get_children(), pattern)

        if foundPosition == len(pattern):
            end = i + 1
            foundStatements.append(statements[start:end])
            foundPosition = 0





def is_match_any(nodes, other, greedy):
    if greedy:
        if other in expansionList:
            return safeSubtreeListMatch(nodes, expansionList[other])
        else:
            expansionList[other] = nodes
            return True
    else:
        return True


def isWildCardString(node, other):
    code = other.get_name()
    if code.matches(STRING_ANY):
        if not code in expansion:
            expansion.put(code, node)
        return True
    else:
        return False


def resetExpansions():
    expansion.clear()
    expansionList.clear()
    foundStatements.clear()


def match_stmt(node, other):
    return False


def match_if(node: ast.If, other):
    if not isinstance(other, ast.If):
        return False
    if match(node.test, other.test) and match(node.body, other.body) and match(node.orelse, other.orelse):
        return True


def match_call(node: Call, other):
    if isinstance(other, ast.Expr):
        other = other.value
    if not isinstance(other, Call):
        return False
    if match(node.func, other.func):
        for i in range(len(node.args)):
            if not match(node.args[i], other.args[i]):
                return False
        return True
    # found = False;
    # if (other instanceof MethodInvocation o & & safeSubtreeListMatch(node.typeArguments(), o.typeArguments())) :
    #     found = safeSubtreeMatch(node.getExpression(), o.getExpression()) & & safeSubtreeMatch(node.getName(), o.getName()) & &
    #     (isWildArgList(node.arguments(), o.arguments()));
    #
    #
    # if (!found) {
    # found = isWildCard(node, other);
    # return found;


def subtree_match(node, other):
    if (isinstance(other, type(node))
            and (node.get_name() == other.get_name()) and eq_children(node, other.get_children())):
        return True
    if other.get_name().startswith(MATCH_ONE):
        return False


def eq_children(self, children):
    size = len(self.get_children())
    if size != len(children):
        return False
    for index in range(size):
        if not match(self._children[index], children[index]):
            return False
    return True


def match(node, other):
    # def is_match_one(node, other):
    if (type(other) == ast.Name and other.id.startswith(MATCH_ONE)):
        if not other in expansion:
            expansion[other] = node
            return True
        else:
            other = expansion[other]
    match type(node):
        # case Add(__ast.operator):
        # case And(__ast.boolop):
        # case AnnAssign(__ast.stmt):
        # case Assert(__ast.stmt):
        case ast.Assign:
            return match_stmt(node, other)
        # case AsyncFor(__ast.stmt):
        # case AsyncFunctionDef(__ast.stmt):
        # case AsyncWith(__ast.stmt):
        # case Attribute(__ast.expr):
        # case AugAssign(__ast.stmt):
        # case Await(__ast.expr):
        # case BinOp(__ast.expr):
        # case ast.BitAnd:
        # case BitOr(__ast.operator):
        # case BitXor(__ast.operator):
        # case BoolOp(__ast.expr):
        # case Break(__ast.stmt):
        case ast.Call:
            return match_call(node, other)
        # case ClassDef(__ast.stmt):
        case ast.Compare:
            pass
        case ast.Constant:
            return match(node.value, other.value)
        # case Continue(__ast.stmt):
        # case Del(__ast.expr_context):
        # case Delete(__ast.stmt):
        # case Dict(__ast.expr):
        # case DictComp(__ast.expr):
        # case Div(__ast.operator):
        # case Eq(__ast.cmpop):
        # case ExceptHandler(__ast.excepthandler):
        case ast.Expr:
            return match(node.value, other.value)
        # case Expression(__ast.mod):
        # case FloorDiv(__ast.operator):
        # case For(__ast.stmt):
        # case FormattedValue(__ast.expr):
        # case FunctionDef(__ast.stmt):
        # case FunctionType(__ast.mod):
        # case GeneratorExp(__ast.expr):
        # case Global(__ast.stmt):
        # case Gt(__ast.cmpop):
        # case GtE(__ast.cmpop):
        case ast.If:
            match_if(node, other)
        # case IfExp(__ast.expr):
        # case Import(__ast.stmt):
        # case ImportFrom(__ast.stmt):
        # case In(__ast.cmpop):
        # case Interactive(__ast.mod):
        # case Invert(__ast.unaryop):
        # case Is(__ast.cmpop):
        # case IsNot(__ast.cmpop):
        # case JoinedStr(__ast.expr):
        # case LShift(__ast.operator):
        # case Lambda(__ast.expr):
        # case List(__ast.expr):
        # case ListComp(__ast.expr):
        # case Load(__ast.expr_context):
        # case Lt(__ast.cmpop):
        # case LtE(__ast.cmpop):
        # case MatMult(__ast.operator):
        # case Match(__ast.stmt):
        # case MatchAs(__ast.pattern):
        # case MatchClass(__ast.pattern):
        # case MatchMapping(__ast.pattern):
        # case MatchOr(__ast.pattern):
        # case MatchSequence(__ast.pattern):
        # case MatchSingleton(__ast.pattern):
        # case MatchStar(__ast.pattern):
        # case MatchValue(__ast.pattern):
        # case Mod(__ast.operator):
        # case Module(__ast.mod):
        # case Mult(__ast.operator):
        case ast.Name:
            return match(node.id, other.id)
        # case NamedExpr(__ast.expr):
        # case Nonlocal(__ast.stmt):
        # case Not(__ast.unaryop):
        # case NotEq(__ast.cmpop):
        # case NotIn(__ast.cmpop):
        # case Or(__ast.boolop):
        # case ParamSpec(__ast.type_param):
        # case Pass(__ast.stmt):
        # case Pow(__ast.operator):
        # case RShift(__ast.operator):
        # case Raise(__ast.stmt):
        # case Return(__ast.stmt):
        # case Set(__ast.expr):
        # case SetComp(__ast.expr):
        # case Slice(__ast.expr):
        # case Starred(__ast.expr):
        # case Store(__ast.expr_context):
        # case Sub(__ast.operator):
        # case Subscript(__ast.expr):
        # case Try(__ast.stmt):
        # case TryStar(__ast.stmt):
        # case Tuple(__ast.expr):
        # case TypeAlias(__ast.stmt):
        # case TypeIgnore(__ast.type_ignore):
        # case TypeVar(__ast.type_param):
        # case TypeVarTuple(__ast.type_param):
        # case UAdd(__ast.unaryop):
        # case USub(__ast.unaryop):
        # case UnaryOp(__ast.expr):
        # case While(__ast.stmt):
        # case With(__ast.stmt):
        # case Yield(__ast.expr):
        # case YieldFrom(__ast.expr):
        case _:
            return node == other
        # compare type if not arguments, compare the same type


#
#

#
# def match(StringLiteral,other) {
#     return isWildCard(node, other) | | isWildCardString(node, other) | | super.match(node, other);
#
# def match(WhileStatement,other) :
#     if (other instanceof WhileStatement o) :
#         return safeSubtreeMatch(node.getExpression(), o.getExpression()) & & safeSubtreeMatch(node.getBody(), o.getBody());
#     return false;
#

def subtreeMatch(node, param):
    return True


def isWildList(param, cursor, greedy):
    pass


def safeSubtreeListMatch(nodes, param):
    pass

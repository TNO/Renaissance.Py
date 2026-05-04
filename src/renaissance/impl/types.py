from abc import ABC
from xmlrpc.client import Boolean

from libcst import In


class Type(ABC):
    pass
    def __str__(self):
        self.__class__.__name__
class UnknownKind:
    pass

class Node(Type):
    pass

class Literal(Type):
    pass

class TranslationUnit(Node):
    pass

class Statement(Node):
    pass


class BodiedStatement(Statement):
    pass

class For(Statement):
    pass
class FunctionDef(Statement):
    pass
class With(Statement):
    pass

class Assign(Statement):
    pass
class Assert(Statement):
    pass
class AugAssign(Statement):
    pass
class Break(Statement):
    pass
class ClassDef(Statement):
    pass
class Continue(Statement):
    pass
class Expr(Statement):
    pass
class FunctionDef(Statement):
    pass
class If(Statement):
    pass
class Import(Statement):
    pass
class ImportFrom(Statement):
    pass
class Match(Statement):
    pass
class Pass(Statement):
    pass
class Raise(Statement):
    pass
class Return(Statement):
    pass
class Try(Statement):
    pass
class While(Statement):
    pass
class Do(Statement):
    pass
class With(Statement):
    pass

class Expression(Node):
    pass

class IfExp(Expression):
    pass

class IfExp(Expression):
    pass

class Call(Expression):
    pass

class Dict(Expression):
    pass

class Set(Expression):
    pass

class List(Expression):
    pass

class DictComp(Expression):
    pass

class ListComp(Expression):
    pass

class SetComp(Expression):
    pass

class Lambda(Expression):
    pass
class Tuple(Expression):
    pass


class GeneratorExp(Expression):
    pass

class Operator(Node):
    pass

class Subscript(Operator):
    pass
class UnaryOperation(Operator):
    pass
class Yield(Operator):
    pass
class Subscript(Operator):
    pass

class BitInvertOperator(UnaryOperation):
    pass
class NotOperator(UnaryOperation):
    pass
class PlusOperator(UnaryOperation):
    pass
class MinusOperator(UnaryOperation):
    pass
class BitOperator(UnaryOperation):
    pass

class Name(Literal):
    pass

class Constant(Literal):
    pass

class Number(Literal):
    pass

class String(Literal):
    pass

class FormattedString(Literal):
    pass

class ImplicitNode(Node):
    pass

class Argument(Node):
    pass

class Pattern(Type):
    pass
class MatchOne(Pattern):
    pass

class MatchAll(Pattern):
    pass

class Declaration(Statement):
    pass

class DeclarationExpression(Expression):
    pass
class TypeReference(Expression):
    pass

class VariableDeclaration(Declaration):
    pass
class FunctionDeclaration(Declaration):
    pass
class ClassDeclaration(Declaration):
    pass


class CompoundStatement(Statement):
    pass


class ParenthesizedExpression(Expression):
    pass


class Constructor(FunctionDef):
    pass


class FieldDeclaration(Declaration):
    pass


class MacroDefinition:
    pass


class Namespace:
    pass


class ParameterDeclaration(Declaration):
    pass


class StructDeclaration(Declaration):
    pass


class TypedefDeclaration(Declaration):
    pass


class Specifier(Node):
    pass


class BaseSpecifier(Specifier):
    pass


class Attribute(Literal):
    pass


class ConstructorExpression(Call):
    pass



class Definition(CompoundStatement):
    pass


class RecordDef(Definition):
    pass


class BinaryOperation(Operator):
    pass


class Cast(Node):
    pass



class BuiltinType(Literal):
    pass


class AccessSpecifier(Specifier):
    pass


class DeclarationLoc(Declaration):
    pass


class Await(Expression):
    pass


class Delete(Expression):
    pass


class AssignTarget(Expression):
    pass


class Global(Statement):
    pass


class Typedef(Declaration):
    pass


class Slice(Literal):
    pass


class NamedExpr(Expression):
    pass


class Starred(Literal):
    pass


class Catch(Statement):
    pass


class ComparasionOperation(Expression):
    pass


class Equal(ComparasionOperation):
    pass
class NotEqual(ComparasionOperation):
    pass
class In(ComparasionOperation):
    pass

class NotIn(ComparasionOperation):
    pass

class Is(ComparasionOperation):
    pass

class IsNot(ComparasionOperation):
    pass

class GreaterEqual(ComparasionOperation):
    pass
class Greater(ComparasionOperation):
    pass
class LessThanEqual(ComparasionOperation):
    pass
class LessThan(ComparasionOperation):
    pass


class BitAnd(Operator):
    pass


class BitOr(Operator):
    pass


class BitXor(Operator):
    pass


class BooleanOperation(Operator):
    pass


class UnaryAdd(UnaryOperation):
    pass
class UnarySubtract(UnaryOperation):
    pass
class Invert(UnaryOperation):
    pass
class Modulo(BinaryOperation):
    pass
class Divide(BinaryOperation):
    pass
class FloorDiv(BinaryOperation):
    pass
class LShift(BinaryOperation):
    pass
class RShift(BinaryOperation):
    pass
class Mult(BinaryOperation):
    pass
class Pow(BinaryOperation):
    pass
class Add(BinaryOperation):
    pass
class Subtract(BinaryOperation):
    pass


class Case(Statement):
    pass


class MatchStar(Node):
    pass

class MatchAs(Node):
    pass


class MatchSingleton(Node):
    pass


class MatchOr(Node):
    pass


class MatchClass(Node):
    pass


class MatchValue(Node):
    pass


class MatchMapping(Node):
    pass


class MatchSequence(Node):
    pass


class Nonlocal(Node):
    pass



OPERATOR_MAP = {
    "AnnAssign": "=",
    "Assert": "assert",
    "Assign": "=",
    "AsyncFor": "for",
    "AsyncFunctionDef": "function",
    "AsyncWith": "with",
    "AugAssignAdd": "+=",
    "Break": "break",
    "Call": "def",
    "ClassDef": "class",
    "Continue": "continue",
    "For": "for",
    "FunctionDef": "function",
    "If": "if",
    "Import": "import",
    "ImportFrom": "import",
    "Match": "match",
    "Pass": "pass",
    "Try": "try",
    "TryStar": "try",
    "While": "while",
    "With": "with",

}


class ArgumentList:
    pass


class Compare:
    pass


class Keyword:
    pass


class Arguments:
    pass


KIND_MAP ={
    "AnnAssign": Assign,
    "Assert": Assert,
    "Assign": Assign,
    "AssignTarget": AssignTarget,
    "AsyncFor":For,
    "arg": Argument,
    "arguments": Arguments,
    "Attributr": Attribute,
    "AsyncFunctionDef": FunctionDef,
    "AsyncWith": With,
    "AugAssign": AugAssign,
    "Await": Await,
    "Break": Break,
    "BitInvert": BitInvertOperator,
    "Call": Call,
    "ClassDef": ClassDef,
    "Continue": Continue,
    "Constant": Literal,
    "Dict": Dict,
    "DictComp": DictComp,
    "Delete": Delete,
    "Del": Delete,
    "Expr": Expr,
    "Eq": Equal,
    "ExceptHandler": Catch,
    "For": For,
    "FormattedString": FormattedString,
    "FunctionDef": FunctionDef,
    "Global": Global,
    "GeneratorExp": GeneratorExp,
    "If": If,
    "IfExp": IfExp,
    "In": In,
    "NotIn": NotIn,
    "NotEq": NotEqual,
    "Is": Is,
    "IsNot":IsNot,
    "Lt": LessThan,
    "LtE": LessThanEqual,
    "Gt": Greater,
    "GtE": GreaterEqual,

    "BinOp": BinaryOperation,
    "BinaryOperation": BinaryOperation,
    "BitAnd": BitAnd,
    "BitOr": BitOr,
    "BitXor": BitXor,
    "BoolOp": BooleanOperation,
    "UAdd": UnaryAdd,
    "USub": UnarySubtract,
    "Invert": Invert,


    "Mod": Modulo,
    "Div": Divide,
    "FloorDiv": FloorDiv,
    "LShift": LShift,
    "RShift": RShift,
    "Mult": Mult,
    "Pow": Pow,
    "Sub": Subtract,
    "Add": Add,
    "Compare" : Compare,
    "FormattedValue": FormattedString,
    "Import": Import,
    "ImportFrom": ImportFrom,
    "ImplicitNode": ImplicitNode,
    "JoinedStr": FormattedString,
    "Lambda": Lambda,
    "keyword": Keyword,
    "List": List,
    "ListComp": ListComp,
    "Match": Match,
    "MatchStar": MatchStar,
    "MatchAs": MatchAs,
    "MatchSingleton": MatchSingleton,
    "MatchOr": MatchOr,
    "MatchClass": MatchClass,
    "MatchValue": MatchValue,
    "MatchMapping": MatchMapping,
    "MatchSequence": MatchSequence,

    "Minus": MinusOperator,
    "Module": TranslationUnit,
    "match_case": Case,
    "Not": NotOperator,
    "Nonlocal": Nonlocal,
    "Name": Name,
    "NamedExpr": NamedExpr,
    "Pass": Pass,
    "Plus": PlusOperator,
    "Raise": Raise,
    "Return": Return,
    "Set": Set,
    "SetComp": SetComp,
    "Slice": Slice,
    "Starred": Starred,
    "Subscript": Subscript,
    "Try": Try,
    "TryStar": Try,
    "Tuple": Tuple,
    "TypeAlias": Typedef,
    "UnaryOp": UnaryOperation,
    "UnaryOperation": UnaryOperation,
    "While": While,
    "With": With,
    "Yield": Yield,
    "YieldFrom": Yield,

    "&": BitAnd,
    "|": BitOr,
    "^": BitXor,
    "assert_statement": Assert,
    "assignment":Assign,
    "arg": Argument,
    "augmented_assignment": AugAssign,
    "argument_list": ArgumentList,
    "await": Await,
    "binary_operator": BinaryOperation,
    "boolean_operator": BooleanOperation,
    "break_statement":Break,
    "call": Call,
    "class_definition":ClassDef,
    "conditional_expression": IfExp,
    "continue_statement": Continue,
    "dictionary": Dict,
    "dictionary_comprehension": DictComp,
    "del": Delete,
    "expression_statement": Expr,
    "for_statement":For,
    "function_definition": FunctionDef,
    "generator_expression": GeneratorExp,
    "identifier": Name,
    "if_statement": If,
    "import_from_statement": ImportFrom,
    "import_statement": Import,
    "integer": Number,
    "lambda": Lambda,
    "list": List,
    "list_comprehension": ListComp,
    "match_statement": Match,
    "module": TranslationUnit,
    "not_operator": UnaryOperation,
    "nonlocal_statement": Nonlocal,
    "pass_statement": Pass,
    "parenthesized_expression": ParenthesizedExpression,
    "raise_statement": Raise,
    "return_statement": Return,
    "set": Set,
    "set_comprehension": SetComp,
    "subscript": Subscript,
    "try_statement": Try,
    "tuple": Tuple,
    "while_statement": While,
    "with_statement": With,
    "yield": Yield,

    "SimpleStatementLine": Statement,

    #clang
    'TRANSLATION_UNIT': TranslationUnit,
    'VAR_DECL': VariableDeclaration,
    'FUNCTION_DECL': FunctionDef,
    'CSTYLE_CAST_EXPR': Cast,
    'DECL_LOC': DeclarationLoc,
    'DECL_REF_EXPR': DeclarationExpression,
    'TYPE_REF': TypeReference,
    'COMPOUND_STMT': CompoundStatement,
    'DECL_STMT': Declaration,
    'PAREN_EXPR': ParenthesizedExpression,
    'BINARY_OPERATOR': BinaryOperation,
    'UNEXPOSED_EXPR': Expression,
    'INTEGER_LITERAL': Number,
    'UNARY_OPERATOR': UnaryOperation,
    'IF_STMT': If,
    'WHILE_STMT': While,
    'CALL_EXPR': Call,
    'COMPOUND_ASSIGNMENT_OPERATOR': Assign,
    'CONSTRUCTOR': Constructor,
    'DO_STMT': Do,
    'FIELD_DECL': FieldDeclaration,
    'MACRO_DEFINITION': MacroDefinition,
    'NAMESPACE': Namespace,
    'PARM_DECL': ParameterDeclaration,
    'RETURN_STMT': Return,
    'STRUCT_DECL': StructDeclaration,
    'TYPEDEF_DECL': TypedefDeclaration,
    'INIT_LIST_EXPR': ListComp,
    'STRING_LITERAL': FormattedString,
    'CLASS_DECL': ClassDeclaration,
    'CXX_BASE_SPECIFIER': BaseSpecifier,
    'CXX_ACCESS_SPEC_DECL': AccessSpecifier,
    'UNEXPOSED_DECL': Declaration,

    'AccessSpecDecl': AccessSpecifier,
    'CXXConstructorDecl': Constructor,
    'IntegerLiteral': Number,
    'CXXConstructExpr': ConstructorExpression,
    'DeclLoc': DeclarationLoc,
    'VarDecl': VariableDeclaration,
    'DeclStmt': Declaration,
    'CompoundStmt': CompoundStatement,
    'CallExpr': Call,
    'CStyleCastExpr': Cast,
    'TypedefDecl': TypedefDeclaration,
    'CXXRecordDecl': RecordDef,
    'RecordDecl': RecordDef,
    # 'FunctionDecl': FunctionDeclaration,
    'FunctionDecl': FunctionDef,
    'TranslationUnitDecl': TranslationUnit,
    'AccessSpecDecl': AccessSpecifier,
    'TypeRef': TypeReference,
    'ParmVarDecl': ParameterDeclaration,
    'BinaryOperator': BinaryOperation,
    'DeclRefExpr': DeclarationExpression,
    'IfStmt': If,
    'ParenExpr': ParenthesizedExpression,
    'UnaryOperator': UnaryOperation,
    'WhileStmt': While,
    'StringLiteral': String,
    'InitListExpr': ListComp,
    'FieldDecl': FieldDeclaration,
    'ImplicitValueInitExpr': Assign,
    'BuiltinType': BuiltinType,
    'CompoundAssignOperator': Assign,
    'DoStmt': Do,
    'ReturnStmt': Return,

    '_MatchAll__': MatchAll,
    '_MatchOne__': MatchOne,
    None: UnknownKind
}

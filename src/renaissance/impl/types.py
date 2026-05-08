from abc import ABC


class Type(ABC):
    pass

    def __str__(self):
        self.__class__.__name__


class UnknownType(Type):
    pass

class BogusType(Type):
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


class Definition(Statement):
    pass


class FunctionDef(Definition):
    pass


class If(Statement):
    pass

class ImportStatement(Statement):
    pass

class Import(ImportStatement):
    pass


class ImportFrom(ImportStatement):
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


class NotOperator(UnaryOperation):
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


class Declaration(Definition):
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


class MacroDefinition(Definition):
    pass


class Namespace(Node):
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


class GreaterThanEqual(ComparasionOperation):
    pass


class GreaterThan(ComparasionOperation):
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


class LeftShift(BinaryOperation):
    pass


class RightShift(BinaryOperation):
    pass


class Multiply(BinaryOperation):
    pass


class Power(BinaryOperation):
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


class ArgumentList(Node):
    pass


class Compare(Node):
    pass


class Keyword(Node):
    pass


class Arguments(Node):
    pass


class Error(Node):
    pass


class CatchClause(Node):
    pass


class ClassSpecifier(Node):
    pass


class Alias(Node):
    pass


class WithItem(Node):
    pass


class Symbol(Node):
    pass


class Colon(Symbol):
    pass


class AssignTo(Symbol):
    pass


class Whitespace(Type):
    pass


class InclusionDirective(Import):
    pass


KIND_MAP = {
    "block": CompoundStatement,
    "except": Catch,
    "none": BogusType,
    "return": Return,
    "string": Literal,
    "string_start": Literal,
    "string_content": Literal,
    "string_end": Literal,
    "case_clause": Case,
    "case": Case,
    "case_pattern": MatchSingleton,
    "withitem": WithItem,
    "Attribute": Attribute,
    "_": BogusType,
    "pass": Pass,
    "def": Symbol,
    "&": BitAnd,
    "(": Tuple,
    ")": Tuple,
    "+": Add,
    "-": Subtract,
    "~": Invert,
    "*": Multiply,
    "**": Power,
    "%": Modulo,
    "/": Divide,
    "//": FloorDiv,
    "+=": BogusType,
    "<": LessThan,
    "==": Equal,
    "=": AssignTo,
    ">": GreaterThan,
    ">=": GreaterThanEqual,
    "<=": LessThanEqual,
    "<<": LeftShift,
    ">>": RightShift,
    "!=": NotEqual,
    ":": Colon,
    "Add": Add,
    "AnnAssign": Assign,
    "Assert": Assert,
    "Assign": Assign,
    "AssignTarget": AssignTarget,
    "AsyncFor": For,
    "AsyncFunctionDef": FunctionDef,
    "AsyncWith": With,
    "Attributr": Attribute,
    "AugAssign": AugAssign,
    "Await": Await,
    "BinOp": BinaryOperation,
    "BinaryOperation": BinaryOperation,
    "BitAnd": BitAnd,
    "BitInvert": Invert,
    "BitOr": BitOr,
    "BitXor": BitXor,
    "BoolOp": BooleanOperation,
    "Break": Break,
    "Call": Call,
    "ClassDef": ClassDef,
    "Compare": Compare,
    "Constant": Literal,
    "Continue": Continue,
    "Del": Delete,
    "Delete": Delete,
    "Dict": Dict,
    "DictComp": DictComp,
    "Div": Divide,
    "ERROR": Error,
    "Eq": Equal,
    "ExceptHandler": Catch,
    "Expr": Expr,
    "FloorDiv": FloorDiv,
    "FloorDivide": FloorDiv,
    "For": For,
    "FormattedString": FormattedString,
    "FormattedValue": FormattedString,
    "FunctionDef": FunctionDef,
    "GeneratorExp": GeneratorExp,
    "Global": Global,
    "Greater": GreaterThan,
    "GreaterEqual": GreaterThanEqual,
    "Gt": GreaterThan,
    "GtE": GreaterThanEqual,
    "If": If,
    "IfExp": IfExp,
    "ImplicitNode": ImplicitNode,
    "Import": Import,
    "ImportFrom": ImportFrom,
    "In": In,
    "Invert": Invert,
    "Is": Is,
    "IsNot": IsNot,
    "JoinedStr": FormattedString,
    "LShift": LeftShift,
    "LeftShift": LeftShift,
    "Lambda": Lambda,
    "List": List,
    "ListComp": ListComp,
    "Lt": LessThan,
    "LtE": LessThanEqual,
    "Match": Match,
    "MatchAs": MatchAs,
    "MatchClass": MatchClass,
    "MatchMapping": MatchMapping,
    "MatchOr": MatchOr,
    "MatchList": MatchSequence,
    "MatchSequence": MatchSequence,
    "MatchSingleton": MatchSingleton,
    "MatchStar": MatchStar,
    "MatchValue": MatchValue,
    "Minus": UnarySubtract,
    "MinusOperator": UnarySubtract,
    "Mod": Modulo,
    "Module": TranslationUnit,
    "Mult": Multiply,
    "Multiply": Multiply,
    "Name": Name,
    "NamedExpr": NamedExpr,
    "Nonlocal": Nonlocal,
    "Not": NotOperator,
    "NotEq": NotEqual,
    "NotIn": NotIn,
    "Pass": Pass,
    "Plus": UnaryAdd,
    "PlusOperator": UnaryAdd,
    "Pow": Power,
    "RShift": RightShift,
    "RightShift": RightShift,
    "Raise": Raise,
    "Return": Return,
    "Set": Set,
    "SetComp": SetComp,
    "SimpleStatementLine": Statement,
    "Slice": Slice,
    "Starred": Starred,
    "Sub": Subtract,
    "Subscript": Subscript,
    "Try": Try,
    "TryStar": Try,
    "Tuple": Tuple,
    "TypeAlias": TypedefDeclaration,
    "UAdd": UnaryAdd,
    "USub": UnarySubtract,
    "UnaryOp": UnaryOperation,
    "UnaryOperation": UnaryOperation,
    "While": While,
    "With": With,
    "Yield": Yield,
    "YieldFrom": Yield,
    "[": List,
    "]": List,
    "^": BitXor,
    "arg": Argument,
    "argument_list": ArgumentList,
    "arguments": Arguments,
    "assert_statement": Assert,
    "assignment": Assign,
    "assignment_expression": Assign,
    "augmented_assignment": AugAssign,
    "await": Await,
    "alias": Alias,
    "binary_expression": BinaryOperation,
    "binary_operator": BinaryOperation,
    "boolean_operator": BooleanOperation,
    "break_statement": Break,
    "call": Call,
    "call_expression": Call,
    "catch": Catch,
    "catch_clause": CatchClause,
    "class": ClassDef,
    "class_definition": ClassDef,
    "class_specifier": ClassSpecifier,
    "compound_statement": CompoundStatement,
    "condition_clause": Compare,
    "conditional_expression": IfExp,
    "continue_statement": Continue,
    "declaration": Declaration,
    "del": Delete,
    "dictionary": Dict,
    "dictionary_comprehension": DictComp,
    "expression_statement": Expr,
    "field_declaration_list": Arguments,
    "for": For,
    "for_statement": For,
    "function_declarator": FunctionDef,
    "function_definition": FunctionDef,
    "generator_expression": GeneratorExp,
    "global": Global,
    "global_statement": Global,
    "identifier": Name,
    "if": If,
    "if_statement": If,
    "import_from_statement": ImportFrom,
    "import_statement": Import,
    "in": In,
    "init_declarator": Assign,
    "integer": Number,
    "is not": IsNot,
    "is": Is,
    "keyword": Keyword,
    "lambda": Lambda,
    "list": List,
    "list_comprehension": ListComp,
    "match_case": Case,
    "match_statement": Match,
    "module": TranslationUnit,
    "nonlocal_statement": Nonlocal,
    "not_operator": UnaryOperation,
    "not": NotOperator,
    "not in": NotIn,
    "number_literal": Number,
    "parameter_declaration": ParameterDeclaration,
    "parameter_list": ArgumentList,
    "parenthesized_expression": ParenthesizedExpression,
    "pass_statement": Pass,
    "raise_statement": Raise,
    "return_statement": Return,
    "set": Set,
    "set_comprehension": SetComp,
    "subscript": Subscript,
    "translation_unit": TranslationUnit,
    "try": Try,
    "try_statement": Try,
    "tuple": Tuple,
    "type_identifier": TypeReference,
    "unary_operator": UnaryOperation,
    "while": While,
    "while_statement": While,
    "with_statement": With,
    "yield": Yield,
    "{": Dict,
    "|": BitOr,
    "}": Dict,
    "AccessSpecDecl": AccessSpecifier,
    "BINARY_OPERATOR": BinaryOperation,
    "BinaryOperator": BinaryOperation,
    "BuiltinType": BuiltinType,
    "CALL_EXPR": Call,
    "CLASS_DECL": ClassDeclaration,
    "COMPOUND_ASSIGNMENT_OPERATOR": Assign,
    "COMPOUND_STMT": CompoundStatement,
    "CONSTRUCTOR": Constructor,
    "CSTYLE_CAST_EXPR": Cast,
    "CStyleCastExpr": Cast,
    "CXXConstructExpr": ConstructorExpression,
    "CXXConstructorDecl": Constructor,
    "CXXRecordDecl": RecordDef,
    "CXX_ACCESS_SPEC_DECL": AccessSpecifier,
    "CXX_BASE_SPECIFIER": BaseSpecifier,
    "CallExpr": Call,
    "CompoundAssignOperator": Assign,
    "CompoundStmt": CompoundStatement,
    "DECL_LOC": DeclarationLoc,
    "DECL_REF_EXPR": DeclarationExpression,
    "DECL_STMT": Declaration,
    "DO_STMT": Do,
    "DeclLoc": DeclarationLoc,
    "DeclRefExpr": DeclarationExpression,
    "DeclStmt": Declaration,
    "DoStmt": Do,
    "FIELD_DECL": FieldDeclaration,
    "FUNCTION_DECL": FunctionDef,
    "FieldDecl": FieldDeclaration,
    "FunctionDecl": FunctionDef,
    "IF_STMT": If,
    "INIT_LIST_EXPR": ListComp,
    "INTEGER_LITERAL": Number,
    "IfStmt": If,
    "ImplicitValueInitExpr": Assign,
    "InitListExpr": ListComp,
    "IntegerLiteral": Number,
    "MACRO_DEFINITION": MacroDefinition,
    "NAMESPACE": Namespace,
    "PAREN_EXPR": ParenthesizedExpression,
    "PARM_DECL": ParameterDeclaration,
    "ParenExpr": ParenthesizedExpression,

    "ParmVarDecl": ParameterDeclaration,
    "RETURN_STMT": Return,
    "RecordDecl": RecordDef,
    "ReturnStmt": Return,
    "STRING_LITERAL": FormattedString,
    "STRUCT_DECL": StructDeclaration,
    "StringLiteral": String,
    "TRANSLATION_UNIT": TranslationUnit,
    "TYPEDEF_DECL": TypedefDeclaration,
    "TYPE_REF": TypeReference,
    "TranslationUnitDecl": TranslationUnit,
    "TypeRef": TypeReference,
    "TypedefDecl": TypedefDeclaration,
    "UNARY_OPERATOR": UnaryOperation,
    "UNEXPOSED_DECL": Declaration,
    "UNEXPOSED_EXPR": Expression,
    "UnaryOperator": UnaryOperation,
    "VAR_DECL": VariableDeclaration,
    "VarDecl": VariableDeclaration,
    "WHILE_STMT": While,
    "WhileStmt": While,
    "_MatchAll__": MatchAll,
    "_MatchOne__": MatchOne,
    "MatchAll": MatchAll,
    "MatchOne": MatchOne,
    None: BogusType,
    "SimpleWhitespace": Whitespace,
    "IndentedBlock": CompoundStatement,
    "ImportAlias": Alias,
    "Arg": Argument,
    "Integer": Number,
    "InclusionDirective": InclusionDirective,
    "INCLUSION_DIRECTIVE": InclusionDirective,
}

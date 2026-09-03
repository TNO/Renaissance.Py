from abc import ABC


class Type(ABC):
    def __str__(self):
        return self.__class__.__name__


# Fallback
class UnknownType(Type):
    pass


class BogusType(UnknownType):
    pass


# Pattern
class Pattern(Type):
    pass


class MatchOne(Pattern):
    pass


class MatchAll(Pattern):
    pass


# Base
class Node(Type):
    pass


class BaseLeaf(Node):
    pass


class BaseValueToken(BaseLeaf):
    pass


class TranslationUnit(Node):
    pass


class Expression(Node):
    pass


class Operator(Node):
    pass


# whitespaces
class Whitespace(Type):
    pass


class BaseParenthesizableWhitespace(Whitespace):
    pass


class SimpleWhitespace(BaseParenthesizableWhitespace, BaseValueToken):
    pass


class Newline(BaseLeaf):
    pass


class Comment(Whitespace, BaseValueToken):
    pass


class ParagraphComment(Comment):
    pass


class TextComment(Comment):
    pass


class TrailingWhitespace(Whitespace):
    pass


class FullComment(Comment):
    pass


class EmptyLine(Whitespace):
    pass


class ParenthesizedWhitespace(BaseParenthesizableWhitespace):
    pass


# Operators
class _BaseOneTokenOp(Node):
    pass


class _BaseTwoTokenOp(Node):
    pass


class BaseUnaryOp(Node):
    pass


class BaseBooleanOp(_BaseOneTokenOp):
    pass


class BaseBinaryOp(Node):
    pass


class BaseCompOp(Node):
    pass


class BaseAugOp(Node):
    pass


class Semicolon(_BaseOneTokenOp):
    pass


class Colon(_BaseOneTokenOp):
    pass


class Comma(_BaseOneTokenOp):
    pass


class Dot(_BaseOneTokenOp):
    pass


class ImportStar(BaseLeaf):
    pass


class AssignEqual(_BaseOneTokenOp):
    pass


class Plus(BaseUnaryOp):
    pass


class Minus(BaseUnaryOp):
    pass


class BitInvert(BaseUnaryOp):
    pass


class Not(BaseUnaryOp):
    pass


class And(BaseBooleanOp):
    pass


class Or(BaseBooleanOp):
    pass


class Add(BaseBinaryOp, _BaseOneTokenOp):
    pass


class Subtract(BaseBinaryOp, _BaseOneTokenOp):
    pass


class Multiply(BaseBinaryOp, _BaseOneTokenOp):
    pass


class Divide(BaseBinaryOp, _BaseOneTokenOp):
    pass


class FloorDivide(BaseBinaryOp, _BaseOneTokenOp):
    pass


class Modulo(BaseBinaryOp, _BaseOneTokenOp):
    pass


class Power(BaseBinaryOp, _BaseOneTokenOp):
    pass


class LeftShift(BaseBinaryOp, _BaseOneTokenOp):
    pass


class RightShift(BaseBinaryOp, _BaseOneTokenOp):
    pass


class BitOr(BaseBinaryOp, _BaseOneTokenOp):
    pass


class BitAnd(BaseBinaryOp, _BaseOneTokenOp):
    pass


class BitXor(BaseBinaryOp, _BaseOneTokenOp):
    pass


class MatrixMultiply(BaseBinaryOp, _BaseOneTokenOp):
    pass


class LessThan(BaseCompOp, _BaseOneTokenOp):
    pass


class GreaterThan(BaseCompOp, _BaseOneTokenOp):
    pass


class Equal(BaseCompOp, _BaseOneTokenOp):
    pass


class LessThanEqual(BaseCompOp, _BaseOneTokenOp):
    pass


class GreaterThanEqual(BaseCompOp, _BaseOneTokenOp):
    pass


class NotEqual(BaseCompOp, _BaseOneTokenOp):
    pass


class In(BaseCompOp, _BaseOneTokenOp):
    pass


class NotIn(BaseCompOp, _BaseTwoTokenOp):
    pass


class Is(BaseCompOp, _BaseOneTokenOp):
    pass


class IsNot(BaseCompOp, _BaseTwoTokenOp):
    pass


class AddAssign(BaseAugOp, _BaseOneTokenOp):
    pass


class SubtractAssign(BaseAugOp, _BaseOneTokenOp):
    pass


class MultiplyAssign(BaseAugOp, _BaseOneTokenOp):
    pass


class MatrixMultiplyAssign(BaseAugOp, _BaseOneTokenOp):
    pass


class DivideAssign(BaseAugOp, _BaseOneTokenOp):
    pass


class ModuloAssign(BaseAugOp, _BaseOneTokenOp):
    pass


class BitAndAssign(BaseAugOp, _BaseOneTokenOp):
    pass


class BitOrAssign(BaseAugOp, _BaseOneTokenOp):
    pass


class BitXorAssign(BaseAugOp, _BaseOneTokenOp):
    pass


class LeftShiftAssign(BaseAugOp, _BaseOneTokenOp):
    pass


class RightShiftAssign(BaseAugOp, _BaseOneTokenOp):
    pass


class PowerAssign(BaseAugOp, _BaseOneTokenOp):
    pass


class FloorDivideAssign(BaseAugOp, _BaseOneTokenOp):
    pass


#  Expression
class LeftSquareBracket(Node):
    pass


class RightSquareBracket(Node):
    pass


class LeftCurlyBrace(Node):
    pass


class RightCurlyBrace(Node):
    pass


class LeftParen(Node):
    pass


class RightParen(Node):
    pass


class Asynchronous(Node):
    pass


class _BaseParenthesizedNode(Node):
    pass


# class ExpressionPosition(Enum): pass
class BaseExpression(_BaseParenthesizedNode):
    pass


class BaseAssignTargetExpression(BaseExpression):
    pass


class BaseDelTargetExpression(BaseExpression):
    pass


class Literal(BaseExpression):
    pass


class Name(BaseAssignTargetExpression, BaseDelTargetExpression):
    pass


class EllipsisLiteral(BaseExpression):
    pass


class BaseNumber(BaseExpression):
    pass


class Integer(BaseNumber):
    pass


class Float(BaseNumber):
    pass


class Imaginary(BaseNumber):
    pass


class BaseString(BaseExpression):
    pass


class Character(BaseExpression):
    pass


# StringQuoteLiteral = Literal['"', "'", '"""', "'''"]
class _BasePrefixedString(BaseString):
    pass


class SimpleString(_BasePrefixedString):
    pass


class BaseFormattedStringContent(Node):
    pass


class FormattedStringText(BaseFormattedStringContent):
    pass


class FormattedStringExpression(BaseFormattedStringContent):
    pass


class FormattedString(_BasePrefixedString):
    pass


class BaseTemplatedStringContent(Node):
    pass


class TemplatedStringText(BaseTemplatedStringContent):
    pass


class TemplatedStringExpression(BaseTemplatedStringContent):
    pass


class TemplatedString(_BasePrefixedString):
    pass


class ConcatenatedString(BaseString):
    pass


class ComparisonTarget(Node):
    pass


class Comparison(BaseExpression):
    pass


class UnaryOperation(BaseExpression):
    pass


class BinaryOperation(BaseExpression):
    pass


class BooleanOperation(BaseExpression):
    pass


class Attribute(BaseAssignTargetExpression, BaseDelTargetExpression):
    pass


class BaseSlice(Node):
    pass


class Index(BaseSlice):
    pass


class Slice(BaseSlice):
    pass


class SubscriptElement(Node):
    pass


class Subscript(BaseAssignTargetExpression, BaseDelTargetExpression):
    pass


class Annotation(Node):
    pass


class ParamStar(Node):
    pass


class ParamSlash(Node):
    pass


class Param(Node):
    pass


class Parameters(Node):
    pass


class Lambda(BaseExpression):
    pass


class Arg(Node):
    pass


class _BaseExpressionWithArgs(BaseExpression):
    pass


class Call(_BaseExpressionWithArgs):
    pass


class Await(BaseExpression):
    pass


class IfExp(BaseExpression):
    pass


class From(Node):
    pass


class Yield(BaseExpression):
    pass


class _BaseElementImpl(Node):
    pass


class BaseElement(_BaseElementImpl):
    pass


class BaseDictElement(_BaseElementImpl):
    pass


class Element(BaseElement):
    pass


class DictElement(BaseDictElement):
    pass


class StarredElement(BaseElement, BaseExpression, _BaseParenthesizedNode):
    pass


class StarredDictElement(BaseDictElement):
    pass


class Tuple(BaseAssignTargetExpression, BaseDelTargetExpression):
    pass


class BaseList(BaseExpression):
    pass


class List(BaseList, BaseAssignTargetExpression, BaseDelTargetExpression):
    pass


class _BaseSetOrDict(BaseExpression):
    pass


class BaseSet(_BaseSetOrDict):
    pass


class Set(BaseSet):
    pass


class BaseDict(_BaseSetOrDict):
    pass


class Dict(BaseDict):
    pass


class CompFor(Node):
    pass


class CompIf(Node):
    pass


class BaseComp(BaseExpression):
    pass


class BaseSimpleComp(BaseComp):
    pass


class GeneratorExp(BaseSimpleComp):
    pass


class ListComp(BaseList, BaseSimpleComp):
    pass


class SetComp(BaseSet, BaseSimpleComp):
    pass


class DictComp(BaseDict, BaseComp):
    pass


class NamedExpr(BaseExpression):
    pass


# Statement
class Statement(Node):
    pass


class BaseSuite(Statement):
    pass


class BaseStatement(Statement):
    pass


class BaseSmallStatement(Statement):
    pass


class Del(BaseSmallStatement):
    pass


class Pass(BaseSmallStatement):
    pass


class Break(BaseSmallStatement):
    pass


class Continue(BaseSmallStatement):
    pass


class Return(BaseSmallStatement):
    pass


class ExpressionStatement(BaseSmallStatement):
    pass


class _BaseSimpleStatement(Node):
    pass


class SimpleStatementLine(_BaseSimpleStatement, BaseStatement):
    pass


class SimpleStatementSuite(_BaseSimpleStatement, BaseSuite):
    pass


class Else(Node):
    pass


class BaseCompoundStatement(BaseStatement):
    pass


class If(BaseCompoundStatement):
    pass


class CompoundStatement(BaseSuite):
    pass


class IndentedBlock(BaseSuite):
    pass


class AsName(Node):
    pass


class ExceptHandler(Node):
    pass


class ExceptStarHandler(Node):
    pass


class Catch(Node):
    pass


class Finally(Node):
    pass


class Try(BaseCompoundStatement):
    pass


class TryStar(BaseCompoundStatement):
    pass


class ImportStatement(BaseSmallStatement):
    pass


class ImportAlias(Node):
    pass


class Import(ImportStatement):
    pass


class ImportFrom(ImportStatement):
    pass


class InclusionDirective(ImportStatement):
    pass


class IncludeDirective(ImportStatement):
    pass


class AssignTarget(Node):
    pass


class Assign(BaseSmallStatement):
    pass


class AnnAssign(BaseSmallStatement):
    pass


class AugAssign(BaseSmallStatement):
    pass


class Decorator(Node):
    pass


class Declaration(BaseSmallStatement):
    pass


class Definition(BaseCompoundStatement):
    pass


class DefinitionX(CompoundStatement):
    pass


class FunctionDef(Definition):
    pass


class ClassDef(Definition):
    pass


class StructDef(Definition):
    pass


class RecordDef(Definition):
    pass


class VariableDef(Definition):
    pass


class FieldDef(Definition):
    pass


class InterfaceDef(Definition):
    pass


class LocalVariableDef(Definition):
    pass


class TemplateDef(Definition):
    pass


class TypeParameterDef(Definition):
    pass


class TypeAlias(Definition):
    pass


class TypedefDef(TypeAlias):
    pass


class PackageDef(Definition):
    pass


class ParameterDef(Definition):
    pass


class UnionDef(Definition):
    pass


class WithItem(Node):
    pass


class With(BaseCompoundStatement):
    pass


class Do(BaseCompoundStatement):
    pass


class For(BaseCompoundStatement):
    pass


class While(BaseCompoundStatement):
    pass


class Raise(BaseSmallStatement):
    pass


class Assert(BaseSmallStatement):
    pass


class NameItem(Node):
    pass


class Global(BaseSmallStatement):
    pass


class Nonlocal(BaseSmallStatement):
    pass


class MatchPattern(_BaseParenthesizedNode):
    pass


class Match(BaseCompoundStatement):
    pass


class MatchCase(Node):
    pass


class MatchValue(MatchPattern):
    pass


class MatchSingleton(MatchPattern):
    pass


class MatchSequenceElement(Node):
    pass


class MatchStar(Node):
    pass


class MatchSequence(MatchPattern):
    pass


class MatchList(MatchSequence):
    pass


class MatchTuple(MatchSequence):
    pass


class MatchMappingElement(Node):
    pass


class MatchMapping(MatchPattern):
    pass


class MatchKeywordElement(Node):
    pass


class MatchClass(MatchPattern):
    pass


class MatchAs(MatchPattern):
    pass


class MatchOrElement(Node):
    pass


class MatchOr(MatchPattern):
    pass


class TypeVar(Node):
    pass


class TypeVarTuple(Node):
    pass


class ParamSpec(Node):
    pass


class TypeParam(Node):
    pass


class TypeParameters(Node):
    pass


# ==== added=====


class ImplicitNode(Node):
    pass


# Specifier
class Specifier(Node):
    pass


class Auto(Specifier):
    pass


class BaseSpecifier(Specifier):
    pass


class ClassSpecifier(Specifier):
    pass


class AccessSpecifier(Specifier):
    pass


class EnumSpecifier(Specifier):
    pass


class StructSpecifier(Specifier):
    pass


# Reference
class Reference(Expression):
    pass


class TypeReference(Reference):
    pass


class MemberRefence(Reference):
    pass


class NamespaceReference(Reference):
    pass


class OverloadedDeclRef(Reference):
    pass


class TemplateRef(Reference):
    pass


# Attributes
class AlignedAttribute:
    pass


class AsmAttribute:
    pass


class ConstAttr:
    pass


class VisibilityAttr:
    pass


class WarnUnusedResultAttr:
    pass


class FinalAttr:
    pass


class OverrideAttr:
    pass


class PureAttr:
    pass


class UnexposedAttr:
    pass


class DeclarationExpression(Expression):
    pass


class ParenthesizedExpression(Expression):
    pass


class Constructor(FunctionDef):
    pass


class MacroDef(Definition):
    pass


class Namespace(Node):
    pass


class ConstructorExpression(Call):
    pass


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


class Alias(Node):
    pass


class Symbol(Node):
    pass


class AssignTo(Symbol):
    pass


class Cast(Node):
    pass


class BuiltinType(Literal):
    pass


class DeclarationLoc(Declaration):
    pass


class Delete(Expression):
    pass


class Starred(Literal):
    pass


class Constant(Literal):
    pass


class Number(Literal):
    pass


class String(Literal):
    pass


class Catch(Statement):
    pass


class ComparisionOperation(Expression):
    pass


class UnaryAdd(UnaryOperation):
    pass


class UnarySubtract(UnaryOperation):
    pass


class Case(Statement):
    pass


class MatchSequence(Node):
    pass


# other
class ConstructorDef(Definition):
    pass


class FriendDecl:
    pass


class AbstractFunctionDeclarator:
    pass


class As:
    pass


class AsPattern:
    pass


class AsPatternTarget:
    pass


class Asterisk:
    pass


class Async:
    pass


class Backslash:
    pass


class CatchFormalParameter:
    pass


class CatchType:
    pass


class ClassBody:
    pass


class ClassPattern:
    pass


class ClassTemplate:
    pass


class ClassTemplatePartial:
    pass


class Comprehension:
    pass


class ConditionalOperator:
    pass


class ConstCastExpr:
    pass


class ConstructorBody:
    pass


class ConversionFunction:
    pass


class BooleanLiteral:
    pass


class FunctionalCast:
    pass


class NullPointer:
    pass


class This:
    pass


class Typeid:
    pass


class DeclarationList:
    pass


class DefaultStmt:
    pass


class Destructor:
    pass


class DictPattern:
    pass


class Dimensions:
    pass


class DottedName:
    pass


class DynamicCastExpr:
    pass


class Enum:
    pass


class EnumBody:
    pass


class EnumConstant:
    pass


class EnumeratorList:
    pass


class ExceptClause:
    pass


class Extends:
    pass


class FieldAccess:
    pass


class FieldIdentifier:
    pass


class FinallyClause:
    pass


class FormalParameter:
    pass


class FormalParameters:
    pass


class FunctionTemplate:
    pass


class IntegralType:
    pass


class Interface:
    pass


class InterfaceBody:
    pass


class Interpolation:
    pass


class LambdaParameters:
    pass


class LinkageSpec:
    pass


class ListPattern:
    pass


class MarkerAnnotation:
    pass


class Method:
    pass


class Modifiers:
    pass


class NamespaceIdentifier:
    pass


class New:
    pass


class Null:
    pass


class ObjectCreationExpression:
    pass


class PackExpansionExpr:
    pass


class Package:
    pass


class Pair:
    pass


class PointerDeclarator:
    pass


class Program:
    pass


class Public:
    pass


class QualifiedIdentifier:
    pass


class ReinterpretCastExpr:
    pass


class ScopedIdentifier:
    pass


class SizeOfPackExpr:
    pass


class SplatPattern:
    pass


class Static:
    pass


class StaticAssert:
    pass


class StaticCastExpr:
    pass


class StringFragment:
    pass


class StringLiteral:
    pass


class Superclass:
    pass


class Switch(Match):
    pass


class SwitchBlock(CompoundStatement):
    pass


class SwitchBlockStatementGroup:
    pass


class SwitchExpression:
    pass


class SwitchLabel(MatchPattern):
    pass


class Symbol:
    pass


class SystemLibString:
    pass


class TemplateNonTypeParameter:
    pass


class TemplateParameterList:
    pass


class TemplateTypeParameter:
    pass


class TypeAliasTemplateDecl:
    pass


class TypeName:
    pass


class Underscore:
    pass


class UnexposedStmt:
    pass


class UnionPattern:
    pass


class UpdateExpression:
    pass


class Using:
    pass


class VoidType:
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

KIND_MAP = {
    "!": Not,
    "!=": NotEqual,
    "#include": IncludeDirective,
    "%": Modulo,
    "&": BitAnd,
    "&&": And,
    "'": Symbol,
    "(": Tuple,
    ")": Tuple,
    "*": Multiply,
    "**": Power,
    "+": Add,
    "++": UnaryAdd,
    "+=": BogusType,
    ",": Symbol,
    "-": Subtract,
    ".": Symbol,
    "...": Symbol,
    "/": Divide,
    "//": FloorDivide,
    ":": Colon,
    "::": Symbol,
    ";": Symbol,
    "<": LessThan,
    "<<": LeftShift,
    "<=": LessThanEqual,
    "=": AssignEqual,
    "==": Equal,
    ">": GreaterThan,
    ">=": GreaterThanEqual,
    ">>": RightShift,
    "@": Symbol,
    "[": ListComp,
    "\\": Backslash,
    "]": ListComp,
    "^": BitXor,
    "_": Underscore,
    "_MatchAll__": MatchAll,
    "_MatchOne__": MatchOne,
    "abstract_function_declarator": AbstractFunctionDeclarator,
    "AccessSpecDecl": AccessSpecifier,
    "Add": Add,
    "AddAssign": AddAssign,
    "alias": TypeAlias,
    "ALIGNED_ATTR": AlignedAttribute,
    "and": And,
    "And": And,
    "AnnAssign": Assign,
    "Annotation": Annotation,
    "Arg": Arg,
    "arg": Arg,
    "argument_list": ArgumentList,
    "arguments": Arguments,
    "ARRAY_SUBSCRIPT_EXPR": Subscript,
    "array_type": List,
    "as": As,
    "as_pattern": AsPattern,
    "as_pattern_target": AsPatternTarget,
    "ASM_LABEL_ATTR": AsmAttribute,
    "AsName": AsName,
    "assert": Assert,
    "Assert": Assert,
    "assert_statement": Assert,
    "Assign": Assign,
    "AssignEqual": AssignEqual,
    "assignment": Assign,
    "assignment_expression": Assign,
    "AssignTarget": AssignTarget,
    "asterisk": Asterisk,
    "async": Async,
    "AsyncFor": For,
    "AsyncFunctionDef": FunctionDef,
    "Asynchronous": Asynchronous,
    "AsyncWith": With,
    "attribute": Attribute,
    "Attribute": Attribute,
    "AugAssign": AugAssign,
    "augmented_assignment": AugAssign,
    "auto": Auto,
    "Await": Await,
    "await": Await,
    "binary_expression": BinaryOperation,
    "binary_operator": BinaryOperation,
    "BINARY_OPERATOR": BinaryOperation,
    "BinaryOperation": BinaryOperation,
    "BinaryOperator": BinaryOperation,
    "BinOp": BinaryOperation,
    "BitAnd": BitAnd,
    "BitInvert": BitInvert,
    "BitOr": BitOr,
    "BitXor": BitXor,
    "block": CompoundStatement,
    "boolean_operator": BooleanOperation,
    "BooleanOperation": BooleanOperation,
    "BoolOp": BooleanOperation,
    "break": Break,
    "Break": Break,
    "break_statement": Break,
    "BREAK_STMT": Break,
    "BuiltinType": BuiltinType,
    "Call": Call,
    "call": Call,
    "CALL_EXPR": Call,
    "call_expression": Call,
    "CallExpr": Call,
    "case": MatchCase,
    "case_clause": MatchCase,
    "case_pattern": MatchSingleton,
    "case_statement": MatchCase,
    "CASE_STMT": MatchCase,
    "catch": ExceptHandler,
    "catch_clause": ExceptHandler,
    "catch_formal_parameter": CatchFormalParameter,
    "catch_type": CatchType,
    "char_literal": Character,
    "character": Character,
    "CHARACTER_LITERAL": Character,
    "class": ClassDef,
    "class_body": ClassBody,
    "CLASS_DECL": ClassDef,
    "class_declaration": ClassDef,
    "class_definition": ClassDef,
    "class_pattern": ClassPattern,
    "class_specifier": ClassSpecifier,
    "CLASS_TEMPLATE": ClassTemplate,
    "CLASS_TEMPLATE_PARTIAL_SPECIALIZATION": ClassTemplatePartial,
    "ClassDef": ClassDef,
    "Colon": Colon,
    "Comma": Comma,
    "Comment": Comment,
    "comment": Comment,
    "Compare": Compare,
    "Comparison": Comparison,
    "comparison_operator": Comparison,
    "ComparisonTarget": ComparisonTarget,
    "CompFor": CompFor,
    "COMPOUND_ASSIGNMENT_OPERATOR": Assign,
    "compound_statement": CompoundStatement,
    "COMPOUND_STMT": CompoundStatement,
    "CompoundAssignOperator": Assign,
    "CompoundStmt": CompoundStatement,
    "comprehension": Comprehension,
    "condition_clause": Compare,
    "conditional_expression": IfExp,
    "CONDITIONAL_OPERATOR": ConditionalOperator,
    "CONST_ATTR": ConstAttr,
    "Constant": Literal,
    "CONSTRUCTOR": Constructor,
    "constructor_body": ConstructorBody,
    "constructor_declaration": ConstructorDef,
    "continue": Continue,
    "Continue": Continue,
    "continue_statement": Continue,
    "CONTINUE_STMT": Continue,
    "CONVERSION_FUNCTION": ConversionFunction,
    "CSTYLE_CAST_EXPR": Cast,
    "CStyleCastExpr": Cast,
    "CXX_ACCESS_SPEC_DECL": AccessSpecifier,
    "CXX_BASE_SPECIFIER": BaseSpecifier,
    "CXX_BOOL_LITERAL_EXPR": BooleanLiteral,
    "CXX_CATCH_STMT": ExceptHandler,
    "CXX_CONST_CAST_EXPR": ConstCastExpr,
    "CXX_DELETE_EXPR": Del,
    "CXX_DYNAMIC_CAST_EXPR": DynamicCastExpr,
    "CXX_FINAL_ATTR": FinalAttr,
    "CXX_FOR_RANGE_STMT": For,
    "CXX_FUNCTIONAL_CAST_EXPR": FunctionalCast,
    "CXX_METHOD": Method,
    "CXX_NEW_EXPR": New,
    "CXX_NULL_PTR_LITERAL_EXPR": NullPointer,
    "CXX_OVERRIDE_ATTR": OverrideAttr,
    "CXX_REINTERPRET_CAST_EXPR": ReinterpretCastExpr,
    "CXX_STATIC_CAST_EXPR": StaticCastExpr,
    "CXX_THIS_EXPR": This,
    "CXX_THROW_EXPR": Raise,
    "CXX_TRY_STMT": Try,
    "CXX_TYPEID_EXPR": Typeid,
    "CXX_UNARY_EXPR": UnaryOperation,
    "CXXConstructExpr": ConstructorExpression,
    "CXXConstructorDecl": Constructor,
    "CXXRecordDecl": RecordDef,
    "decimal_integer_literal": Integer,
    "DECL_LOC": DeclarationLoc,
    "DECL_REF_EXPR": DeclarationExpression,
    "DECL_STMT": Declaration,
    "declaration": Declaration,
    "declaration_list": DeclarationList,
    "DeclLoc": DeclarationLoc,
    "DeclRefExpr": DeclarationExpression,
    "DeclStmt": Declaration,
    "Decorator": Decorator,
    "def": Symbol,
    "DEFAULT_STMT": DefaultStmt,
    "Del": Del,
    "del": Del,
    "Delete": Del,
    "delete_statement": Del,
    "DESTRUCTOR": Destructor,
    "Dict": Dict,
    "dict_pattern": DictPattern,
    "DictComp": DictComp,
    "DictElement": DictElement,
    "dictionary": Dict,
    "dictionary_comprehension": DictComp,
    "dimensions": Dimensions,
    "Div": Divide,
    "Divide": Divide,
    "do": Do,
    "do_statement": Do,
    "DO_STMT": Do,
    "DoStmt": Do,
    "Dot": Dot,
    "dotted_name": DottedName,
    "Element": Element,
    "ellipsis": EllipsisLiteral,
    "else": Else,
    "EmptyLine": EmptyLine,
    "enum": Enum,
    "enum_body": EnumBody,
    "enum_constant": EnumConstant,
    "ENUM_CONSTANT_DECL": EnumConstant,
    "ENUM_DECL": Enum,
    "enum_declaration": Enum,
    "enum_specifier": EnumSpecifier,
    "enumerator": Enum,
    "enumerator_list": EnumeratorList,
    "Eq": Equal,
    "Equal": Equal,
    "ERROR": Error,
    "except": Catch,
    "except_clause": ExceptClause,
    "ExceptHandler": Catch,
    "ExceptStarHandler": ExceptStarHandler,
    "Expr": ExpressionStatement,
    "expression_statement": ExpressionStatement,
    "extends": Extends,
    "field_access": FieldAccess,
    "FIELD_DECL": FieldDef,
    "field_declaration": FieldDef,
    "field_declaration_list": Arguments,
    "field_identifier": FieldIdentifier,
    "FieldDecl": FieldDef,
    "Finally": Finally,
    "finally": Finally,
    "finally_clause": FinallyClause,
    "float": float,
    "FLOATING_LITERAL": Float,
    "FloorDiv": FloorDivide,
    "FloorDivide": FloorDivide,
    "For": For,
    "for": For,
    "for_in_clause": For,
    "for_statement": For,
    "FOR_STMT": For,
    "formal_parameter": FormalParameter,
    "formal_parameters": FormalParameters,
    "FormattedString": FormattedString,
    "FormattedStringExpression": FormattedStringExpression,
    "FormattedStringText": FormattedStringText,
    "FormattedValue": FormattedString,
    "FRIEND_DECL": FriendDecl,
    "From": From,
    "from": From,
    "FullComment": FullComment,
    "FUNCTION_DECL": FunctionDef,
    "function_declarator": FunctionDef,
    "function_definition": FunctionDef,
    "FUNCTION_TEMPLATE": FunctionTemplate,
    "FunctionDecl": FunctionDef,
    "FunctionDef": FunctionDef,
    "generator_expression": GeneratorExp,
    "GeneratorExp": GeneratorExp,
    "Global": Global,
    "global": Global,
    "global_statement": Global,
    "Greater": GreaterThan,
    "GreaterEqual": GreaterThanEqual,
    "GreaterThan": GreaterThan,
    "GreaterThanEqual": GreaterThanEqual,
    "Gt": GreaterThan,
    "GtE": GreaterThanEqual,
    "identifier": Name,
    "If": If,
    "if": If,
    "if_clause": IfExp,
    "if_statement": If,
    "IF_STMT": If,
    "IfExp": IfExp,
    "IfStmt": If,
    "ImplicitNode": ImplicitNode,
    "ImplicitValueInitExpr": Assign,
    "import": Import,
    "Import": Import,
    "import_declaration": Import,
    "import_from_statement": ImportFrom,
    "import_statement": Import,
    "ImportAlias": ImportAlias,
    "ImportFrom": ImportFrom,
    "In": In,
    "in": In,
    "INCLUSION_DIRECTIVE": InclusionDirective,
    "InclusionDirective": InclusionDirective,
    "IndentedBlock": IndentedBlock,
    "init_declarator": Assign,
    "INIT_LIST_EXPR": ListComp,
    "InitListExpr": ListComp,
    "int": int,
    "Integer": Number,
    "integer": Number,
    "INTEGER_LITERAL": Number,
    "IntegerLiteral": Number,
    "integral_type": IntegralType,
    "interface": Interface,
    "interface_body": InterfaceBody,
    "interface_declaration": InterfaceDef,
    "interpolation": Interpolation,
    "Invert": BitInvert,
    "is not": IsNot,
    "Is": Is,
    "is": Is,
    "IsNot": IsNot,
    "JoinedStr": FormattedString,
    "keyword": Keyword,
    "keyword_pattern": Keyword,
    "Lambda": Lambda,
    "lambda": Lambda,
    "lambda_capture_specifier": LambdaParameters,
    "LAMBDA_EXPR": Lambda,
    "lambda_expression": Lambda,
    "lambda_parameters": LambdaParameters,
    "LeftCurlyBrace": LeftCurlyBrace,
    "LeftParen": LeftParen,
    "LeftShift": LeftShift,
    "LeftSquareBracket": ListComp,
    "LessThan": LessThan,
    "LessThanEqual": LessThanEqual,
    "LINKAGE_SPEC": LinkageSpec,
    "List": List,
    "list": List,
    "list_comprehension": ListComp,
    "list_pattern": ListPattern,
    "ListComp": ListComp,
    "local_variable_declaration": LocalVariableDef,
    "LShift": LeftShift,
    "Lt": LessThan,
    "LtE": LessThanEqual,
    "MACRO_DEFINITION": MacroDef,
    "marker_annotation": MarkerAnnotation,
    "match": Match,
    "Match": Match,
    "MatMult": MatrixMultiply,
    "match_case": MatchCase,
    "match_statement": Match,
    "MatchAll": MatchAll,
    "MatchAs": MatchAs,
    "MatchCase": MatchCase,
    "MatchClass": MatchClass,
    "MatchKeywordElement": MatchKeywordElement,
    "MatchList": MatchSequence,
    "MatchMapping": MatchMapping,
    "MatchMappingElement": MatchMappingElement,
    "MatchOne": MatchOne,
    "MatchOr": MatchOr,
    "MatchOrElement": MatchOrElement,
    "MatchSequence": MatchSequence,
    "MatchSequenceElement": MatchSequenceElement,
    "MatchSingleton": MatchSingleton,
    "MatchStar": MatchStar,
    "MatchValue": MatchValue,
    "MEMBER_REF": MemberRefence,
    "MEMBER_REF_EXPR": MemberRefence,
    "method_declaration": FunctionDef,
    "method_invocation": Call,
    "Minus": UnarySubtract,
    "MinusOperator": UnarySubtract,
    "Mod": Modulo,
    "modifiers": Modifiers,
    "Module": TranslationUnit,
    "module": TranslationUnit,
    "Modulo": Modulo,
    "Mult": Multiply,
    "Multiply": Multiply,
    "Name": Name,
    "NamedExpr": NamedExpr,
    "NameItem": NameItem,
    "namespace": Namespace,
    "NAMESPACE": Namespace,
    "namespace_definition": Namespace,
    "namespace_identifier": NamespaceIdentifier,
    "NAMESPACE_REF": NamespaceReference,
    "NamespaceDecl": Namespace,
    "new": New,
    "Newline": Newline,
    "none": BogusType,
    "nonlocal": Nonlocal,
    "Nonlocal": Nonlocal,
    "nonlocal_statement": Nonlocal,
    "not in": NotIn,
    "Not": Not,
    "not": Not,
    "not_operator": UnaryOperation,
    "NotEq": NotEqual,
    "NotEqual": NotEqual,
    "NotIn": NotIn,
    "null": Null,
    "NULL_STMT": Null,
    "nullptr": Null,
    "number_literal": Number,
    "object_creation_expression": ObjectCreationExpression,
    "or": Or,
    "Or": Or,
    "OVERLOADED_DECL_REF": OverloadedDeclRef,
    "PACK_EXPANSION_EXPR": PackExpansionExpr,
    "package": Package,
    "package_declaration": PackageDef,
    "pair": Pair,
    "ParagraphComment": ParagraphComment,
    "Param": Param,
    "parameter_declaration": ParameterDef,
    "parameter_list": ArgumentList,
    "Parameters": Parameters,
    "ParamSpec": ParamSpec,
    "parameters": Parameters,
    "PAREN_EXPR": ParenthesizedExpression,
    "ParenExpr": ParenthesizedExpression,
    "parenthesized_expression": ParenthesizedExpression,
    "ParenthesizedWhitespace": ParenthesizedWhitespace,
    "PARM_DECL": ParameterDef,
    "ParmVarDecl": ParameterDef,
    "pass": Pass,
    "Pass": Pass,
    "pass_statement": Pass,
    "Plus": UnaryAdd,
    "PlusOperator": UnaryAdd,
    "pointer_declarator": PointerDeclarator,
    "Pow": Power,
    "Power": Power,
    "primitive_type": BuiltinType,
    "program": Program,
    "public": Public,
    "PURE_ATTR": PureAttr,
    "qualified_identifier": QualifiedIdentifier,
    "raise": Raise,
    "Raise": Raise,
    "raise_statement": Raise,
    "RecordDecl": RecordDef,
    "return": Return,
    "Return": Return,
    "return_statement": Return,
    "RETURN_STMT": Return,
    "ReturnStmt": Return,
    "RightCurlyBrace": RightCurlyBrace,
    "RightParen": RightParen,
    "RightShift": RightShift,
    "RightSquareBracket": ListComp,
    "RShift": RightShift,
    "scoped_identifier": ScopedIdentifier,
    "Set": Set,
    "set": Set,
    "set_comprehension": SetComp,
    "SetComp": SetComp,
    "SimpleStatementLine": Statement,
    "SimpleStatementSuite": SimpleStatementSuite,
    "SimpleString": SimpleString,
    "SimpleWhitespace": Whitespace,
    "SIZE_OF_PACK_EXPR": SizeOfPackExpr,
    "slice": slice,
    "Slice": Slice,
    "splat_pattern": SplatPattern,
    "Starred": Starred,
    "static": Static,
    "STATIC_ASSERT": StaticAssert,
    "str": str,
    "string": Literal,
    "string_content": Literal,
    "string_end": Literal,
    "string_fragment": StringFragment,
    "STRING_LITERAL": FormattedString,
    "string_literal": StringLiteral,
    "string_start": Literal,
    "StringLiteral": String,
    "struct": StructDef,
    "STRUCT_DECL": StructDef,
    "struct_specifier": StructSpecifier,
    "Sub": Subtract,
    "Subscript": Subscript,
    "subscript": Subscript,
    "SubscriptElement": SubscriptElement,
    "Subtract": Subtract,
    "superclass": Superclass,
    "switch": Switch,
    "switch_block": SwitchBlock,
    "switch_block_statement_group": SwitchBlockStatementGroup,
    "switch_expression": SwitchExpression,
    "switch_label": SwitchLabel,
    "switch_statement": Switch,
    "SWITCH_STMT": Switch,
    "system_lib_string": SystemLibString,
    "template": TemplateDef,
    "template_declaration": TemplateDef,
    "TEMPLATE_NON_TYPE_PARAMETER": TemplateNonTypeParameter,
    "template_parameter_list": TemplateParameterList,
    "TEMPLATE_REF": TemplateRef,
    "TEMPLATE_TEMPLATE_PARAMETER": TemplateParameterList,
    "TEMPLATE_TYPE_PARAMETER": TemplateTypeParameter,
    "TextComment": TextComment,
    "TrailingWhitespace": TrailingWhitespace,
    "translation_unit": TranslationUnit,
    "TRANSLATION_UNIT": TranslationUnit,
    "TranslationUnit": TranslationUnit,
    "TranslationUnitDecl": TranslationUnit,
    "Try": Try,
    "try": Try,
    "try_statement": Try,
    "TryStar": Try,
    "Tuple": Tuple,
    "tuple": Tuple,
    "type_alias_statement": TypeAlias,
    "TYPE_ALIAS_DECL": TypeAlias,
    "TYPE_ALIAS_TEMPLATE_DECL": TypeAliasTemplateDecl,
    "type_identifier": TypeReference,
    "type_parameter_declaration": TypeParameterDef,
    "TYPE_REF": TypeReference,
    "TypeAlias": TypeAlias,
    "TYPEDEF_DECL": TypedefDef,
    "TypedefDecl": TypedefDef,
    "typename": TypeName,
    "TypeRef": TypeReference,
    "TypeVar": TypeVar,
    "TypeVarTuple": TypeVarTuple,
    "UAdd": UnaryAdd,
    "unary_expression": UnaryOperation,
    "unary_operator": UnaryOperation,
    "UNARY_OPERATOR": UnaryOperation,
    "UnaryOp": UnaryOperation,
    "UnaryOperation": UnaryOperation,
    "UnaryOperator": UnaryOperation,
    "UNEXPOSED_ATTR": UnexposedAttr,
    "UNEXPOSED_DECL": Declaration,
    "UNEXPOSED_EXPR": Expression,
    "UNEXPOSED_STMT": UnexposedStmt,
    "UNION_DECL": UnionDef,
    "union_pattern": UnionPattern,
    "update_expression": UpdateExpression,
    "using": Using,
    "USING_DIRECTIVE": Using,
    "USub": UnarySubtract,
    "VAR_DECL": VariableDef,
    "VarDecl": VariableDef,
    "variable_declarator": VariableDef,
    "VISIBILITY_ATTR": VisibilityAttr,
    "void_type": VoidType,
    "WARN_UNUSED_RESULT_ATTR": WarnUnusedResultAttr,
    "While": While,
    "while": While,
    "while_statement": While,
    "WHILE_STMT": While,
    "WhileStmt": While,
    "with": With,
    "With": With,
    "with_clause": With,
    "with_item": WithItem,
    "with_statement": With,
    "WithItem": WithItem,
    "withitem": WithItem,
    "Yield": Yield,
    "yield": Yield,
    "YieldFrom": Yield,
    "{": Dict,
    "|": BitOr,
    "||": Or,
    "}": Dict,
    "~": BitInvert,
    '"': Symbol,
    None: BogusType,
}

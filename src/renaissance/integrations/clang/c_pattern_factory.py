import re
from collections.abc import Sequence

from more_itertools import first
from more_itertools.more import last

from renaissance.integrations.clang.cpp_utils import CPPUtils
from renaissance.integrations.types import (
    Call,
    CompoundStatement,
    Declaration,
    FunctionDef,
    InclusionDirective,
    MacroDef,
    ParenthesizedExpression,
    Type,
    TypedefDef,
    VariableDef,
)
from renaissance.syntax_tree.ast_factory import ASTFactory
from renaissance.syntax_tree.ast_finder import find_ast_type
from renaissance.syntax_tree.ast_node import ASTNode
from renaissance.syntax_tree.ast_shower import ASTShower

SHOW_NODE = False


def derive_header_text(language: str, ref_node: ASTNode | None):
    # collect includes #defines  and var decl from the refNode
    header = "\n"
    if ref_node:
        language = ref_node.filename.split(".")[-1]
        offset = min(
            (n.offset for n in ref_node.children if n.is_part_of_translation_unit() and n.ast_type == InclusionDirective),
            default=0,
        )

        header = CPatternFactory.remove_indent(ref_node.content(0, offset))
        header += "\n".join(
            n.text + ";"
            for n in ref_node.children
            if n.is_part_of_translation_unit()
            and isinstance(n.ast_type(), (FunctionDef, VariableDef | TypedefDef, MacroDef))
            and len(find_ast_type(n, CompoundStatement)) == 0
        )
        # and isinstance(n.ast_type, (Declaration, MacroDefinition))
        # and len(find_ast_type(n, CompoundStatement)) == 0
        header += "\n"

    return header, language


class CPatternFactory:
    reserved_function_name = "__rejuvenation__reserved__function__name__"
    reserved_variable_name = "__rejuvenation__reserved__variable__name__"

    def __init__(
        self,
        factory: ASTFactory,
        ref_node: ASTNode | None = None,
        language: str = "c",
    ):
        self.factory = factory
        self.header, self.language = derive_header_text(language, ref_node)

    @staticmethod
    def remove_indent(text: str) -> str:
        split = [len(line) - len(line.lstrip()) for line in text.splitlines() if line.strip()]
        indent = split[0] if split else 0
        return "\n".join([line[indent:] for line in text.splitlines()])

    def create_expression(self, text: str, extra_declarations=None) -> ASTNode:
        if extra_declarations is None:
            extra_declarations = []
        keywords = CPatternFactory._get_keywords_from_text(text)
        keywords = [k for k in keywords if not any(k in ed for ed in extra_declarations)]
        full_text = (
            self.header
            + "\n".join(extra_declarations)
            + "\n"
            + "\n".join(CPatternFactory._to_declaration(keywords))
            + f"\nvoid {CPatternFactory.reserved_function_name}() {{ int {CPatternFactory.reserved_variable_name} = ({text}); }}"
        )
        root = self._create(full_text)
        # return the first expression found in the tree as a ASTNode
        return last(n.children[0] for n in find_ast_type(root.children[-1], ParenthesizedExpression) if n.is_part_of_translation_unit)

    def create_declarations(
        self,
        text: str,
        types=None,
        parameters=None,
        extra_declarations=None,
        declarations=None,
    ):
        if declarations is None:
            declarations = []
        if extra_declarations is None:
            extra_declarations = []
        if parameters is None:
            parameters = []
        if types is None:
            types = []
        keywords = CPatternFactory._get_keywords_from_text(text)
        keywords = [
            k
            for k in keywords
            if not any(k in ed for ed in extra_declarations)
            and not any(k in ed for ed in parameters)
            and not any(k in ed for ed in types)
            and not any(k in ed for ed in declarations)
        ]
        return self._create_body(text, types, [*parameters, *keywords], extra_declarations, Declaration)

    def create_declaration(
        self,
        text: str,
        types=None,
        parameters=None,
        extra_declarations=None,
        declarations=None,
    ) -> ASTNode:
        if declarations is None:
            declarations = []
        if extra_declarations is None:
            extra_declarations = []
        if parameters is None:
            parameters = []
        if types is None:
            types = []
        result = self.create_declarations(text, types, parameters, extra_declarations, declarations)
        assert len(result) > 0, "At least one declaration is expected"
        return result[0]

    def create_statements(
        self,
        text: str,
        types=None,
        extra_declarations=None,
        kind: type[Type] = Type,
    ) -> Sequence[ASTNode]:
        # create a reference for all used variables excluding the specified types
        if extra_declarations is None:
            extra_declarations = []
        if types is None:
            types = []
        parameters = [
            par
            for par in CPatternFactory._get_keywords_from_text(text)
            if par not in types and not any(par in ed for ed in extra_declarations)
        ]
        return self._create_body(text, types, parameters, extra_declarations, kind)

    def create(self, text: str, kind: type[Type] = None) -> ASTNode:
        """Creates an object using the factory from the provided text.
        The object is created by the factory using the provided text and the header of the provided reference node.
        It is up to the user to pick the right node for pattern matching.

        Args:
            text (str): The input text used to create the object.
            kind (str, optional): The kind of the node to be returned. Defaults to None.

        Returns:
            object: The object created by the factory.

        """
        # print(self.header + text)
        root = self.factory.create_from_text(self.header + text, "test." + self.language)
        if kind:
            return first(find_ast_type(root.children[-1], kind))
        return root

    def create_statement(
        self,
        text: str,
        types=None,
        extra_declarations=None,
        kind: str = Type,
    ) -> ASTNode:
        if extra_declarations is None:
            extra_declarations = []
        if types is None:
            types = []
        statements = list(self.create_statements(text, types, extra_declarations, kind))
        assert len(statements) == 1, "Only one statement is expected"
        return statements[0]

    def _create_body(
        self,
        text: str,
        types: Sequence[str],
        parameters: Sequence[str],
        extra_declarations: Sequence[str],
        kind: type[Type],
    ) -> list[ASTNode]:
        full_text = (
            self.header
            + "\n".join(CPatternFactory._to_typedef(types))
            + "\n\n".join(CPatternFactory._to_declaration(parameters))
            + "\n\n".join(extra_declarations)
            + "\n"
            "\nvoid " + CPatternFactory.reserved_function_name + "(){\n" + text + "\n}"
        )
        root = self._create(full_text)

        # from the children of the compound statement that contains the text, get for each child the first
        # node of the specified kind

        body = first(find_ast_type(root.children[-1], CompoundStatement)).children
        return list(n for n in body if n.is_part_of_translation_unit and first(find_ast_type(n, kind)))

    def _create(self, text: str) -> ASTNode:
        atu = self.factory.create_from_text(text, "test." + self.language)
        if SHOW_NODE:
            ASTShower.show_node(atu)
        return atu

    @staticmethod
    def _get_keywords_from_text(text: str) -> Sequence[str]:
        # regex to get keywords that start with one of two dollars followed by a \\w+
        pattern = re.compile(r"\${0,2}[a-zA-Z]\w*")
        return list(k for k in set(re.findall(pattern, text)) if k not in CPPUtils.RESERVED_KEYWORDS)

    @staticmethod
    def _get_dollar_keywords_from_text(text: str) -> Sequence[str]:
        # regex to get keywords that start with one of two dollars followed by a \\w+
        pattern = re.compile(r"\${1,2}[a-zA-Z]\w*")
        return list(set(re.findall(pattern, text)))

    @staticmethod
    def _get_non_dollar_keywords_from_text(text: str) -> Sequence[str]:
        pattern = re.compile(r"[^$][a-zA-Z]\w*")
        return list(set(re.findall(pattern, text)))

    @staticmethod
    def _to_declaration(keywords: Sequence[str], prefix: str = "int ", postfix: str = ";") -> Sequence[str]:
        return [prefix + keyword + postfix for keyword in keywords]

    @staticmethod
    def _to_typedef(keywords: Sequence[str], prefix: str = "typedef int ", postfix: str = ";") -> Sequence[str]:
        return [prefix + keyword + postfix for keyword in keywords]


class CPPPatternFactory(CPatternFactory):
    def __init__(self, factory: ASTFactory, ref_node: ASTNode | None = None):
        super().__init__(factory, ref_node, "cpp")

    def create_constructor_call(self, pattern: str):
        class_and_args = re.match(R"([$\w]+)\(([^)]+)\)", pattern.replace(" ", ""))
        if class_and_args:
            class_name = class_and_args.group(1)
            args = class_and_args.group(2).split(",")
            return self._create_constructor_call(class_name, args)
        return None

    def _create_constructor_call(self, class_name: str, args=None):
        if args is None:
            args = []
        arg_call_string = ",".join(args)
        arg_decl_string = ",".join("int " + arg for arg in args)
        code = f"""
            class {class_name}{{
            public:
                {class_name}({arg_decl_string}) {{}}
            }};
            class derived : public {class_name}{{
            public:
                derived({arg_decl_string}) : {class_name}({arg_call_string}) {{ }}
           }};
        """
        root: ASTNode = self.factory.create_from_text(code, "test." + self.language)
        target_class = root.children[-1]
        # this should yield something like:
        # (TYPE_REF, $var, test.cpp[237:241]): |$var|
        # (CALL_EXPR, , test.cpp[237:266]): |$var($container,$headerCount)|
        #     (DECL_REF_EXPR, $container, test.cpp[242:252]): |$container|
        #     (DECL_REF_EXPR, $headerCount, test.cpp[253:265]): |$headerCount|
        if SHOW_NODE:
            ASTShower.show_node(target_class)
        # search the call expr and the preceding type ref
        call_expr = last(find_ast_type(target_class, Call))
        # include the preceding type ref
        assert isinstance(call_expr, ASTNode), "No call expression found"
        type_ref = call_expr.preceding_sibling
        assert isinstance(type_ref, ASTNode), "No type ref found"
        # return the constrained pattern where the first node must be of type TypeRef

        return call_expr

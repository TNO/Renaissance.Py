import re
from typing import Optional, Sequence

from common.stream import Stream
from .cpp_utils import CPPUtils
from .ast_node import ASTNode
from .ast_shower import ASTShower

from .ast_factory import ASTFactory
from .ast_finder import ASTFinder

SHOW_NODE = False


class CPatternFactory:

    reserved_function_name = "__rejuvenation__reserved__function__name__"
    reserved_variable_name = "__rejuvenation__reserved__variable__name__"

    def __init__(
        self,
        factory: ASTFactory,
        ref_node: Optional[ASTNode] = None,
        language: str = "c",
    ):
        self.factory = factory
        # collect includes #defines  and var decl from the refNode
        if ref_node:
            offset = (
                Stream(ref_node.children)
                .filter(lambda n : n.is_part_of_translation_unit)
                .filter(
                    lambda c: not ASTFinder.matches_kind(
                        c, "(?i)Macro.*|Inclusion_?Directive"
                    )
                )
                .map(lambda n: n.offset)
                .reduce(min)
                .or_else(0)
            )
            self.language = ref_node.filename.split(".")[-1]

            self.header = (
                    CPatternFactory.remove_indent(ref_node.content(0, offset)) + "\n"
            )
            self.header += (
                Stream(ref_node.children)
                .filter(ASTNode.is_part_of_translation_unit)
                .filter(
                    lambda c: ASTFinder.matches_kind(
                        c, "(?i)(Function|Var|Typedef)_?Decl"
                    )
                )
                .filter(
                    lambda c: ASTFinder.find_kind(c, "(?i)Compound_?Stmt").count() == 0
                )
                .map(lambda c: c.text + ";")
                .collect(lambda n: "\n".join(n))
                + "\n"
            )
        else:
            self.language = language
            self.header = ""
        # print(self.header)

    @staticmethod
    def remove_indent(text: str) -> str:
        split = [len(l) - len(l.lstrip()) for l in text.splitlines() if l.strip()]
        indent = split[0] if split else 0
        return "\n".join([line[indent:] for line in text.splitlines()])

    def create_expression(
        self, text: str, extra_declarations: Sequence[str] = []
    ) -> ASTNode:
        keywords = CPatternFactory._get_keywords_from_text(text)
        keywords = [
            k for k in keywords if not any(k in ed for ed in extra_declarations)
        ]
        full_text = (
            self.header
            + "\n".join(extra_declarations)
            + "\n"
            + "\n".join(CPatternFactory._to_declaration(keywords))
            + f"\nvoid {CPatternFactory.reserved_function_name}() {{ int {CPatternFactory.reserved_variable_name} = ({text}); }}"
        )
        root = self._create(full_text)
        # return the first expression found in the tree as a ASTNode
        return (
            ASTFinder.find_kind(root.children[-1], "(?i)PAREN_?EXPR")
            .filter(ASTNode.is_part_of_translation_unit)
            .find_last()
            .get()
            .children[0]
        )

    def create_declarations(
        self,
        text: str,
        types: Sequence[str] = [],
        parameters: Sequence[str] = [],
        extra_declarations: Sequence[str] = [],
        declarations: Sequence[str] = [],
    ):
        keywords = CPatternFactory._get_keywords_from_text(text)
        keywords = [
            k
            for k in keywords
            if not any(k in ed for ed in extra_declarations)
            and not any(k in ed for ed in parameters)
            and not any(k in ed for ed in types)
            and not any(k in ed for ed in declarations)
        ]
        return self._create_body(
            text, types, [*parameters, *keywords], extra_declarations, "(?i).*DECL.*"
        )

    def create_declaration(
        self,
        text: str,
        types: Sequence[str] = [],
        parameters: Sequence[str] = [],
        extra_declarations: Sequence[str] = [],
        declarations: Sequence[str] = [],
    ) -> ASTNode:
        result = self.create_declarations(
            text, types, parameters, extra_declarations, declarations
        )
        assert len(result) > 0, "At least one declaration is expected"
        return result[0]

    def create_statements(
        self,
        text: str,
        types: Sequence[str] = [],
        extra_declarations: Sequence[str] = [],
        kind: str = ".*",
    ) -> Sequence[ASTNode]:
        # create a reference for all used variables excluding the specified types
        parameters = [
            par
            for par in CPatternFactory._get_keywords_from_text(text)
            if not par in types and not any(par in ed for ed in extra_declarations)
        ]
        return self._create_body(text, types, parameters, extra_declarations, kind)

    def create(self, text: str, kind: Optional[str] = None) -> ASTNode:
        """
        Creates an object using the factory from the provided text.
        The object is created by the factory using the provided text and the header of the provided reference node.
        It is up to the user to pick the right node for pattern matching

        Args:
            text (str): The input text used to create the object.

        Returns:
            object: The object created by the factory.
        """
        # print(self.header + text)
        root = self.factory.create_from_text(
            self.header + text, "test." + self.language
        )
        if kind:
            return ASTFinder.find_kind(root.children[-1], kind).find_first().get()
        return root

    def create_statement(
        self,
        text: str,
        types: Sequence[str] = [],
        extra_declarations: Sequence[str] = [],
        kind: str = ".*",
    ) -> ASTNode:
        statements = list(self.create_statements(text, types, extra_declarations, kind))
        assert len(statements) == 1, "Only one statement is expected"
        return statements[0]

    def _create_body(
        self,
        text: str,
        types: Sequence[str],
        parameters: Sequence[str],
        extra_declarations: Sequence[str],
        kind: str,
    ) -> list[ASTNode]:
        full_text = (
            self.header + "\n".join(CPatternFactory._to_typedef(types)) + "\n"
            "\n".join(CPatternFactory._to_declaration(parameters)) + "\n"
            "\n".join(extra_declarations) + "\n"
            "\nvoid " + CPatternFactory.reserved_function_name + "(){\n" + text + "\n}"
        )
        root = self._create(full_text)

        # from the children of the compound statement that contains the text, get for each child the first
        # node of the specified kind

        return (
            Stream(
                ASTFinder.find_kind(root.children[-1], "(?i)COMPOUND_?STMT")
                .find_first()
                .get()
                .children
            )
            .filter(ASTNode.is_part_of_translation_unit)
            .map(lambda n: ASTFinder.find_kind(n, kind).find_first().get())
            .to_list()
        )

    def _create(self, text: str) -> ASTNode:
        atu = self.factory.create_from_text(text, "test." + self.language)
        if SHOW_NODE:
            ASTShower.show_node(atu)
        return atu

    @staticmethod
    def _get_keywords_from_text(text: str) -> Sequence[str]:
        # regex to get keywords that start with one of two dollars followed by a \\w+
        pattern = re.compile(r"\${0,2}[a-zA-Z]\w*")
        return list(
            k
            for k in set(re.findall(pattern, text))
            if k not in CPPUtils.RESERVED_KEYWORDS
        )

    @staticmethod
    def _get_dollar_keywords_from_text(text: str) -> Sequence[str]:
        # regex to get keywords that start with one of two dollars followed by a \\w+
        pattern = re.compile(r"\${1,2}[a-zA-Z]\w*")
        return list(set(re.findall(pattern, text)))

    @staticmethod
    def _get_non_dollar_keywords_from_text(
        text: str, prefix: str = "void* ", postfix: str = ";"
    ) -> Sequence[str]:
        pattern = re.compile(r"[^\$][a-zA-Z]\w*")
        return list(set(re.findall(pattern, text)))

    @staticmethod
    def _to_declaration(
        keywords: Sequence[str], prefix: str = "int ", postfix: str = ";"
    ) -> Sequence[str]:
        return [prefix + keyword + postfix for keyword in keywords]

    @staticmethod
    def _to_typedef(
        keywords: Sequence[str], prefix: str = "typedef int ", postfix: str = ";"
    ) -> Sequence[str]:
        return [prefix + keyword + postfix for keyword in keywords]


class CPPPatternFactory(CPatternFactory):

    def __init__(self, factory: ASTFactory, ref_node: Optional[ASTNode] = None):
        super().__init__(factory, ref_node, "cpp")

    def create_constructor_call(self, pattern: str):
        class_and_args = re.match(R"([$\w]+)\(([^)]+)\)", pattern.replace(" ", ""))
        if class_and_args:
            class_name = class_and_args.group(1)
            args = class_and_args.group(2).split(",")
        # TODO: implement else or use default values for class_name and args
        return self._create_constructor_call(class_name, args)

    def _create_constructor_call(self, class_name: str, args: Sequence[str] = []):
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
        call_expr = (
            ASTFinder.find_kind(target_class, "CallExpr")
            .peek(lambda n: ASTShower.show_node(n))
            .find_last()
            .get()
        )
        # include the preceding typeref
        assert isinstance(call_expr, ASTNode), "No call expression found"
        type_ref = call_expr.preceding_sibling
        assert isinstance(type_ref, ASTNode), "No type ref found"
        # return the constrained pattern where the first node must be of type TypeRef
        # return ConstrainedPattern([type_ref, call_expr], lambda m: ASTFinder.matches_kind(m.src_nodes[0], 'TypeRef'))
        return call_expr


if __name__ == "__main__":
    print(
        CPatternFactory._get_dollar_keywords_from_text(
            "struct $type;struct $name; $type a = $name; int b = 4; $$x = $$y"
        )
    )
    # factory = ASTFactory(ClangASTNode)
    # patternFactory = CPatternFactory(factory)
    # ASTShower.show_node(patternFactory.create_expression('a == $hallo'))

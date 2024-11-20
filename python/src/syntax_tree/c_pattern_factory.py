import re
from typing import Generic, Optional, Sequence

from common.stream import Stream
from .ast_node import ASTNode, ASTNodeType
from .ast_shower import ASTShower

from .ast_factory import ASTFactory
from .ast_finder import ASTFinder
SHOW_NODE = False

class CPatternFactory(Generic[ASTNodeType]):

    reserved_name = '__rejuvenation__reserved__'

    def __init__(self, factory: ASTFactory[ASTNodeType], refNode: Optional[ASTNode] = None , language: str = 'c'):
        self.factory = factory
        #collect includes #defines  and var decl from the refNode
        if refNode:
            offset = Stream(refNode.get_children()).\
                filter(ASTNode.is_part_of_translation_unit).\
                filter(lambda c: not ASTFinder.matches_kind(c,'(?i)Macro.*|Inclusion_?Directive')).\
                peek(lambda c:  print("-->"+c.get_kind())).\
                map(ASTNode.get_start_offset).reduce(min).or_else(0)
            self.language = refNode.get_containing_filename().split('.')[-1]

            self.header = CPatternFactory.remove_indent(refNode.get_content(0, offset)) + '\n'
            self.header+= Stream(refNode.get_children()).\
                filter(ASTNode.is_part_of_translation_unit).\
                filter(lambda c: ASTFinder.matches_kind(c,'(?i)(Function|Var|Typedef)_?Decl')).\
                filter(lambda c: ASTFinder.find_kind(c,'(?i)Compound_?Stmt').count()==0).\
                map(lambda c: c.get_text()+';').\
                collect(lambda n: '\n'.join(n)) +'\n'
        else:
            self.language = language
            self.header = ''
        print(self.header)

    @staticmethod
    def remove_indent(text):
        split = [ len(l)-len(l.lstrip()) for l in  text.splitlines() if l.strip()]
        indent = split[0] if split else 0
        return '\n'.join([line[indent:] for line in text.splitlines()])

    def create_expression(self, text:str) -> ASTNodeType:
        keywords = CPatternFactory._get_keywords_from_text(text)
        fullText = self.header + '\n'.join(CPatternFactory._to_declaration(keywords)) + f'\nint {CPatternFactory.reserved_name} = ({text});'
        root =  self._create( fullText)
        #return the first expression found in the tree as a ASTNode
        return  ASTFinder.find_kind(root, '(?i)PAREN_?EXPR').find_last().get().get_children()[0]

    def create_declarations(self, text:str, types: Sequence[str] = [] , parameters: Sequence[str] = [], extra_declarations: Sequence[str] = []):
        return self._create_body(text, types, parameters, extra_declarations)

    def create_declaration(self, text:str, types: Sequence[str] = [] , parameters: Sequence[str] = [], extra_declarations: Sequence[str] = []):
        declarations = list(self.create_declarations(text, types, parameters))
        assert len(declarations) == 1, "Only one declaration is expected"
        return declarations[0]
    
    def create_statements(self, text:str, types: Sequence[str] = [], extra_declarations: Sequence[str] = []):
        # create a reference for all used variables excluding the specified types
        parameters = [ par for par in CPatternFactory._get_keywords_from_text(text) if not par in types and not any(par in ed for ed in extra_declarations)]
        return self._create_body(text, types, parameters, extra_declarations)

    def create(self, text:str):
        """
        Creates an object using the factory from the provided text.
        The object is created by the factory using the provided text and the header of the provided reference node.
        It is up to the user to pick the right node for pattern matching

        Args:
            text (str): The input text used to create the object.

        Returns:
            object: The object created by the factory.
        """
        print(self.header + text)
        return self.factory.create_from_text(self.header + text,  'test.' + self.language)


    def create_statement(self, text:str, types: Sequence[str] = [], extra_declarations: Sequence[str] = []):
        statements = list(self.create_statements(text, types, extra_declarations))
        assert len(statements) == 1, "Only one statement is expected"
        return statements[0]
    
    def _create_body(self, text, types, parameters, extra_declarations):
        fullText = \
            self.header+\
            '\n'.join(CPatternFactory._to_typedef(types)) +'\n'\
            '\n'.join(CPatternFactory._to_declaration(parameters)) +'\n'\
            '\n'.join(extra_declarations) +'\n'\
             '\nvoid '+CPatternFactory.reserved_name+'(){\n' +text +'\n}'
        root =  self._create(fullText)
        #return the first expression found in the tree as a ASTNode
        return  ASTFinder.find_kind(root, '(?i)COMPOUND_?STMT').find_first().get().get_children()

    def _create(self, text:str)-> ASTNodeType:  
        atu =  self.factory.create_from_text( text, 'test.' + self.language)
        if SHOW_NODE: ASTShower.show_node(atu)
        return atu

    @staticmethod
    def _get_keywords_from_text(text:str) -> Sequence[str]:
        # regex to get keywords that start with one of two dollars followed by a \\w+
        pattern = re.compile(r'\${0,2}[a-zA-Z]\w*')
        return list(set(re.findall(pattern, text)))

    @staticmethod
    def _get_dollar_keywords_from_text(text:str) -> Sequence[str]:
        # regex to get keywords that start with one of two dollars followed by a \\w+
        pattern = re.compile(r'\${1,2}[a-zA-Z]\w*')
        return list(set(re.findall(pattern, text)))

    @staticmethod
    def _get_non_dollar_keywords_from_text(text:str, prefix: str ='void* ', postfix: str =';') -> Sequence[str]:
        pattern = re.compile(r'[^\$][a-zA-Z]\w*')
        return list(set(re.findall(pattern, text)))

    @staticmethod
    def _to_declaration(keywords:Sequence[str], prefix: str ='int ', postfix: str =';') -> Sequence[str]:
        return  [ prefix + keyword + postfix for keyword in keywords]

    @staticmethod
    def _to_typedef(keywords:Sequence[str], prefix: str ='typedef int ', postfix: str =';') -> Sequence[str]:
        return  [ prefix + keyword + postfix for keyword in keywords]


class CPPPatternFactory(CPatternFactory):

    def __init__(self, factory: ASTFactory, refNode: Optional[ASTNode] = None):
        super().__init__(factory, refNode, 'cpp')

if __name__ == "__main__":
    print(CPatternFactory._get_dollar_keywords_from_text('struct $type;struct $name; $type a = $name; int b = 4; $$x = $$y'))
    # factory = ASTFactory(ClangASTNode)
    # patternFactory = CPatternFactory(factory)
    # ASTShower.show_node(patternFactory.create_expression('a == $hallo'))




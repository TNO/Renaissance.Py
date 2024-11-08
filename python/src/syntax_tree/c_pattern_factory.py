import re

from syntax_tree.ast_shower import ASTShower

from .ast_factory import ASTFactory
from .ast_finder import ASTFinder
SHOW_NODE = False
class CPatternFactory:

    reserved_name = '__rejuvenation__reserved__'

    def __init__(self, factory: ASTFactory, language: str = 'c'):
        self.factory = factory
        self.language = language

    def create_expression(self, text:str):
        keywords = CPatternFactory._get_keywords_from_text(text)
        fullText = '\n'.join(CPatternFactory._to_declaration(keywords)) + f'\nint {CPatternFactory.reserved_name} = ({text});'
        root =  self._create( fullText)
        #return the first expression found in the tree as a ASTNode
        return ASTFinder.find_kind(root, '(?i)PAREN_?EXPR').find_first().get().get_children()[0]

    def create_declarations(self, text:str, types: list[str] = [] , parameters: list[str] = [], extra_declarations: list[str] = []):
        return self._create_body(text, types, parameters, extra_declarations)

    def create_declaration(self, text:str, types: list[str] = [] , parameters: list[str] = [], extra_declarations: list[str] = []):
        declarations = list(self.create_declarations(text, types, parameters))
        assert len(declarations) == 1, "Only one declaration is expected"
        return declarations[0]
    
    def create_statements(self, text:str, types: list[str] = [], extra_declarations: list[str] = []):
        # create a reference for all used variables excluding the specified types
        parameters = [ par for par in CPatternFactory._get_keywords_from_text(text) if not par in types and not any(par in ed for ed in extra_declarations)]
        return self._create_body(text, types, parameters, extra_declarations)

    def create_statement(self, text:str, types: list[str] = [], extra_declarations: list[str] = []):
        statements = list(self.create_statements(text, types, extra_declarations))
        assert len(statements) == 1, "Only one statement is expected"
        return statements[0]
    
    def _create_body(self, text, types, parameters, extra_declarations):
        fullText = \
            '\n'.join(CPatternFactory._to_typedef(types)) +'\n'\
            '\n'.join(CPatternFactory._to_declaration(parameters)) +'\n'\
            '\n'.join(extra_declarations) +'\n'\
             '\nvoid '+CPatternFactory.reserved_name+'(){\n' +text +'\n}'
        root =  self._create(fullText)
        #return the first expression found in the tree as a ASTNode
        return  ASTFinder.find_kind(root, '(?i)COMPOUND_?STMT').find_first().get().get_children()

    def _create(self, text:str):  
        atu =  self.factory.create_from_text( text, 'test.' + self.language)
        if SHOW_NODE: ASTShower.show_node(atu)
        return atu

    @staticmethod
    def _get_keywords_from_text(text:str) -> list[str]:
        # regex to get keywords that start with one of two dollars followed by a \\w+
        pattern = re.compile(r'\${0,2}[a-zA-Z]\w*')
        return list(set(re.findall(pattern, text)))

    @staticmethod
    def _get_dollar_keywords_from_text(text:str) -> list[str]:
        # regex to get keywords that start with one of two dollars followed by a \\w+
        pattern = re.compile(r'\${1,2}[a-zA-Z]\w*')
        return list(set(re.findall(pattern, text)))

    @staticmethod
    def _get_non_dollar_keywords_from_text(text:str, prefix: str ='void* ', postfix: str =';') -> list[str]:
        pattern = re.compile(r'[^\$][a-zA-Z]\w*')
        return list(set(re.findall(pattern, text)))

    @staticmethod
    def _to_declaration(keywords:list[str], prefix: str ='int ', postfix: str =';') -> list[str]:
        return  [ prefix + keyword + postfix for keyword in keywords]

    @staticmethod
    def _to_typedef(keywords:list[str], prefix: str ='typedef int ', postfix: str =';') -> list[str]:
        return  [ prefix + keyword + postfix for keyword in keywords]


class CPPPatternFactory(CPatternFactory):

    def __init__(self, factory: ASTFactory):
        super().__init__(factory, 'cpp')

if __name__ == "__main__":
    print(CPatternFactory._get_dollar_keywords_from_text('struct $type;struct $name; $type a = $name; int b = 4; $$x = $$y'))
    # factory = ASTFactory(ClangASTNode)
    # patternFactory = CPatternFactory(factory)
    # ASTShower.show_node(patternFactory.create_expression('a == $hallo'))





from common import Rewriter
from .match_finder import PatternMatch
from .ast_node import ASTNode

class ASTRewriter():
    def __init__(self, atu: ASTNode, encoding='utf-8') -> None:
        assert atu == atu.root,  "ASTRewriter can only be used for the root node"
        bytes_array = atu.get_binary_file_content()
        self.__encoding = encoding
        self.__rewriter = Rewriter(bytes_array)
        self.__filename = atu.get_containing_filename()
    
    def replace_bytes(self, start: int, end: int, new_content: str):
        """
        Replaces the content in the specified range with new content.

        Args:
            start (int): The starting index of the range to be replaced.
            end (int): The ending index of the range to be replaced.
            new_content (str): The new content to insert in the specified range.
        """
        enc = self.__encoding
        self.__rewriter.replace(start, end, new_content.encode(enc))    

    def get_filename(self) -> str:
        return self.__filename
    
    def replace(self, new_content:str, target: ASTNode|list[ASTNode]|PatternMatch, include_whitespace: bool = False, include_comments: bool = False):
        new_content, node_list = ASTRewriter._prepare_replacement_content(new_content, target)
        self.__replace(new_content, node_list, include_whitespace, include_comments)

    def remove(self, target: ASTNode|list[ASTNode]|PatternMatch, include_whitespace: bool = False, include_comments: bool = False):
        new_content, node_list = ASTRewriter._prepare_replacement_content('', target)
        self.__replace(new_content, node_list, include_whitespace, include_comments)

    def insert_before(self,new_content:str, target: ASTNode|list[ASTNode]|PatternMatch, include_whitespace: bool = True, include_comments: bool = True):
        new_content, node_list = ASTRewriter._prepare_replacement_content(new_content, target)
        self.__insert(new_content, True, node_list, include_whitespace, include_comments)

    def insert_after(self,new_content:str, target: ASTNode|list[ASTNode]|PatternMatch, include_whitespace: bool = True, include_comments: bool = True):
        new_content, node_list = ASTRewriter._prepare_replacement_content(new_content, target)
        self.__insert(new_content, False, node_list, include_whitespace, include_comments)

    def __insert(self,new_content:str, before:bool, nodes: list[ASTNode], include_whitespace: bool = False, include_comments: bool = False):
        if not nodes:
            return  
        offset = nodes[0].get_start_offset()
        content = self.__rewriter.content
        indent = ASTRewriter._get_indent(content, offset)
        spaces = ' '*indent
        # if flattened_nodes[-1] has a new line after white space then we need to add a new line:
        ext_start_offset, ext_end_offset =  self.correct_for_comments_and_whitespace(include_whitespace, include_comments, nodes)
        insert_new_line = '\n' if content[ext_end_offset] in b'\n' else ''
        #indent the new content except the first line
        new_content = new_content.replace('\n', '\n' + spaces)
        if before:
            self.replace_bytes( ext_start_offset, ext_start_offset, new_content + insert_new_line + spaces)
        else:
            self.replace_bytes( ext_end_offset,  ext_end_offset, insert_new_line + spaces + new_content)

    def __replace(self, new_content: str, nodes: list[ASTNode], include_whitespace: bool = False, include_comments: bool = False):
        """
        Replaces the content of the given node(s) with new content.

        Args:
            nodes (list[ASTNode]): The nodes whose content is to be replaced.
            new_content (str): The new content to insert in the specified range.
        """
        if not nodes:
            return  
        start_offset, end_offset = self.correct_for_comments_and_whitespace(include_whitespace, include_comments, nodes)
        self.replace_bytes(start_offset, end_offset, new_content) 

    
    def apply_to_string(self) -> str:
        return self.__rewriter.apply().decode(self.__encoding)

    def apply(self) -> bytes:
        return self.__rewriter.apply()

    def correct_for_comments_and_whitespace(self, include_whitespace, include_comments, nodes):
        start_offset = nodes[0].get_start_offset()
        end_offset = nodes[-1].get_end_offset()
        if include_comments:
            precedingNode = nodes[0].get_preceding_sibling()
            parent = nodes[0].get_parent()
            start_comment_location = precedingNode.get_end_offset() if precedingNode else parent.get_start_offset() if parent else 0
            extended_location = ASTRewriter._get_comment_location(start_comment_location, start_offset,self.__rewriter.content)
            if extended_location != (-1, -1):
                start_offset = extended_location[0]
            nextSibling = nodes[-1].get_next_sibling()
            end_comment_location = nextSibling.get_start_offset() if nextSibling else parent.get_end_offset() if parent else len(self.__rewriter.content)    
            location_after_comment = ASTRewriter._get_comment_after_location(end_offset, end_comment_location, self.__rewriter.content)
            if location_after_comment != (-1, -1):
                end_offset = location_after_comment[1]
        if include_whitespace:
            end_offset = ASTRewriter._extend_with_whitespace(end_offset, self.__rewriter.content)
        return start_offset,end_offset  

    @staticmethod
    def _get_indent(byte_array: bytes, offset:int) -> int:
        idx = offset-1
        while idx >=0:
            char = byte_array[idx]
            if char in b' \t':  
                idx -= 1
            else:
                break            
        return offset - idx - 1

    @staticmethod
    def _get_comment_location(start_offset: int,stop_offset: int, content: bytes) -> tuple[int,int]:
        """ get the location of the comment before the location, but after the stop_location
            a comment is a line that starts with // or a block that starts with /* and ends with */
            or a line that starts with #
        """
        #search last occurrence of //, /*, # in a byte array
        comment_start = content.rfind(b'//', start_offset, stop_offset)
        if comment_start != -1:
            comment_end = ASTRewriter._get_end_of_line(content, comment_start) 
            return comment_start,  comment_end
        comment_start = content.rfind(b'/*', start_offset, stop_offset)
        if comment_start != -1:
            comment_end = content.find(b'*/', comment_start, stop_offset)   
            if comment_end != -1:
                comment_end += len('*/')
            return comment_start,  comment_end
        comment_start = content.rfind(b'#', start_offset, stop_offset)
        if comment_start != -1 :
            comment_end =ASTRewriter._get_end_of_line(content, comment_start)
            return comment_start,  comment_end
        return -1,-1

    @staticmethod
    def _extend_with_whitespace(start_offset: int, content: bytes) -> int:
        end_location = ASTRewriter._get_end_of_line(content, start_offset)
        text = content[start_offset:end_location]
        for byt in text:
            if byt not in  b' \t':
                return start_offset
        return end_location

    @staticmethod
    def _get_comment_after_location(start_offset: int,  end_offset: int, content: bytes) -> tuple[int,int]:
        """ get the location of the comment before the location, but after the stop_location
            a comment is a line that starts with // or a block that starts with /* and ends with */
            or a line that starts with #
        """
        line_end_offset = ASTRewriter._get_end_of_line(content, start_offset)
        if line_end_offset == -1:
            line_end_offset = len(content)        
        comment_start = content.find(b'//', start_offset, line_end_offset)
        if comment_start == -1:
            comment_start = content.rfind(b'#', start_offset, line_end_offset)
        if comment_start != -1:
            return comment_start,  line_end_offset
        comment_start = content.rfind(b'/*', start_offset, line_end_offset)
        if comment_start != -1:
            # a block comment must start on the same line but doesn't have to finish on the same line
            comment_end = content.find(b'*/', comment_start, end_offset)   
            if comment_end != -1:
                comment_end += len('*/')
            return comment_start,  comment_end
        return -1,-1

    @staticmethod
    def _get_end_of_line(content: bytes, start: int):
        location = content.find(b'\n', start)
        if location == -1:
            return len(content)
        return location
    
    @staticmethod
    def _prepare_replacement_content(new_content, target):
        node_list = []
        if isinstance(target, PatternMatch):
            new_content = target.compose_replacement(new_content)
            node_list = target.src_nodes
        else:
            node_list = [target] if isinstance(target, ASTNode) else target
        return new_content,node_list

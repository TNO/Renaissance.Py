from enum import Enum
import re
import sys
from typing import Optional, Sequence
from common import Rewriter
from .match_finder import PatternMatch
from .ast_finder import ASTFinder
from .ast_node import ASTNode
from .text_utils import TextUtils


class _RewriteActionType(Enum):
    REPLACE = 1
    INSERT_BEFORE = 2
    INSERT_AFTER = 3
    REMOVE = 4


DEFAULT_INDENT = 4


class ASTRewriter:
    def __init__(
        self,
        nodes: ASTNode | Sequence[ASTNode],
        encoding: str = sys.getfilesystemencoding(),
        correct_indent: bool = True,
    ) -> None:
        self.__rewrites = _RewriteActions(nodes, encoding, correct_indent=correct_indent)
        self.__filename = (
            nodes[0].root.filename
            if isinstance(nodes, Sequence)
            else nodes.root.filename
        )

    def get_filename(self) -> str:
        return self.__filename

    def replace(
        self,
        new_content: str,
        target: ASTNode | Sequence[ASTNode] | PatternMatch | Sequence[PatternMatch],
        include_whitespace: bool = True,
        include_comments: bool = True,
    ):
        self.__rewrites.add(
            _RewriteActionType.REPLACE,
            target,
            new_content,
            include_whitespace,
            include_comments,
        )

    def remove(
        self,
        target: ASTNode | Sequence[ASTNode] | PatternMatch | Sequence[PatternMatch],
        include_whitespace: bool = True,
        include_comments: bool = True,
    ):
        self.__rewrites.add(
            _RewriteActionType.REMOVE, target, "", include_whitespace, include_comments
        )

    def insert_before(
        self,
        new_content: str,
        target: ASTNode | Sequence[ASTNode] | PatternMatch | Sequence[PatternMatch],
        include_whitespace: bool = True,
        include_comments: bool = True,
    ):
        self.__rewrites.add(
            _RewriteActionType.INSERT_BEFORE,
            target,
            new_content,
            include_whitespace,
            include_comments,
        )

    def insert_after(
        self,
        new_content: str,
        target: ASTNode | Sequence[ASTNode] | PatternMatch | Sequence[PatternMatch],
        include_whitespace: bool = True,
        include_comments: bool = True,
    ):
        self.__rewrites.add(
            _RewriteActionType.INSERT_AFTER,
            target,
            new_content,
            include_whitespace,
            include_comments,
        )

    def apply_to_string(self) -> str:
        return self.__rewrites.apply_to_string()

    def apply(self) -> bytes:
        if len(self.__rewrites.rewrites) == 0:
            return self.__rewrites.content
        return self.__rewrites.apply()

    def has_changed(self) -> bool:
        return len(self.__rewrites.rewrites) > 0

    @staticmethod
    def _get_comment_location(
        start_offset: int, stop_offset: int, content: bytes
    ) -> tuple[int, int]:
        return _RewriteActions._get_comment_location(start_offset, stop_offset, content)


class _RewriteAction:
    """
    Data container for  a rewrite action to be applied later on to the AST.
    """

    def __init__(
        self,
        action: _RewriteActionType,
        target: ASTNode | Sequence[ASTNode] | PatternMatch | Sequence[PatternMatch],
        replacement: str,
        include_whitespace: bool,
        include_comments: bool,
    ) -> None:
        self.action = action
        self.target = target
        self.replacement = replacement
        self.nodes = self._get_nodes(target)
        self.include_whitespace = include_whitespace
        self.include_comments = include_comments

    @staticmethod
    def _get_nodes(
        target: ASTNode | Sequence[ASTNode] | PatternMatch | Sequence[PatternMatch],
    ) -> Sequence[ASTNode]:
        if isinstance(target, ASTNode):
            return [target]
        if isinstance(target, PatternMatch):
            return target.nodes
        assert isinstance(
            target, Sequence
        ), "type of target violates its type requirements " + type(target).__name__
        if len(target) > 0:
            if isinstance(target[0], ASTNode):
                return [n for n in target if isinstance(n, ASTNode)]
            if isinstance(target[-1], PatternMatch):
                return target[-1].src_nodes
        return []


class _RewriteActions:
    """
    Data container for a list of rewrite actions to be applied later on to the AST.
    """

    def __init__(
        self,
        nodes: ASTNode | Sequence[ASTNode] | PatternMatch,
        encoding: str,
        correct_indent: bool,
        rewrites: Optional[list[_RewriteAction]] = None,
    ) -> None:
        self.rewrites: list[_RewriteAction] = rewrites if rewrites else []
        self.nodes = (
            nodes
            if isinstance(nodes, Sequence)
            else nodes.src_nodes if isinstance(nodes, PatternMatch) else [nodes]
        )
        self.encoding = encoding
        self.content = self.nodes[0].root.binary_file_content()[
            self.nodes[0].offset: self.nodes[-1].extended_end_offset
        ]
        self.correct_indent = correct_indent

    def add(
        self,
        action: _RewriteActionType,
        target: ASTNode | Sequence[ASTNode] | PatternMatch | Sequence[PatternMatch],
        replacement: str,
        include_whitespace: bool,
        include_comments: bool,
    ):
        rewrite = _RewriteAction(
            action, target, replacement, include_whitespace, include_comments
        )
        self.add_rewrite(rewrite)

    def add_rewrite(self, rewrite: _RewriteAction):
        self.rewrites.append(rewrite)

    def apply(self) -> bytes:
        rewriter = Rewriter(self.content[:])

        for rewrite in self.rewrites:
            # skip nested rewrites as they are handled recursively by the parent rewrite
            # except for if the rewrite node is the root node
            if any(
                self.__is_ancestor_in_nodes(n)
                for n in rewrite.nodes
                if n != self.nodes[0]
            ):
                continue
            new_content, nodelist = self.__prepare_replacement_content(
                rewrite.replacement, rewrite.target
            )
            if rewrite.action == _RewriteActionType.REPLACE:
                self.__replace(
                    rewriter,
                    new_content,
                    nodelist,
                    rewrite.include_whitespace,
                    rewrite.include_comments,
                )
            elif rewrite.action == _RewriteActionType.INSERT_BEFORE:
                self.__insert(
                    rewriter,
                    new_content,
                    True,
                    nodelist,
                    rewrite.include_whitespace,
                    rewrite.include_comments,
                )
            elif rewrite.action == _RewriteActionType.INSERT_AFTER:
                self.__insert(
                    rewriter,
                    new_content,
                    False,
                    nodelist,
                    rewrite.include_whitespace,
                    rewrite.include_comments,
                )
            elif rewrite.action == _RewriteActionType.REMOVE:
                self.__remove(
                    rewriter,
                    nodelist,
                    rewrite.include_whitespace,
                    rewrite.include_comments,
                )
        return rewriter.apply()

    def apply_to_string(self) -> str:
        return self.apply().decode(self.encoding)

    def __is_ancestor_in_nodes(self, node: ASTNode) -> bool:
        """
        Check if the given node is a descendant of any nodes in the rewrite list.

        Args:
            node (ASTNode): The node to check.

        Returns:
            bool: True if the node is a descendant of any nodes in the rewrite list, False otherwise.
        """
        return any(
            node != rewrite_node and node.is_descendant_of(rewrite_node)
            for rewrite in self.rewrites
            for rewrite_node in rewrite.nodes
        )

    def __replace(
        self,
        rewriter: Rewriter,
        new_content: str,
        nodes: Sequence[ASTNode],
        include_whitespace: bool,
        include_comments: bool,
    ):
        """
        Replaces the content of the given node(s) with new content.

        Args:
            nodes (Sequence[ASTNode]): The nodes whose content is to be replaced.
            new_content (str): The new content to insert in the specified range.
        """
        if not nodes:
            return
        start_offset, end_offset = (
            _RewriteActions.__correct_for_comments_and_whitespace(
                self.nodes[0].offset,
                self.content,
                include_whitespace,
                include_comments,
                nodes,
            )
        )
        # start_offset =nodes[0].get_start_offset()
        # end_offset =nodes[-1].get_start_offset()+nodes[-1].get_length()+1
        indent = len(nodes[0].indent)
        if self.correct_indent:
            new_content = TextUtils.shift_right(new_content, indent, start_line=1)
        self.__replace_bytes(rewriter, start_offset, end_offset, new_content)

    def __remove(
        self,
        rewriter: Rewriter,
        nodes: Sequence[ASTNode],
        include_whitespace: bool = False,
        include_comments: bool = False,
    ):
        """
        Removes a list of AST nodes from the content, optionally including surrounding whitespace and comments.

        Args:
            nodes (Sequence[ASTNode]): The list of AST nodes to remove.
            include_whitespace (bool, optional): Whether to include surrounding whitespace in the removal. Defaults to False.
            include_comments (bool, optional): Whether to include surrounding comments in the removal. Defaults to False.

        Returns:
            None
        """
        if not nodes:
            return
        indent = len(nodes[0].indent)
        start_offset, end_offset = (
            _RewriteActions.__correct_for_comments_and_whitespace(
                self.nodes[0].offset,
                self.content,
                include_whitespace,
                include_comments,
                nodes,
            )
        )
        # remove the indent in front of it
        start_offset -= indent
        # remove the line if it is empty
        if (
            start_offset > 0
            and self.content[start_offset - 1] == ord("\n")
            and self.content[end_offset] == ord("\n")
        ):
            start_offset -= 1
        self.__replace_bytes(rewriter, start_offset, end_offset, "")

    def __insert(
        self,
        rewriter: Rewriter,
        new_content: str,
        before: bool,
        nodes: Sequence[ASTNode],
        include_whitespace: bool,
        include_comments: bool,
    ):
        if not nodes:
            return
        content = self.content
        indent = TextUtils.get_spaces_before(content, nodes[0].offset)
        spaces = " " * indent
        # if flattened_nodes[-1] has a new line after white space then we need to add a new line:
        ext_start_offset, ext_end_offset = (
            _RewriteActions.__correct_for_comments_and_whitespace(
                self.nodes[0].offset,
                self.content,
                include_whitespace,
                include_comments,
                nodes,
            )
        )
        white_space = (
            ""
            if not include_whitespace
            else "\n" + spaces if content[ext_end_offset] in b"\n" else spaces
        )
        # indent the new content except the first line
        new_content = TextUtils.shift_right(new_content, indent, start_line=1)

        if before:
            self.__replace_bytes(
                rewriter, ext_start_offset, ext_start_offset, new_content + white_space
            )
        else:
            self.__replace_bytes(
                rewriter, ext_end_offset, ext_end_offset, white_space + new_content
            )

    def __replace_bytes(
        self, rewriter: Rewriter, start: int, end: int, new_content: str
    ) -> None:
        """
        Replaces the content in the specified range with new content.

        Args:
            start (int): The starting index of the range to be replaced.
            end (int): The ending index of the range to be replaced.
            new_content (str): The new content to insert in the specified range.
        """
        rewriter.replace(start, end, new_content.encode(self.encoding))

    def __compose_replacement(
        self, replacement: str, matches: Sequence[PatternMatch]
    ) -> str:
        all_placeholders = {p: n for m in matches for p, n in m.expansions.items()}
        for placeholder, nodes in all_placeholders.items():
            quoted_placeholder = re.escape(placeholder)
            raw_signature = self.__get_texts(nodes)
            # replacement = replacement.replace(placeholder, raw_signature)
            while placeholder in replacement:
                pattern = re.compile(r"( *)" + quoted_placeholder)
                matcher = pattern.search(replacement)

                if matcher:
                    spaces = matcher[1]
                    place_holder_length = len(placeholder)
                    index = replacement.index(placeholder)
                    # TODO a regex may be provided between backticks and the groups are used. This needs a better design
                    # A preferable solution is to pass a transformer function to the compose_replacement
                    if index + place_holder_length < len(replacement) and replacement[index + place_holder_length] == "`":
                        # ` ` means get regex
                        end_index = replacement.index(
                            "`", index + place_holder_length + 1
                        )
                        if not end_index:
                            raise ValueError("No closing ` found")
                        regex = replacement[index + place_holder_length + 1 : end_index]
                        regex_match = re.match(regex, raw_signature)
                        if regex_match:
                            raw_signature = "".join(regex_match.groups())
                        place_holder_length = end_index - index + 1
                    indent_replacement = raw_signature.replace("\n", "\n" + spaces)
                    if (
                        PatternMatch.is_multi(placeholder)
                        and index + place_holder_length < len(replacement)
                        and replacement[index + place_holder_length] == ";"
                    ):
                        place_holder_length += 1
                    # replace the placeholder with the indent replacement
                    replacement = (
                        replacement[:index]
                        + indent_replacement
                        + replacement[index + place_holder_length :]
                    )
                else:
                    print("Match doesn't match unexpectedly")
        return replacement

    def __get_texts(self, nodes: Sequence[ASTNode]) -> str:
        if len(nodes) == 1:
            return self.__get_text(nodes[0])
        # Use a ASTRewriter to only rewrite exactly that what needs to be rewritten
        rewriter = ASTRewriter(nodes, self.encoding, correct_indent=False)
        for node in nodes:
            rs = self.__get_text(node)
            org_rs = node.text
            if rs != org_rs:
                rewriter.replace(rs, node)
        result = rewriter.apply_to_string()
        indent = nodes[0].indent
        return TextUtils.shift_left(result, indent, start_line=1)

    def __get_text(self, node: ASTNode) -> str:
        if self._should_skip(node):
            return ""

        if node == self.nodes[0]:
            return node.text
        # the descendants may need to be rewritten as well
        #        rewrites = [rewrite for rewrite in self.rewrites if any(node.is_ancestor_of(rewrite_node) for rewrite_node in rewrite.nodes)]
        rewrites = [
            rewrite
            for rewrite in self.rewrites
            if any(node.is_ancestor_of(rewrite_node) for rewrite_node in rewrite.nodes)
        ]
        if rewrites:
            rewriter = _RewriteActions(
                node, self.encoding, self.correct_indent, rewrites
            )
            return rewriter.apply_to_string()
        return node.text

    def __prepare_replacement_content(
        self, new_content: str, target: PatternMatch | ASTNode | Sequence[ASTNode]
    ) -> tuple[str, Sequence[ASTNode]]:
        if isinstance(target, PatternMatch):
            new_content = self.__compose_replacement(new_content, [target])
            node_list = target.nodes
        else:
            node_list = (
                [target] if isinstance(target, ASTNode) else target
            )  # TODO How to make a Sequence[ASTNode] as type hints also show list[ASTNode]?
        return new_content, node_list

    def _should_skip(self, node: ASTNode):
        """
        if the node is not the first node of a pattern match it should be skipped
        """
        return any(
            node in rewrite.nodes[1:]
            for rewrite in self.rewrites
            if isinstance(rewrite.target, PatternMatch)
        )

    @staticmethod
    def _get_parent_statement(node : ASTNode):
        parent = node
        while parent and not parent.is_statement:
            parent = parent.parent
        return parent

    @staticmethod
    def __correct_for_comments_and_whitespace(
        offset: int,
        content: bytes,
        include_whitespace: bool,
        include_comments: bool,
        nodes: Sequence[ASTNode],
    ):
        start_offset = nodes[0].offset - offset
        end_offset = nodes[-1].extended_end_offset - offset
        if include_comments:
            preceding_node = nodes[0].preceding_sibling
            parent = nodes[0].parent
            start_comment_location = 0
            if preceding_node:
                # start after the comment of the preceding node
                start_comment_location = (
                        preceding_node.extended_end_offset - offset
                )
                preceding_end_offset = _RewriteActions.__get_comment_after_location(
                    start_comment_location, start_offset, content
                )
                if preceding_end_offset != (-1, -1):
                    start_comment_location = preceding_end_offset[1]
            elif parent:
                start_comment_location = parent.offset - offset
            # get the comment belonging to the preceding node
            extended_location = _RewriteActions._get_comment_location(
                start_comment_location, start_offset, content
            )
            if extended_location != (-1, -1):
                start_offset = extended_location[0]
            next_sibling = nodes[-1].next_sibling
            end_comment_location = (
                next_sibling.offset - offset
                if next_sibling
                else parent.end_offset - offset if parent else len(content)
            )
            location_after_comment = _RewriteActions.__get_comment_after_location(
                end_offset, end_comment_location, content
            )
            if location_after_comment != (-1, -1):
                end_offset = location_after_comment[1]
        if include_whitespace:
            end_offset = _RewriteActions.__extend_with_whitespace(end_offset, content)
        return start_offset, end_offset

    def cor_offset(self, offset: int):
        return offset - self.nodes[0].offset

    @staticmethod
    def _get_comment_location(
        start_offset: int, stop_offset: int, content: bytes
    ) -> tuple[int, int]:
        """get the location of the comment before the location, but after the stop_location
        a comment is a line that starts with // or a block that starts with /* and ends with */
        or a line that starts with #
        """
        # search last occurrence of //, /*, # in a byte array
        comment_start = content.rfind(b"//", start_offset, stop_offset)
        if comment_start != -1:
            comment_end = _RewriteActions.__get_end_of_line(content, comment_start)
            return comment_start, comment_end
        comment_start = content.rfind(b"/*", start_offset, stop_offset)
        if comment_start != -1:
            comment_end = content.find(b"*/", comment_start, stop_offset)
            if comment_end != -1:
                comment_end += len("*/")
            return comment_start, comment_end
        comment_start = content.rfind(b"#", start_offset, stop_offset)
        if comment_start != -1:
            comment_end = _RewriteActions.__get_end_of_line(content, comment_start)
            return comment_start, comment_end
        return -1, -1

    @staticmethod
    def __extend_with_whitespace(start_offset: int, content: bytes) -> int:
        end_location = _RewriteActions.__get_end_of_line(content, start_offset)
        text = content[start_offset:end_location]
        for byt in text:
            if byt not in b" \t":
                return start_offset
        return end_location

    @staticmethod
    def __get_comment_after_location(
        start_offset: int, end_offset: int, content: bytes
    ) -> tuple[int, int]:
        """get the location of the comment before the location, but after the stop_location
        a comment is a line that starts with // or a block that starts with /* and ends with */
        or a line that starts with #
        """
        line_end_offset = _RewriteActions.__get_end_of_line(content, start_offset)
        if line_end_offset == -1:
            line_end_offset = len(content)
        comment_start = content.find(b"//", start_offset, line_end_offset)
        if comment_start == -1:
            comment_start = content.rfind(b"#", start_offset, line_end_offset)
        if comment_start != -1:
            return comment_start, line_end_offset
        comment_start = content.rfind(b"/*", start_offset, line_end_offset)
        if comment_start != -1:
            # a block comment must start on the same line but doesn't have to finish on the same line
            comment_end = content.find(b"*/", comment_start, end_offset)
            if comment_end != -1:
                comment_end += len("*/")
            return comment_start, comment_end
        return -1, -1

    @staticmethod
    def __get_end_of_line(content: bytes, start: int):
        location = content.find(b"\n", start)
        if location == -1:
            return len(content)
        return location

    @staticmethod
    def __get_depth(node: ASTNode) -> int:
        depth = 0
        parent = node.parent
        while parent:
            if ASTFinder.matches_kind(parent, "(?i)Compound_?Stmt"):
                depth += 1
            parent = parent.parent
        return depth

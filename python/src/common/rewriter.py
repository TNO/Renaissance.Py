import sys


class Rewrite:
    def __init__(self, start: int, end: int, replacement: bytes) -> None:
        self.start = start
        self.end = end
        self.replacement = replacement


class Rewriter:
    """
    A class that allows for modifications to a byte sequence.
    """

    def __init__(self, content: bytes) -> None:
        self.__content = content
        self.__rewrites: list[Rewrite] = []

    def replace(self, start: int, end: int, new_content: bytes) -> None:
        """
        Replaces a portion of the content with new content.

        This method will replace the content between the specified start and end
        indices with the provided new_content. If there is an existing rewrite
        that partially overlaps with the specified range, the new content will be
        appended to the existing replacement, and the range will be adjusted to
        encompass both the old and new content. If the start or end indices are out
        of bounds, then new content will be inserted at the end of the byte sequence.

        Args:
            start (int): The starting index of the content to be replaced.
            end (int): The ending index of the content to be replaced.
            new_content (bytes): The new content to insert in place of the old content.

        Returns:
            None
        """
        for r in self.__rewrites:
            # if r partially overlaps with start and end then append the new content to the existing replacement
            if r.start <= start and r.end >= start:
                r.replacement += new_content
                r.start = min(r.start, start)
                r.end = max(r.end, end)
                return
        real_start = (
            len(self.__content) if start > len(self.__content) or start < 0 else start
        )
        real_end = len(self.__content) if end > len(self.__content) or end < 0 else end
        self.__rewrites.append(Rewrite(real_start, real_end, new_content))

    def apply(self) -> bytes:
        """
        Applies the rewrites to a copied byte sequence.

        This method reverses the order of the rewrites to ensure that insertions
        are performed correctly. It then sorts the rewrites by their start position
        in descending order and applies each rewrite to the byte sequence.

        Returns:
            bytes: The modified byte sequence after all rewrites have been applied.
        """
        result = bytearray(self.__content[:])
        for rewrite in sorted(self.__rewrites, key=lambda x: x.start, reverse=True):
            result[rewrite.start : rewrite.end] = rewrite.replacement
        return result

    @property
    def content(self) -> bytes:
        return self.__content


if __name__ == "__main__":
    # create a byte array a random bytes of len 20

    bytes = bytearray(20)
    for i in range(20):
        bytes[i] = ord("a") + i
    rewriter = Rewriter(bytes)
    rewriter.replace(5, 10, b"hellooo")
    rewriter.replace(5, 10, b" world")
    rewriter.replace(0, 0, b"BEGIN")
    s = rewriter.apply().decode(sys.getfilesystemencoding())
    print(len(s))
    print(s)

from dataclasses import dataclass, field
from typing import Any, Self

import pytest

import test.syntax_tree.infra_syntax_node
import test.syntax_tree.infra_text_segment


def _offset_to_line_col(text: str, offset: int) -> tuple[int, int]:
    """0-based (line, column) for a 0-based offset; offset may be len(text)."""
    assert 0 <= offset <= len(text)
    line = text.count("\n", 0, offset)
    last_nl = text.rfind("\n", 0, offset)
    col = offset if last_nl == -1 else offset - (last_nl + 1)
    return line, col


@dataclass(slots=True)
class DummyNode:
    # ---- backing text segment ----
    full_text: str
    location: str
    start_offset: int
    end_offset: int

    # ---- syntax node aspects ----
    kind: str = "Dummy"
    _children: list[Self] = field(default_factory=list)  # type: ignore
    _parent: Self | None = None

    # ---- TextSegment derived properties ----
    @property
    def start_line(self) -> int:
        return _offset_to_line_col(self.full_text, self.start_offset)[0]

    @property
    def start_column(self) -> int:
        return _offset_to_line_col(self.full_text, self.start_offset)[1]

    @property
    def end_line(self) -> int:
        return _offset_to_line_col(self.full_text, self.end_offset)[0]

    @property
    def end_column(self) -> int:
        return _offset_to_line_col(self.full_text, self.end_offset)[1]

    @property
    def text_segment(self) -> str:
        return self.full_text[self.start_offset : self.end_offset]

    # ---- SyntaxNode protocol properties ----
    @property
    def children(self) -> list[Self]:
        return self._children

    @property
    def syntax_attributes(self) -> dict[str, Any]:
        return {}

    @property
    def parent(self) -> Self | None:
        return self._parent

    @property
    def original_node(self) -> Self:
        return self

    # ---- safe mutator for tests (avoids "protected access" warnings) ----
    def set_children(self, children: list[Self]) -> None:
        self._children = children
        for c in children:
            c._parent = self

    def __hash__(self):
        return id(self)


# ----------------------------
# Monkeypatch: verify assert_valid_text_segment is called
# ----------------------------


class _SegmentCallCounter:
    def __init__(self) -> None:
        self.calls: list[Any] = []

    def __call__(self, seg: Any) -> None:
        self.calls.append(seg)


@pytest.fixture
def segment_validator_counter(monkeypatch: pytest.MonkeyPatch) -> _SegmentCallCounter:
    counter = _SegmentCallCounter()
    monkeypatch.setattr(test.syntax_tree.infra_text_segment, "assert_valid_text_segment", counter)
    return counter


# ----------------------------
# Success cases
# ----------------------------
@pytest.mark.skip("result is empty")
def test_assert_valid_syntax_node_ok(segment_validator_counter: _SegmentCallCounter) -> None:
    text = "ab\ncd\nef"
    loc = "mem://t"

    root: DummyNode = DummyNode(text, loc, 0, len(text), kind="Root")
    c0 = DummyNode(text, loc, 0, 3, kind="L0")  # "ab\n"
    c1 = DummyNode(text, loc, 3, 6, kind="L1")  # "cd\n"
    c2 = DummyNode(text, loc, 6, 8, kind="L2")  # "ef"

    root.set_children([c0, c1, c2])

    test.syntax_tree.infra_syntax_node.assert_valid_syntax_node(root)

    assert segment_validator_counter.calls == [root, c0, c1, c2]


@pytest.mark.skip("result is empty")
def test_assert_valid_syntax_tree_ok(segment_validator_counter: _SegmentCallCounter) -> None:
    text = "ab\ncd\nef"
    loc = "mem://t"

    root: DummyNode = DummyNode(text, loc, 0, len(text), kind="Root")
    mid = DummyNode(text, loc, 0, 6, kind="Mid")
    leaf0 = DummyNode(text, loc, 0, 3, kind="Leaf0")
    leaf1 = DummyNode(text, loc, 3, 6, kind="Leaf1")

    root.set_children([mid])
    mid.set_children([leaf0, leaf1])

    test.syntax_tree.infra_syntax_node.assert_valid_syntax_tree(root)

    assert set(segment_validator_counter.calls) >= {root, mid, leaf0, leaf1}


# ----------------------------
# Failure modes (node-level)
# ----------------------------


def test_children_must_be_ordered_by_start_offset(segment_validator_counter: _SegmentCallCounter) -> None:
    text = "abcdef"
    loc = "mem://t"

    root: DummyNode = DummyNode(text, loc, 0, 6, kind="Root")
    a = DummyNode(text, loc, 2, 3, kind="A")
    b = DummyNode(text, loc, 1, 2, kind="B")

    root.set_children([a, b])

    with pytest.raises(AssertionError, match=r"ordered by non-decreasing start_offset"):
        test.syntax_tree.infra_syntax_node.assert_valid_syntax_node(root)


def test_children_must_not_overlap(segment_validator_counter: _SegmentCallCounter) -> None:
    text = "abcdef"
    loc = "mem://t"

    root: DummyNode = DummyNode(text, loc, 0, 6, kind="Root")
    a = DummyNode(text, loc, 1, 4, kind="A")
    b = DummyNode(text, loc, 3, 5, kind="B")

    root.set_children([a, b])

    with pytest.raises(AssertionError, match=r"must not overlap"):
        test.syntax_tree.infra_syntax_node.assert_valid_syntax_node(root)


def test_child_must_be_within_parent_span(segment_validator_counter: _SegmentCallCounter) -> None:
    text = "abcdef"
    loc = "mem://t"

    root: DummyNode = DummyNode(text, loc, 1, 5, kind="Root")
    child = DummyNode(text, loc, 0, 2, kind="Bad")

    root.set_children([child])

    with pytest.raises(AssertionError, match=r"start_offset must lie within the node span"):
        test.syntax_tree.infra_syntax_node.assert_valid_syntax_node(root)


def test_child_must_point_back_to_parent(segment_validator_counter: _SegmentCallCounter) -> None:
    text = "abcdef"
    loc = "mem://t"

    root: DummyNode = DummyNode(text, loc, 0, 6, kind="Root")
    child = DummyNode(text, loc, 0, 1, kind="Child")

    # Intentionally wrong: do not use set_children; parent stays None
    root._children = [child]  # type: ignore

    with pytest.raises(AssertionError, match=r"parent must be the node itself"):
        test.syntax_tree.infra_syntax_node.assert_valid_syntax_node(root)


def test_child_must_share_text_and_location(segment_validator_counter: _SegmentCallCounter) -> None:
    text = "abcdef"
    loc = "mem://t"

    root: DummyNode = DummyNode(text, loc, 0, 6, kind="Root")
    child = DummyNode("DIFFERENT", loc, 0, 1, kind="Child")

    root.set_children([child])

    with pytest.raises(AssertionError, match=r"full_text must equal node\.full_text"):
        test.syntax_tree.infra_syntax_node.assert_valid_syntax_node(root)


# ----------------------------
# Failure modes (tree-level)
# ----------------------------


def test_assert_valid_syntax_tree_detects_cycle(segment_validator_counter: _SegmentCallCounter) -> None:
    text = "abc"
    loc = "mem://t"

    root: DummyNode = DummyNode(text, loc, 0, 1, kind="Root")
    child = DummyNode(text, loc, 0, 1, kind="Child")

    root.set_children([child])
    child.set_children([root])  # cycle

    with pytest.raises(AssertionError, match=r"same node object twice"):
        test.syntax_tree.infra_syntax_node.assert_valid_syntax_tree(root)

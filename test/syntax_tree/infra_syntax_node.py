from typing import Any

from renaissance.syntax_tree.syntax_node import SyntaxNode
from test.syntax_tree.infra_text_segment import assert_valid_text_segment


def assert_valid_syntax_node(node: SyntaxNode[Any]) -> None:
    """
    Validate local (non-recursive) invariants for a syntax node.

    Uses `assert_valid_text_segment` to check text-segment invariants.

    Enforced syntax-node invariants:
      1) Each child segment is within the parent's segment.
      2) Children are ordered by increasing start_offset (lowest first).
      3) Children do not overlap (child[i].end_offset <= child[i+1].start_offset).
      4) Each child's parent pointer is exactly this node (identity: `is`).
      5) Each child shares the same backing text and location as the parent.
    """
    # Ensure the node itself is a valid text segment.
    assert_valid_text_segment(node)

    children = node.children
    if not children:
        return

    # Validate first child fully, then compare successive pairs.
    prev = children[0]
    _assert_child_valid(node, prev, index=0)

    for i in range(1, len(children)):
        cur = children[i]
        _assert_child_valid(node, cur, index=i)

        # (2) order: lowest offset first
        assert prev.start_offset <= cur.start_offset, (
            "Children must be ordered by non-decreasing start_offset. "
            f"Found child[{i-1}].start_offset={prev.start_offset} > child[{i}].start_offset={cur.start_offset}."
        )

        # (3) non-overlap
        assert prev.end_offset <= cur.start_offset, (
            "Children must not overlap and must be in textual order. "
            f"Found child[{i-1}].end_offset={prev.end_offset} > child[{i}].start_offset={cur.start_offset}."
        )

        prev = cur


def _assert_child_valid(node: SyntaxNode[Any], child: SyntaxNode[Any], *, index: int) -> None:
    # Ensure the child itself is a valid text segment.
    assert_valid_text_segment(child)

    # (4) parent pointer (identity, not equality)
    assert child.parent is node, f"child[{index}].parent must be the node itself (identity check with `is`)."

    # (5) same backing text and location
    assert child.full_text == node.full_text, f"child[{index}].full_text must equal node.full_text (same backing text expected)."
    assert child.location == node.location, f"child[{index}].location must equal node.location (same origin expected)."

    # (1) containment within parent span
    assert node.start_offset <= child.start_offset <= node.end_offset, (
        "child[{idx}].start_offset must lie within the node span. " "Got child[{idx}].start_offset={cso}, expected in [{nso}, {neo}]."
    ).format(idx=index, cso=child.start_offset, nso=node.start_offset, neo=node.end_offset)

    assert node.start_offset <= child.end_offset <= node.end_offset, (
        "child[{idx}].end_offset must lie within the node span. " "Got child[{idx}].end_offset={ceo}, expected in [{nso}, {neo}]."
    ).format(idx=index, ceo=child.end_offset, nso=node.start_offset, neo=node.end_offset)


def assert_valid_syntax_tree(root: SyntaxNode[Any]) -> None:
    """
    Validate an entire syntax tree (all reachable nodes).

    Enforced invariants:
      - All local invariants (see assert_valid_syntax_node)
      - No cycles / no repeated node object in traversal (a proper tree)
    """
    visited: set[int] = set()
    stack: list[SyntaxNode[Any]] = [root]

    while stack:
        node = stack.pop()

        node_id = id(node)
        assert node_id not in visited, (
            "Tree traversal encountered the same node object twice. " "This indicates a cycle or a DAG (shared subtree), not a tree."
        )
        visited.add(node_id)

        assert_valid_syntax_node(node)

        # Order does not matter for validation.
        stack.extend(node.children)

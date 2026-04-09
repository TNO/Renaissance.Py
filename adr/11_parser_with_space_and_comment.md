# 11 - Parser with Space and Comment

Status: Proposal

Date: 2026-03-27

Authors:
 - jinmin.hu@capgemini.com
 - huub.joosten@capgemini.com
 - luna.li@capgemini.com
 - paul.nelissen@esi.nl
 - pierre.vandelaar@tno.nl

## Table of contents

- [Context](#context)
- [Decision](#decision)
- [Implementation notes](#implementation-notes)
- [Example](#example)
- [Rationale](#rationale)
- [Consequences](#consequences)
- [Alternatives considered](#alternatives-considered)
- [Related decisions](#related-decisions)

## Context

The goal of this ADR is provide a guideline on what to focus on when selecting a parser for a new language in renaissance.

Refactoring tools must preserve the exact formatting of source code, including whitespace and comments, which are
not semantically significant to the language but are critical for producing output that is indistinguishable from
the original. Traditional parsers discard whitespace and comments (trivia) before building the AST, which means a
round-trip from raw source → AST → raw source loses this information and produces incorrect or unacceptable output.
Storing trivia in a separate data structure requires glue code to reassemble the output, increasing complexity and
maintenance burden.

## Decision

- Whitespace and comments must be preserved through the full parse → transform → unparse round-trip, producing
  output that is identical to the original source when no transformation is applied.
- Comments and whitespace are made part of the AST node itself (as leading/trailing trivia attached to the node),
  rather than stored in a separate data structure.
- The amount of glue code required to reassemble source text from the AST is minimised by design.
- For Python, **libcst** is used as the parser, as it natively represents whitespace and comments as part of its
  CST nodes and provides a lossless round-trip out of the box.

## Implementation notes

- Use `libcst` for parsing and unparsing Python source. It stores whitespace and comments directly on each node
  via `whitespace`, `leading_lines`, and similar fields.
- For non-Python languages, attach leading and trailing trivia directly to each AST node, following the pattern
  used by Roslyn (C#) and tree-sitter.
- The unparser must not add, remove, or reorder trivia unless a transformation explicitly modifies it.
- When a transformation produces a new node, trivia from the replaced node is transferred to the replacement by
  default.

## Example

```python
import libcst as cst

source = """\
# important comment
x = 1  # inline comment
"""

tree = cst.parse_module(source)
# Round-trip: produces exactly the same source
assert tree.code == source

# Transformation using libcst
class RenameX(cst.CSTTransformer):
    def leave_Name(self, original_node, updated_node):
        if updated_node.value == "x":
            return updated_node.with_changes(value="y")
        return updated_node

new_tree = tree.visit(RenameX())
# Whitespace and comments are preserved; only "x" is renamed to "y"
print(new_tree.code)
```

## Rationale

Using libcst for Python eliminates the need to build a custom trivia-preserving parser. libcst is a
production-quality Concrete Syntax Tree library that natively preserves all whitespace, comments, and formatting
as part of its node structure, providing lossless round-trips with minimal glue code. Attaching trivia to nodes
(rather than a side-table) ensures transformations can reason about and manipulate comments and whitespace in a
uniform, self-contained way.

## Consequences

Positive:
- Lossless round-trip: raw → CST → raw produces identical output when no transformation is applied.
- No separate trivia store; no glue code to reassemble source text.
- Transformations can inspect and modify comments and whitespace uniformly.
- libcst is actively maintained and widely used in the Python ecosystem.

Negative:
- libcst adds an external dependency.
- libcst's node model is more verbose than a plain AST; developers must learn its API.
- For non-Python languages a custom trivia-preserving strategy must still be implemented.

## Alternatives considered

- Standard `ast` module — rejected because it discards all whitespace and comments, making lossless round-trips
  impossible.
- Store trivia in a separate side-table indexed by source position — rejected because it requires glue code to
  rejoin trivia with nodes during unparsing, contradicting the goal of minimal glue code.
- tree-sitter — considered but rejected for Python as primary parser because libcst provides a higher-level,
  Python-native API with built-in transformation support.

## Related decisions

- See ADR 01 (Children and properties) for the overall AST node structure that trivia fields extend.
- See ADR 04 (Immutable properties) for the immutability strategy applied to trivia fields.

---

Revision history:
- 2026-03-27: Converted to ADR template and clarified decision.

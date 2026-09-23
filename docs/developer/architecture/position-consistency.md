# Position consistency

{ #dev-architecture-code-position-consistency }

**Stable ID:** `ARCH-CODE-POSITION-CONSISTENCY`

## Purpose

Document the design decisions that guarantee that the [rewrite](modify.md) step and the parser agree on
what a node's position (offset, length) in the source text means.

## Scope

This document covers how a node's position is bound to the source buffer it was computed from, so
that a rewrite can never apply a position under a different assumption (encoding, unit, or buffer)
than the one the parser used when it built the node.

It does not cover how multiple changes are combined once their positions are known to be consistent -
see [Rewrite semantics](rewrite-semantics.md) for that.
It does not cover the definition of the rewrite step itself - see [Modify](modify.md).

## Definition

Every node exposes an `offset` and `length` (or `end_offset`), and is navigable to its root via `parent`
(see [Code architecture](code-architecture.md)). The root is the same object, produced by the same
parser invocation, that the buffer and every offset in the tree were derived from.

A parser determines, on its own terms, what positional information it exposes for a node - this may
be an offset, a line/column pair, or both. This is a property of the given parser, not a design
decision of Renaissance: we adopt whatever positional information the parser natively provides,
rather than mandating a single representation.

### Position representation is defined by the parser

A parser also determines how it stores the file content internally in order to compute those
positions - for example, as a byte buffer with a particular encoding, or as a sequence of
characters. The parser may treat this internal representation as an implementation detail that is
not exposed through its own public interface.

The rewriter uses the positional information produced by the parser to locate text within that same
content. If the rewriter's view of the content (e.g. a sequence of bytes) differs from the view the
parser used to compute positions (e.g. a sequence of characters, or vice versa), a position that is
valid under one view need not be valid, or may refer to a different location, under the other - see
[Matching](../../user/concepts/matching.md) for how the same text yields different results
depending on the conceptual view (e.g. granularity) chosen; a byte-based view and a
character-based view of the same text are exactly such differing views.

#### Decision - Adapter exposes the parser's view

We require that the adapter/wrapper of each parser integration exposes:

1. the positional information exactly as produced by the parser (offset and/or line/column,
   whichever the parser natively provides), together with the (lazy) logic to convert an offset
   into a line/column pair and vice versa, whenever the parser does not natively provide both, and
1. the representation of the file content the parser used to compute that positional information
   (e.g. bytes with a specific encoding, or a sequence of characters),

even when the parser itself considers either of these an internal implementation detail not
exposed through its own interface. This way the rewriter obtains the exact same view of the source
text that the parser used, rather than assuming or independently reconstructing one. Requiring the
conversion logic from the adapter, rather than from the Renaissance core, keeps the core and the
rewriter independent of how a particular parser natively represents positional information.

### Guaranteeing agreement between parser and rewriter

A rewrite reads a node's position and splices replacement text into a byte buffer at that position.
This is only correct if the buffer being patched is the same buffer, encoded the same way, that the
parser used to compute the node's position in the first place. If the rewriter independently
reconstructs a buffer - for example, by re-encoding a node's text using an unrelated, ambient encoding -
the two sides can silently disagree, producing incorrect or corrupted output.

#### Options considered

* Structural rewriting: mutate the tree and let the parser's own printer regenerate text, so no
  separate offset bookkeeping exists (as used for Python, see
  [ADR 11](adr/11_parser_with_space_and_comment.md)). Not available for every integration, since
  not every parser provides a lossless printer.
* Wrap positions in a new value type (e.g. `Span`/`SourceFile`) that binds an offset to the buffer
  it was computed from. Rejected as redundant: the node already carries everything needed (offset,
  length, and a path to its root) without introducing a new type.
* Compare source file paths to decide whether two nodes' positions are comparable. Rejected: the
  same path can back different buffers at different times (e.g. a stale tree held before a reparse,
  a file re-read after an on-disk edit, or two different node representations for the same language
  parsed from the same file). Path equality would wrongly treat these as compatible.

#### Decision - Root identity

1. A rewrite batch is scoped to a single root.
1. Nodes are accepted into the same rewrite batch only if they share that root, checked by object
   identity (`is`), not by file path or any other derived key.
1. The byte buffer used to apply a rewrite batch is obtained from the root itself, not re-derived
   by re-encoding node text.
1. A mismatch is rejected immediately (fail fast) rather than silently applied.

## Invariants / guarantees

* All nodes involved in a single rewrite batch share the same root object.
* The buffer patched by a rewrite is the same buffer the parser produced the involved nodes' offsets
  from.
* A rewrite across nodes with different roots is rejected rather than silently applied.
* A node's positional information (offset and/or line/column) and the content representation it was
  computed from are exposed by the adapter exactly as the parser produced them, not independently
  re-derived or assumed.

## Related features

* [Modify](modify.md)
* [Rewrite semantics](rewrite-semantics.md)
* [Matching](../../user/concepts/matching.md)

## Related tests

## Related code

## Notes
* [GCC diagnostics docs](https://gcc.gnu.org/onlinedocs/gcc/Diagnostic-Message-Formatting-Options.html) show a widely used, but de facto, location format such as `file:line` or `file:line:column`. This is a practical convention used by compiler tooling, not a single universal formal standard.
* [Clang diagnostics docs](https://clang.llvm.org/docs/UsersManual.html#diagnostics) also use location and range formats in a compiler-style convention and explicitly state that column numbers may be counted in bytes from the beginning of the line. This illustrates why position semantics depend on the underlying text model and encoding, especially when multibyte characters are present.
* [Language Server Protocol position specification](https://microsoft.github.io/language-server-protocol/specifications/lsp/3.19/specification/#position) defines positions as `line` and `character` in a text model, with `character` expressed in the document's chosen indexing unit (for example, UTF-16 code units in many client implementations). This makes the point that a single file location may be represented differently across tools, editors, and parsers.
* [Language Server Protocol range specification](https://microsoft.github.io/language-server-protocol/specifications/lsp/3.19/specification/#range) formalizes the relationship between ranges and text positions, including the need to handle line splitting and end-of-line conventions consistently.
* These examples reinforce the core design decision of this document: positions must be treated as bound to the exact buffer and text representation used by the parser, rather than assumed to be a universal byte-based or character-based convention.


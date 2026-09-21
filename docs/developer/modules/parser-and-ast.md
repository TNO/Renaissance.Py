# Parser and AST modules

{ #codemod-parser-and-ast }

**Stable ID:** `CODEMOD-PARSER_AND_AST`

## Adding a parser integration

A parser integration adapts an external syntax tree to the structural node
contract used by Renaissance. The integration belongs in its own directory:

```text
src/renaissance/integrations/<parser>/
test/<parser-or-language>/
```

Keep parser-specific code inside that directory. Generic matching, traversal,
rewriting, and refactoring code should depend on the node protocol rather than
on parser classes.

## Current status

Renaissance provides reusable mechanisms, not a universal parser abstraction.
Parser adapters choose their own parsing, source-span, trivia, navigation, and
reparsing implementations.

### Shared facilities

- An adapter that satisfies `NodeProtocol` can use generic traversal, finding,
  and matching.
- An adapter whose nodes also satisfy `Rewritable` can use the shared
  `ASTRewriter`.
- `SemanticKind` is optional. It is a coarse convenience for broad searches,
  diagnostics, and tests; recipes may instead use `parser_kind` or parser-local
  predicates.

### Adapter responsibilities

Each adapter owns its parsing and reparsing, node construction and navigation
helpers, source-span calculation, comment and whitespace handling, and any
reference or data-flow analysis it provides. Renaissance does not require a
shared parser factory, trivia model, reference model, or navigation API.

### Recipes

Renaissance shares transformation mechanisms across adapters, but recipes
normally select and generate language- or parser-specific code. Validate a
recipe against the source and trivia behavior of the selected adapter.

## Node contract

Every adapted node must expose the fields consumed by `NodeProtocol`:

```python
parser_kind: str
semantic_kind: SemanticKind
properties: Mapping[str, Any]
children: Sequence[NodeProtocol]
signature: str
name: str
```

The core protocol is the minimum contract for traversal and matching. It
allows a node to participate in generic finding and matching, but does not
make that node a source-text rewrite target.

`ASTRewriter` is shared across integrations. It accepts nodes satisfying its
separate `Rewritable` protocol:

```python
offset: int
end_offset: int
extended_end_offset: int
filename: str
text: str
parent: Rewritable | None
```

`parent` provides the upward navigation consumed by the rewriter. Adapters may
also provide navigation helpers such as `root`, `next_sibling`, and
`preceding_sibling` for their own recipes.

To use one node in the complete workflow, it must satisfy both protocols and
its source locations must address the same original source as the root passed
to `ASTRewriter`:

```text
parse with a backend-specific factory
-> receive a node satisfying NodeProtocol
-> find and match generically
-> select a node also satisfying Rewritable
-> collect edits with ASTRewriter
-> apply edits using that backend's source-span and trivia semantics
-> reparse with that backend's factory
```

The shared rewriter does not prescribe how an adapter derives source spans,
preserves comments and whitespace, or reparses source. Each adapter supplies
those behaviors individually. Reference and data-flow collections
(`references`, `referenced_by`) are also parser-specific because not every
parser can provide the same analysis. Keep the original parser node available
when callers need parser-specific data.

The native Python `ast.AST` adapter is a lightweight structural adapter and
does not preserve source trivia in the same way as the lossless Python RST/CST
adapters. Use the lossless adapter when source-preserving rewriting is needed.

## Classify nodes

`parser_kind` preserves the exact spelling supplied by the parser. Map that
spelling to the shared vocabulary in a parser-local map:

```python
PARSER_KIND_MAP = {
    "function_definition": SemanticKind.FUNCTION,
    "call_expression": SemanticKind.CALL,
}

self.parser_kind = parser_node.kind
self.semantic_kind = PARSER_KIND_MAP.get(self.parser_kind, SemanticKind.NODE)
```

`semantic_kind` is an optional, coarse shared vocabulary. Use it for broad
searches, stable display labels, and cross-adapter tests where the shared
concept is useful. It is not a universal language taxonomy and does not make
recipes or replacement text portable. Use `parser_kind` or a parser-local
predicate whenever a recipe depends on exact grammar or parser behavior. Do
not create a shared nominal class for a parser-only concept.

## Use predicates

Use a parser-local predicate when several parser spellings represent one
adapter concept, or when the condition combines multiple node fields:

```python
TYPE_REFERENCE_KINDS = frozenset({"TypeRef", "TYPE_REF"})


def is_parser_type_reference(node: NodeProtocol) -> bool:
    return node.parser_kind in TYPE_REFERENCE_KINDS
```

Patterns are not node classifications. Represent one-node and all-node
placeholders with `PatternKind.MATCH_ONE` and `PatternKind.MATCH_ALL`.

## Equality and display

For equality and hashing, use semantic identity when it is mapped and exact
parser identity otherwise:

```python
kind_key = semantic_kind if semantic_kind is not SemanticKind.NODE else parser_kind
```

Normal AST display is semantic-first. Developer diagnostics can request exact
parser labels with:

```python
ASTShower.get_node(node, display_parser_kind=True)
```

## Required tests

Add focused tests for:

- parser metadata and semantic mappings
- unknown parser kinds
- equality and hashing
- parser-local predicates
- matching and `PatternKind` placeholders
- source ranges, comments, and whitespace
- rewriting, when supported
- references, when supported
- default and parser-detail display modes

Use the existing backend tests as the primary contract examples. Cross-backend
tests establish the `NodeProtocol` matching contract; rewrite, trivia, and
reparse behavior remain tests and responsibilities of the selected adapter.

## Validation

Run the repository checks with the parser's optional dependencies installed:

```powershell
uv run pytest ./test
uv run pytest ./features
uv run ruff check ./src ./test ./tools ./features
uv run pyright ./src ./test ./tools ./features
uv run mkdocs build --strict
```

For Clang integrations, make LLVM available on `PATH` before running tests.

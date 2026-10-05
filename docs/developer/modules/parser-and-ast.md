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

## Clang prerequisites

The repository has two independent Clang backends, and they obtain Clang in
different ways:

| Backend | Needs | Obtained from |
| --- | --- | --- |
| `ClangASTNode` | the `libclang` library | the pinned `libclang-ng` wheel, installed by `uv sync` |
| `ClangJsonASTNode` | the `clang` or `clang++` driver | an LLVM installation on the machine |

`ClangASTNode` works without extra setup: `clang_ast_node.py` points libclang
at the bundled native library, so its version is pinned by `pyproject.toml`
and is identical on every machine.

`ClangJsonASTNode` runs the compiler driver as a subprocess, because
`-Xclang -ast-dump=json` is a frontend action that the library API does not
expose. That driver is not part of the Python dependencies and must be
installed separately. Without it, every `clang_json` test fails.

### Determine the required version

Both backends are compared against the same expectations in the cross-backend
tests, so the driver should have the same LLVM major version as the bundled
library. The bundled version is the one pinned in `pyproject.toml`. Print the
LLVM version it corresponds to:

```powershell
uv run python -c "from importlib.metadata import version; print('.'.join(version('libclang-ng').split('.')[:3]))"
```

The `libclang-ng` version has four components, such as `22.1.4.2`. The first
three are the LLVM version, `22.1.4` in this example, and the fourth is the
wheel build number.

### Install that version

Windows, where the version must be given exactly as published. A major version
alone is rejected with `No version found matching: 22`, and
`winget show LLVM.LLVM --versions` lists the accepted values:

```powershell
winget install LLVM.LLVM --version 22.1.4
```

Debian, Ubuntu, or WSL. The distribution package is usually older than the
pinned version, so install from the LLVM apt repository, which takes the major
version and installs version-suffixed binaries such as `clang-22`:

```bash
wget https://apt.llvm.org/llvm.sh
chmod +x llvm.sh
sudo ./llvm.sh 22
```

macOS, using the versioned formula:

```bash
brew install llvm@22
```

Open a new terminal afterwards, so that the updated `PATH` is picked up, and
check that the driver is reachable and reports the expected version:

```powershell
clang --version
```

On Windows the installer does not add LLVM to `PATH`, so this reports that
`clang` is not recognized even though the install succeeded. Either add
`C:\Program Files\LLVM\bin` to `PATH`, or point `RENAISSANCE_CLANG` at the
driver as described below.

### Select a specific driver

The driver is resolved in this order:

1. the first entry of `extra_args`, when it names a clang executable
2. the path passed to `ClangJsonASTNode.set_compiler_path()`
3. the `RENAISSANCE_CLANG` environment variable
4. `clang`, or `clang++` for C++, found on `PATH`

When none of these resolves to an executable driver, parsing raises
`FileNotFoundError` describing these options, rather than failing inside the
subprocess call.

Set `RENAISSANCE_CLANG` when `PATH` does not already point at the intended
driver. This is the normal case on Windows, where the installer leaves `PATH`
alone, and on Linux, where the LLVM apt repository installs `clang-22` while
`clang` remains the distribution version:

```bash
export RENAISSANCE_CLANG=/usr/bin/clang++-22
```

```powershell
$env:RENAISSANCE_CLANG = "C:/Program Files/LLVM/bin/clang++.exe"
& $env:RENAISSANCE_CLANG --version
```

The major version of the resolved driver is compared with the pinned
`libclang-ng` version, and a mismatch raises a warning such as
`clang++ is LLVM 18 while libclang is pinned to LLVM 22; the ASTs may differ.`
Only the major version is compared, so any `22.x` driver satisfies a `22.1.4`
pin. No warning means the versions agree.

## Validation

Run the repository checks with the parser's optional dependencies installed:

```powershell
uv run pytest ./test
uv run pytest ./features
uv run ruff check ./src ./test ./tools ./features
uv run pyright ./src ./test ./tools ./features
uv run mkdocs build --strict
```

The Clang backends additionally require the setup described in
[Clang prerequisites](#clang-prerequisites).

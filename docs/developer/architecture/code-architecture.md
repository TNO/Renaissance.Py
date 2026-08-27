# Code architecture

{ #dev-architecture-code }

**Stable ID:** `ARCH-CODE`

1. We have chosen [Python](https://www.python.org/) as the programming language for our implementation.

    a. We have chosen the latest released version, currently 3.14, and when a new version is released we
       intend to follow within three months, given that resources permit.

    a. We have chosen to use [typing](https://docs.python.org/3/library/typing.html) on all functions
       and their parameters.
       We use [pyright](https://github.com/microsoft/pyright) as type checker.

    a. Our code should adhere to the conventions of Python,
       such as [philosophy](https://peps.python.org/pep-0020/),
       [style](https://peps.python.org/pep-0008/), and [documentation](https://peps.python.org/pep-0257/).
       We use [ruff](https://docs.astral.sh/ruff/) as code formatter and linter.

1. We enable analyses purely based on the AST as being insensitive to layout and comments signanficantly
   simplifies the development and maintenance of these analyses.

1. We do not limit analyses and transformations to the AST, as knowledge about the
   [token](../../glossary.md#token) and [trivia](../../glossary.md#trivia) is often also needed.

1. We defined AST Node as a
   [Protocol (a.k.a. statically duck typing)](https://typing.python.org/en/latest/spec/protocol.html),
   with basic functionality and a back door:
   `get_original_node` to obtain the AST node as provided by the parser.

1. AST Nodes are read only and immutable.

1. AST Nodes are navigable, so parent must be present (except for the ATU / top node) and
   children are always present (although it might be an empty list).

1. Standard 'semantic' functions must be provided that when given a code snippet will return
   the variables read or written.
   Based on the output of these functions dependencies between code snippets are determined.

1. We enable syntax pattern matching and semantic filtering, see the [Find](find.md),
   [Filter](filter.md), and [Modify](modify.md) steps for details.
   In most cases, standard filter functions (as describe before) are enough, but we enable user specific
   filter functions that access the original AST.

1. We collect multiple transformations, we are syntax aware - to handle shared text boundaries,
   and then in one step [rewrite](rewrite-semantics.md) the code text.

1. For general purpose, we don't mandate that the final text should be parsable.
   When chaining changes, all intermediate texts must be parsable - in case of transpilation,
   different parsers can be involved.

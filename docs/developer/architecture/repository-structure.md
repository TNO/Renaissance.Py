<!--
Copyright (C) 2024-2026 TNO

Licensed under the terms specified in the LICENSE file in the root directory
of this repository, also available at:
https://github.com/TNO/Renaissance.Py/blob/main/LICENSE
-->

# Repository structure

{ #dev-architecture-repository-structure }

**Stable ID:** `ARCH-CODE-STRUCTURE`

**Status:** Draft, proposal for [issue 187](https://github.com/TNO/Renaissance.Py/issues/187).
Once accepted, it supersedes the directory layout of [ADR 14](adr/14_code_repositories.md);
the single-repository decision of ADR 14 is unchanged.

## Purpose

Document the target structure of the source code, the tests and the documentation, the dependencies allowed between its parts,
and the public API of each package.

## Scope

This page describes *where code lives* and *what may depend on what*.
It does not describe how to get there; that is the job of the migration plan.
It does not introduce new functionality: every package listed here holds code that exists today.
Packages envisioned in issue 187 for which no code exists yet, such as semantic services, are added when that code is written.

## Definition

### Three layers

The source tree is divided into three layers.

| Layer             | Package                           | Contents                                                                    |
| ----------------- | --------------------------------- | --------------------------------------------------------------------------- |
| `core`            | `renaissance.core`                | Parser- and language-agnostic infrastructure                                |
| `parser_bindings` | `renaissance.parser_bindings`     | Integration of one concrete parser each, including build-artefact parsers   |
| `recipes`         | `renaissance.recipes`             | Analyses, transformations and applications, including the command line      |

Decisions:

- Application code, such as the command line interface, is a recipe. There is no separate application layer.
- Reading build artefacts (`compile_commands.json`, a `Makefile` via Bear, a source directory tree) is parsing,
  so the project scanners are a parser binding.
- Directory names are valid Python identifiers: lower case, words separated by `_`, no `.` or `-`.

### Allowed dependencies between layers

```text
recipes ──────► core ◄────── parser_bindings
   ┆                                ▲
   └┄┄┄┄┄ only with evidence ┄┄┄┄┄┄┄┘
```

| Layer             | May import                                                   | Must not import                    |
| ----------------- | ------------------------------------------------------------ | ---------------------------------- |
| `core`            | nothing outside `core`                                       | `parser_bindings`, `recipes`       |
| `parser_bindings` | `core.model`, `core.pattern`, `core.matching`                | another binding, `recipes`         |
| `recipes`         | `core`, other recipes                                        | `parser_bindings`, unless exempted |

Imports of the standard library and of third-party packages are not restricted by this page.
Imports inside an `if TYPE_CHECKING:` block count as dependencies.

#### Recipes do not use parser bindings, unless proven necessary

A recipe expresses intent in terms of the core, so that it runs on any parser that provides the abstractions the core defines.
An import from a recipe into a parser binding is a violation.
It may be exempted only on facts, not on expectations. An exemption names:

1. the binding symbol that is used;
1. the capability the core is missing, demonstrated by the code that needs it;
1. the issue that tracks adding that capability to the core.

#### No dependencies between parser bindings

A parser binding imports nothing from another parser binding, without exceptions.
Two bindings that need similar data, such as a mapping from parser kinds to `SemanticKind`, each keep their own copy.
Duplicated mappings are acceptable; a mapping shared between bindings is not, because a key added for one parser then silently
changes the classification of another parser ([issue 266](https://github.com/TNO/Renaissance.Py/issues/266)).
What bindings genuinely share, such as `SemanticKind` and `NodeProtocol`, is common vocabulary and belongs in the core.

#### Bindings do not use rewriting or processing

No binding uses `core.rewriting` or `core.processing` today.
Information that the rewriter needs from a binding, such as the location of comments, flows through `core.model`.

### Core

The core has five sub-packages. Each may import only the sub-packages below it in this list.

| Sub-package          | Responsibility                                                                                  |
| -------------------- | ----------------------------------------------------------------------------------------------- |
| `core.processing`    | Running recipes: processors, batch processing, recipe steps and repetition until no change      |
| `core.rewriting`     | Collecting changes and applying them to the text, both node based and character based           |
| `core.matching`      | Finding the occurrences of a pattern in a tree, with their placeholder bindings                 |
| `core.pattern`       | The pattern language: placeholder markers, placeholder kinds and the `$` notation               |
| `core.model`         | The AST model: node protocol, semantic kinds, text segments, navigation, finding by predicate   |

`core.rewriting` imports `core.matching` for one reason: the rewriter accepts a `PatternMatch` as a target and uses its
bindings to fill in a replacement. It does not use the matching algorithm.

`renaissance.core` itself exports nothing; code imports from the sub-packages.
This avoids the eager re-exports that cause the circular import in the current `renaissance.syntax_tree` package.

#### The core contains no language- or parser-specific facts

Kind names, property names, keywords and comment syntax belong to the binding of the parser that defines them.
Where generic logic needs such a fact, the binding supplies it, either through the model (a member of the node protocol) or as a
parameter of the generic algorithm.
An import check cannot detect a violation of this rule, so it is enforced by review.
The violations known at the time of writing are listed under [Known violations](#known-violations).

#### Comments are handled by the parser bindings

Comment syntax is language specific, so the core does not contain comment delimiters.
Either of the following is acceptable, and a binding may choose:

1. the binding recognises comments and exposes them through the model, for example as text segments attached to nodes;
1. the binding provides a description of its comment syntax (line-comment prefixes, block-comment delimiters) and the generic
   algorithm in `core.rewriting` takes it as a parameter.

This is related to [issue 261](https://github.com/TNO/Renaissance.Py/issues/261), which observes that trivia is modelled in two
different ways.

### Parser bindings

A binding is one parser. Bindings for the same language are grouped in a directory named after the language.

```text
parser_bindings/
├── clang/          # grouping only: contains no code
│   ├── libclang/   # libclang through its Python bindings (clang.cindex), including the compilation database
│   └── json_ast/   # the JSON AST dump of the clang executable
├── python/         # grouping only: contains no code
│   ├── ast/        # Python standard library ast
│   └── libcst/     # libcst
├── tree_sitter/    # tree-sitter, for all grammars it is used with
└── project/        # build artefacts and source trees: compile_commands.json, Bear, directory scans
```

Decisions:

- A grouping directory such as `clang/` or `python/` holds an `__init__.py` without imports and nothing else, so it cannot
  become a place where bindings share code.
- The two clang parsers are separate bindings: they name kinds differently (`COMPOUND_STMT` and `CompoundStmt`), so a shared
  kind map is a joined map in the sense of issue 266.
- Each binding owns its parser's vocabulary: kind maps, property names, placeholder detection and comment syntax.
- Each binding provides its own factory and pattern factory.

### Recipes

Each recipe is a package under `recipes/`, as proposed in issue 187.
A recipe holds its language-specific patterns itself, and may use other recipes.

```text
recipes/
├── cleanup_refactoring/
├── python_refactoring/
├── simplify_renaissance/
├── taut_to_python_unittest/
├── unit_to_pytest/
├── refactor_actions/       # ASTRefactorActions: reusable transformations are recipes, not core
├── cli/                    # the rejuvenate and taut2test commands
└── examples/               # the example applications that are now in src/rejuvenation
```

Decisions:

- There is no separate library directory: reusable transformations, such as `ASTRefactorActions`, are recipes.
- The `rejuvenation` package is dissolved: its command line moves to `recipes/cli/`, its examples to `recipes/examples/`.

### Public API

Decisions:

- Each package lists its public API in `__all__` of its `__init__.py`. Code outside the package imports from the package,
  not from its modules: `from renaissance.core.matching import match_pattern`.
- Some symbols exist only for parser bindings to implement the model. They are exported too, and marked *binding* below.
  Recipes do not use them.
- Everything not listed is internal. Unit tests of the package itself may use internal symbols.

The tables below are a first draft. The column *now in* gives the current module, relative to `src/renaissance/`.

#### `core.model`

| Symbol                                                          | For     | Now in                                  |
| --------------------------------------------------------------- | ------- | --------------------------------------- |
| `NodeProtocol`                                                  | all     | `syntax_tree/node_protocol.py`          |
| `SemanticKind`                                                  | all     | `syntax_tree/semantic_kind.py`          |
| `TextSegment`, `SyntaxNode`, `Siblings`                         | all     | `syntax_tree/text_segment.py` and so on |
| `ASTNode`, `ASTReference`, `VisitorResult`                      | all     | `syntax_tree/ast_node.py`               |
| `ASTFactory`                                                    | all     | `syntax_tree/ast_factory.py`            |
| `ASTFinder`, `find_nodes`, `matches_node`, `find_semantic_kind` | all     | `syntax_tree/ast_finder.py`             |
| `ASTShower`, `Displayable`                                      | all     | `syntax_tree/ast_shower.py`             |
| `traverse`                                                      | all     | `utils/ast_utils.py`                    |
| `TextUtils`                                                     | all     | `utils/text_utils.py`                   |
| `preceding_sibling`, `next_sibling`                             | binding | `utils/ast_utils.py`                    |
| `match_props`, `match_children`, `format_node`                  | binding | `utils/ast_utils.py`                    |
| `convert` (line and column to offset)                           | binding | `integrations/python/ast/util.py`       |

Internal: `display_context`, `DISPLAY_PARSER_KIND`, `process_node`.

#### `core.pattern`

| Symbol                                               | For     | Now in                        |
| ---------------------------------------------------- | ------- | ----------------------------- |
| `PatternKind`                                        | all     | `syntax_tree/pattern_kind.py` |
| `MATCH_ONE`, `MATCH_ALL`                             | binding | `integrations/__init__.py`    |
| `replace_dollar`, `use_dollar`, `detect_placeholder` | binding | `utils/ast_utils.py`          |
| `pattern_kind`                                       | binding | `syntax_tree/match_finder.py` |

A pattern type of its own (improvement plan, phase 3) does not exist yet and is not part of this draft.

#### `core.matching`

| Symbol                                                         | For     | Now in                        |
| -------------------------------------------------------------- | ------- | ----------------------------- |
| `PatternMatch`, `MatchFinder`                                  | all     | `syntax_tree/match_finder.py` |
| `match_pattern`, `find_all`, `is_match`                        | all     | `syntax_tree/match_finder.py` |
| `find_in_list`                                                 | binding | `syntax_tree/match_finder.py` |

Internal: `Variant`, `find_variants`, `is_match_tree`, `variant_in_match_stmt`, `is_match_dict`, `node_kinds_match`,
`IRRELEVANT_PROPS`, `MIS_MATCH`, `INCOMPLETE_MATCH`.

#### `core.rewriting`

| Symbol                      | For | Now in                        |
| --------------------------- | --- | ----------------------------- |
| `ASTRewriter`, `Rewritable` | all | `syntax_tree/ast_rewriter.py` |
| `Rewriter`, `Rewrite`       | all | `common/rewriter.py`          |

Internal: `DEFAULT_INDENT`.

#### `core.processing`

| Symbol                                                                | For | Now in                                |
| --------------------------------------------------------------------- | --- | ------------------------------------- |
| `ASTProcessor`                                                        | all | `syntax_tree/ast_processor.py`        |
| `BatchASTProcessor`, `process_atu`                                    | all | `syntax_tree/batch_ast_processor.py`  |
| `Action`, `IterableProvider`, `AST_FACTORY_AND_ATU`                   | all | `syntax_tree/batch_ast_processor.py`  |
| `RecipeASTProcessor`, `recipe_step`, `after_step`, `final_action`     | all | `syntax_tree/recipe_ast_processor.py` |

Internal: `annotate_decorator`, `get_methods_with_decorator`.

#### Leaving the core API

| Symbol               | Moves to                                 | Reason                                        |
| -------------------- | ---------------------------------------- | --------------------------------------------- |
| `CPPUtils`           | each clang binding (internal)            | C++ specific                                  |
| `ASTRefactorActions` | `recipes.refactor_actions`               | reusable transformation, so a recipe          |
| `signature_to_id`    | `parser_bindings.tree_sitter` (internal) | only used by the tree-sitter visualizer       |
| `snake_case`         | `recipes.python_refactoring` (internal)  | only used by that recipe                      |
| `to_str`             | `recipes.python_refactoring` (internal)  | not Python specific; only used by that recipe |

#### `parser_bindings` API

The public API of a binding serves the tests, the recipes with an exemption, and the bindings' own documentation.

- `clang.libclang`: `ClangASTNode`, `ClangTranslationUnit`, `ClangAdapter`, `CompilationDatabase`, its own pattern factories
  for C and C++, and its own `is_clang_*` predicates.
- `clang.json_ast`: `ClangJsonASTNode`, `ClangJsonTranslationUnit`, its own pattern factories for C and C++, and its own
  `is_clang_*` predicates.
- `python.ast`: `PythonRstNode`, `PythonRstTranslationUnit`, `PythonRSTReference`, `ASTExtension`, `PythonExtractor`,
  `convert_function`, and its own factory and pattern factory.
- `python.libcst`: `PythonCstNode`, `PythonCstTranslationUnit`, and its own factory and pattern factory.
- `tree_sitter`: `TreeSitterAdapter`, `TreeSitterPatternFactory`, `LST`, `LSTNode`, `LstVisualizer`, `Extractor`,
  `BaseCodeGraphExtractor`, `PythonCodeGraphExtractor`, `JavaCodeGraphExtractor`, `CppCodeGraphExtractor`.
- `project`: `ProjectScanner`, `CppScanner`, `BearCppScanner`, `JavaScanner`, `PythonScanner`.

Today `PythonFactory`, `PythonPatternFactory` and `PythonPattern` serve the `ast`, `libcst` and tree-sitter parsers at once.
They are split, so that each binding has its own.

#### `recipes` API

Each recipe package exports its recipe; `renaissance.recipes` itself exports nothing.

| Recipe                    | Public API             |
| ------------------------- | ---------------------- |
| `cleanup_refactoring`     | `CleanupRefactoring`   |
| `python_refactoring`      | `PythonRefactoring`    |
| `simplify_renaissance`    | `SimplifyRenaissance`  |
| `taut_to_python_unittest` | `TautToPythonUnittest` |
| `unit_to_pytest`          | `UnitToPytest`         |
| `refactor_actions`        | `ASTRefactorActions`   |
| `cli`                     | `refactor`             |
| `examples`                | none                   |

### Tests

```text
test/
├── unit/                       # mirrors the source tree
│   ├── core/
│   │   ├── model/
│   │   ├── pattern/
│   │   ├── matching/
│   │   ├── rewriting/
│   │   └── processing/
│   ├── parser_bindings/
│   │   ├── clang/libclang/
│   │   ├── clang/json_ast/
│   │   ├── python/ast/
│   │   ├── python/libcst/
│   │   ├── tree_sitter/
│   │   └── project/
│   ├── recipes/
│   │   └── <recipe>/
│   └── tools/                  # mirrors tools/, which lives outside src/
├── feature/                    # was features/: *.feature, steps/, targets/
└── test_data/
```

Decisions:

- A unit test lives in the directory of the unit it tests, not of the parser it happens to use.
  A test of the matcher that parses C++ is a test of `core.matching`.
- Unit tests of the core may use parser bindings to obtain realistic trees; ten test modules of the current `syntax_tree` tests do.
  Where possible they use the test doubles instead, such as `test/syntax_tree/infra_syntax_node.py`.
- Feature tests are end to end. They may import from every layer.
- The layering rules are checked for `src/` only.

### Documentation

```text
docs/
├── user/                       # no pages about parser bindings
│   ├── concepts/
│   ├── features/
│   ├── workflows/
│   ├── core/                   # mirrors renaissance.core: model, pattern, matching, rewriting, processing
│   └── recipes/                # mirrors renaissance.recipes: one page per recipe
├── developer/
│   ├── architecture/           # including adr/ and this page
│   ├── modules/                # mirrors src/renaissance: core/, parser_bindings/, recipes/
│   ├── api/                    # mirrors src/renaissance: one reference page per package
│   ├── feature-test-map/
│   ├── tools/                  # mirrors tools/
│   └── coding-conventions.md
└── documentation-system/
```

Decisions:

- The user documentation does not describe parser bindings; which parser is used is an implementation detail.
  It may state which languages are supported.
- `docs/user/core/` and `docs/user/recipes/` follow the structure of the core and the recipes.
  `concepts/`, `features/` and `workflows/` remain organised by task.
- `docs/developer/modules/` and `docs/developer/api/` follow the structure of `src/renaissance/`.
  The parser bindings are documented there.

### Tools

`tools/` stays at the repository root. Its scripts are standalone guard rails and do not import `renaissance`.

## Invariants / guarantees

- `core` imports nothing from `parser_bindings` or `recipes`.
- Within `core`, a sub-package imports only the sub-packages below it.
- No parser binding imports from another parser binding.
- A recipe imports from a parser binding only through a recorded exemption.
- Every module under `src/` belongs to exactly one layer, and every module under `parser_bindings/` to exactly one binding.
- The core contains no language- or parser-specific facts.

## Known violations

At the time of writing, the current code violates this structure as follows.
`tools/check_layering.py` and its allowlist are the authoritative list for the violations an import check can find.

### Imports between parser bindings

Today the `ast` and `libcst` parsers share one package, `integrations/python/ast/`, and the libclang and JSON AST parsers share
`integrations/clang/`.
Imports within these packages are not yet visible to an import check; they become violations once they are split per parser.

| Importing module                          | Imported                                       | Resolution                                                                        |
| ----------------------------------------- | ---------------------------------------------- | --------------------------------------------------------------------------------- |
| `integrations/python/ast/cst_node`        | `PYTHON_KIND_MAP`, shared with the `ast` nodes | one map per binding (issue 266)                                                   |
| `integrations/python/ast/cst_node`        | `integrations/python/ast/util.convert`         | `convert` is parser-agnostic: move to `core.model`                                |
| `integrations/python/ast/factory`         | `ast`, `libcst` and tree-sitter nodes          | one factory and pattern factory per binding                                       |
| `integrations/clang/clang_ast_node`       | `CLANG_KIND_MAP`, `predicates`, `cpp_utils`    | one map, one set of predicates and one `CPPUtils` per binding                     |
| `integrations/clang/clang_json_ast_node`  | `CLANG_KIND_MAP`, `predicates`, `cpp_utils`    | as above                                                                          |
| `integrations/clang/c_pattern_factory`    | `predicates`, `cpp_utils`, shared by both      | one pattern factory per binding                                                   |
| `integrations/clang/clang_adapter`        | `integrations/tree_sitter/lst`                 | clang gets its own node type; `LSTNode` classifies kinds with the tree-sitter map |

These are resolved during the migration. The allowlist may carry them only until the step that removes them.

### Recipes importing parser bindings

| Importing module                   | Imported                                                 | Missing in the core                                                 |
| ---------------------------------- | -------------------------------------------------------- | ------------------------------------------------------------------- |
| `recipes/python_refactoring`       | `PythonFactory`, `PythonPatternFactory`, `PythonRstNode` | parsing a file and creating patterns without naming the parser      |
| `recipes/unit_to_pytest`           | `convert_function`                                       | access to the parameters of a function; it reads stdlib `ast` today |
| `rejuvenation/cli`                 | `PythonExtractor`, `PythonRstNode`, `PythonScanner`      | the same as for `python_refactoring`                                |
| `syntax_tree/ast_refactor_actions` | `CPPPatternFactory` (type-checking only)                 | a pattern factory protocol                                          |
| `rejuvenation/*_example`           | various bindings                                         | to be assessed per example                                          |

Each needs either an exemption with evidence or a core capability before the rule is enforced.

### Language-specific facts in the core

| Module                        | Symbol                                                  | Fact                                        |
| ----------------------------- | ------------------------------------------------------- | ------------------------------------------- |
| `syntax_tree/ast_rewriter.py` | `get_comment_location`, `__get_comment_after_location`  | comment delimiters `//`, `/* */`, `#`       |
| `syntax_tree/ast_rewriter.py` | `__get_depth`                                           | clang kinds `CompoundStmt`, `COMPOUND_STMT` |
| `syntax_tree/match_finder.py` | `_TOP_LEVEL_KINDS`                                      | root kinds `Module`, `TRANSLATION_UNIT`     |
| `syntax_tree/match_finder.py` | `pattern_kind`                                          | parser kinds `MatchOne`, `MatchAll`         |
| `syntax_tree/match_finder.py` | `IRRELEVANT_PROPS`                                      | clang and tree-sitter property names        |

## Related features

## Related tests

- `test/tools/test_check_layering.py`

## Related code

- `tools/check_layering.py`

## Notes

Open questions:

1. The code graph extractors (`PythonExtractor`, the `*CodeGraphExtractor` classes) are analyses and therefore candidate recipes,
   but each is written against one parser. This draft leaves them in their binding.
1. The examples that demonstrate one particular parser (`python_ast_example`, `python_cst_example`, `python_lst_example`,
   `python_rst_example`, `cpp_clang_lst_example`) document a binding rather than express intent.
   They may fit better in that binding's developer documentation or tests than in `recipes/examples/`.

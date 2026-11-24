<!--
Copyright (C) 2024-2026 TNO

Licensed under the terms specified in the LICENSE file in the root directory
of this repository, also available at:
https://github.com/TNO/Renaissance.Py/blob/main/LICENSE
-->

# Repository structure

{ #dev-architecture-repository-structure }

**Stable ID:** `ARCH-CODE-STRUCTURE`

**Status:** Accepted, for [issue 187](https://github.com/TNO/Renaissance.Py/issues/187).
It supersedes the decision record [Code repository structure](adr/14_code_repositories.md); its decisions that remain are
listed under [Carried over from the code repository decision](#carried-over-from-the-code-repository-decision).

## Purpose

Document the target structure of the source code, the tests and the documentation, the dependencies allowed between its parts,
and the public API of each package.

## Scope

This page describes *where code lives* and *what may depend on what*.
It does not describe how to get there; that is the job of the [migration plan](repository_structure_migration.md).
It does not introduce new functionality: every package listed here holds code that exists today.
Packages envisioned in issue 187 for which no code exists yet, such as semantic services, are added when that code is written.

## Definition

### Carried over from the code repository decision

- The project is one repository.
- The layers that others extend, the parser bindings and the recipes, have one directory per contribution.
  Adding a contribution adds a directory, and changes neither the core nor other contributions.
- A contribution directory may carry its own license, in a `LICENSE` file or in SPDX headers, for example for a binding that
  wraps a GPL or proprietary parser.
- The dependencies of a parser binding are meant to become an optional extra, see
  [Use uv for package and environment management](adr/07_package_management.md).
  Today every parser is a required dependency.

### Names

File and directory names separate their words by a single `_`, never by `-`, throughout the repository: the code, the tests,
the documentation and its images, and the workflows. With one separator, a page has the name of the unit it mirrors.
The only other separator is the triple `___` in the names of test files, see [Tests](#tests).
A name consists of ASCII letters, digits and `_`, with a `.` only before its extension and at the start of a hidden file, such
as `.gitignore`.
The [name check](../tools/check_names.md) enforces these names.

### Three layers

The source tree is divided into three layers.

| Layer             | Package                           | Contents                                                                    |
| ----------------- | --------------------------------- | --------------------------------------------------------------------------- |
| `core`            | `renaissance.core`                | Parser- and language-agnostic infrastructure                                |
| `parser_bindings` | `renaissance.parser_bindings`     | Integration of one concrete parser each, including build-artefact parsers   |
| `recipes`         | `renaissance.recipes`             | Analyses, transformations and applications, including the command line      |

Decisions:

- Application code, such as the command line interface, is a recipe. There is no separate application layer.
- Extractors are recipes: they analyse code and extract information from it, without changing it.
- Reading build artefacts (`compile_commands.json`, a `Makefile` via Bear, a source directory tree) is parsing,
  so the project scanners are a parser binding.
- Module names contain no triple underscore `___`. Python's own module names, such as `__init__` and `__main__`, contain none
  either. The names of the test files use it as a separator, see [Tests](#tests).
- Directory names are valid Python identifiers: lower case words, separated by a single `_`, without `.` or `-`.

### Allowed dependencies between layers

```text
recipes ──────► core ◄────── parser_bindings
   ┆                                ▲
   └┄┄┄┄┄ parser-specific only ┄┄┄┄┄┘
```

The exact rules are the Import Linter contracts in `[tool.importlinter]` of `pyproject.toml`, their single source of truth;
see [Layering check](../tools/check_layering.md). This page explains the reasons for them.
Imports of the standard library and of third-party packages are not restricted.
Imports inside an `if TYPE_CHECKING:` block count as dependencies.

#### Recipes use parser bindings only when they are parser specific

A recipe expresses its intent in terms of the core where it can, so that it runs on every parser that provides the
abstractions the core defines.
Some recipes cannot be written for a language only, because they rely on what one parser provides; such a recipe is
*parser specific*.
For example, `PythonExtractor` walks the nodes of the Python standard library `ast` parser.

- A parser-specific recipe declares each parser binding it depends on; it may depend on more than one.
  A declaration is an entry in `[tool.importlinter]` with the reason, based on the code that needs the binding.
- Any other import from a recipe into a parser binding is a violation. It is resolved by adding the missing capability to the
  core, or, if the facts show that the recipe is parser specific, by a declaration.

#### No dependencies between parser bindings

A parser binding imports nothing from another parser binding, without exceptions.
Two bindings that need similar data, such as a mapping from parser kinds to `SemanticKind`, each keep their own copy.
Duplicated mappings are acceptable; a mapping shared between bindings is not, because a key added for one parser then silently
changes the classification of another parser ([issue 266](https://github.com/TNO/Renaissance.Py/issues/266)).
What bindings genuinely share, such as `SemanticKind` and `NodeProtocol`, is common vocabulary and belongs in the core.

#### Bindings share helpers in `parser_bindings/shared/`

`parser_bindings/shared/` holds the functions that several bindings use to implement the model, such as
`equal_in_properties` and `equal_in_children` in `equal.py`, with which a binding implements node equality. It is not a
binding:

- it imports nothing from Renaissance.Py, only the standard library and third-party packages;
- only the parser bindings and its own unit tests import it.

A helper takes the facts of a binding as parameters, such as the properties that equality ignores, so each binding keeps its
own data, and no mapping is shared in the sense of issue 266.
A helper that needs the core, or that the core uses too, stays in the core: `format_node` reads a setting of `core.model`, and
`ASTNode` uses it.

#### Bindings do not use rewriting or processing

No binding uses `core.rewrite` or `core.processing` today.
Information that the rewriter needs from a binding, such as the location of comments, flows through `core.model`.

### Core

The core has six sub-packages. Each may import only the sub-packages below it in this list.

| Sub-package          | Responsibility                                                                                  |
| -------------------- | ----------------------------------------------------------------------------------------------- |
| `core.processing`    | Running recipes: processors, batch processing, recipe steps and repetition until no change      |
| `core.rewrite`       | Collecting changes and applying them to the text, both node based and character based           |
| `core.match`         | Finding the occurrences of a pattern in a tree, with their placeholder bindings                 |
| `core.pattern`       | The pattern language: placeholder markers, placeholder kinds and the `$` notation               |
| `core.model`         | The AST model: node protocol, semantic kinds, text segments, finding by predicate               |
| `core.navigate`      | The navigation protocols, and the ancestors and siblings of a node                              |

`core.rewrite` imports `core.match` for one reason: the rewriter accepts a `PatternMatch` as a target and uses its
bindings to fill in a replacement. It does not use the matching algorithm.

The sub-packages for what can be done with a node are named after verbs: `core.match`, `core.rewrite` and `core.navigate`.
Their protocols are named the same way, as in `NodeNavigateProtocol`.

`renaissance.core` itself exports nothing; code imports from the sub-packages.
This avoids eager re-exports.

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
   algorithm in `core.rewrite` takes it as a parameter.

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
├── project/        # build artefacts and source trees: compile_commands.json, Bear, directory scans
└── shared/         # helpers that several bindings use; not a binding, imports nothing from Renaissance.Py
```

Decisions:

- A grouping directory such as `clang/` or `python/` holds an `__init__.py` without imports and nothing else, so it cannot
  become a place where bindings share code; `shared/` is the only such place.
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
├── ruff_utils/             # run_ruff_import_cleanup: removes the imports that a recipe left unused
├── unit_to_pytest/
├── refactor_actions/       # ASTRefactorActions: reusable transformations are recipes, not core
├── python_extractor/       # PythonExtractor: parser specific, uses python.ast
├── code_graph_extractor/   # the *CodeGraphExtractor classes: parser specific, use tree_sitter
├── cli/                    # the rejuvenate command
└── examples/               # the example applications that are now in src/rejuvenation
```

Decisions:

- There is no separate library directory: reusable transformations, such as `ASTRefactorActions`, are recipes.
- The `rejuvenation` package is dissolved: its command line moves to `recipes/cli/`, its examples to `recipes/examples/`.
- An example that shows how one parser represents code is a unit test of that parser binding, not a recipe.
  Such a test documents, for instance, that the Python `ast` parser represents `else: if` and `elif` alike.
  This applies to `cpp_clang_lst_example`, unless the facts show that the example is a parser-specific recipe.

### Public API

Decisions:

- Each package lists its public API in `__all__` of its `__init__.py`. Its `__init__.py` imports these symbols and defines
  nothing else.
- Code outside the package imports from the package, not from its modules: `from renaissance.core.match import match_pattern`.
- `format_node` exists only for the core and the parser bindings, which implement `__repr__` with it. It lives in the module
  `renaissance.core.model.format`, which `core.model` does not export. Recipes do not import it.
- The placeholder markers and the `$` notation are part of the pattern language, not of a binding, so `core.pattern` exports
  them for all.
- Everything else is internal. Unit tests of the package itself may use internal symbols.

How these decisions are checked:

- Each package has a `protected` contract in `[tool.importlinter]`: its modules may be imported only by the package itself and by
  its unit tests. One contract per package is needed, because a contract cannot name "the package of the protected module" as
  the allowed importer.
- `core.model.format` has a `protected` contract that allows the core, the parser bindings and their unit tests.
- `parser_bindings.shared` has a `forbidden` contract, which forbids every other package of Renaissance.Py, and a `protected`
  contract, which allows the parser bindings and its unit tests.
- Ruff rule F401 reports a name that an `__init__.py` imports but does not list in `__all__`.
- That an `__init__.py` defines nothing itself is enforced by review.

The `__all__` of each core sub-package is the source of truth of its public API. For the parser bindings and the recipes, the
sections below are the starting point; once a package exists, its `__all__` is the source of truth.

#### Out of tree

Code in this repository is in tree; code that uses Renaissance.Py from another project is out of tree.

- The public API is the contract with out-of-tree code. Before version 1.0, it may change without notice.
- Out-of-tree recipes may use the public API of the core, the parser bindings and the recipes.
- Out-of-tree parser bindings may use the public API of the core and of `parser_bindings/shared`.
- An out-of-tree project ships its own command line; Renaissance.Py does not discover recipes or parser bindings.
- The rules of this page cannot be enforced out of tree; there they are principles of good design. The core may raise an
  exception when out-of-tree code violates an assumption of the core.
- Out-of-tree code that is offered for inclusion follows the rules of this page.

#### Leaving the core API

| Symbol               | Moves to                                 | Reason                                        |
| -------------------- | ---------------------------------------- | --------------------------------------------- |
| `CPPUtils`           | each clang binding (internal)            | C++ specific                                  |
| `ASTRefactorActions` | `recipes.refactor_actions`               | reusable transformation, so a recipe          |
| `signature_to_id`    | `parser_bindings.tree_sitter` (internal) | only used by the tree-sitter visualizer       |
| `snake_case`         | `recipes.python_refactoring` (internal)  | only used by that recipe                      |
| `to_str`             | `recipes.python_refactoring` (internal)  | not Python specific; only used by that recipe |

#### `parser_bindings` API

The public API of a binding serves the tests, the parser-specific recipes, and the bindings' own documentation.

- `clang.libclang`: `ClangASTNode`, `ClangTranslationUnit`, `ClangAdapter`, `CompilationDatabase`, its own pattern factories
  for C and C++, and its own `is_clang_*` predicates.
- `clang.json_ast`: `ClangJsonASTNode`, `ClangJsonTranslationUnit`, its own pattern factories for C and C++, and its own
  `is_clang_*` predicates.
- `python.ast`: `PythonRstNode`, `PythonRstTranslationUnit`, `PythonRSTReference`, `ASTExtension`, `convert_function`, and its
  own factory and pattern factory.
- `python.libcst`: `PythonCstNode`, `PythonCstTranslationUnit`, and its own factory and pattern factory.
- `tree_sitter`: `TreeSitterAdapter`, `TreeSitterPatternFactory`, `LST`, `LSTNode`, `LstVisualizer`.
- `project`: `ProjectScanner`, `CppScanner`, `BearCppScanner`, `JavaScanner`, `PythonScanner`.

`shared` exports `equal_in_properties` and `equal_in_children`, now in `integrations/shared/equal.py`.

Today `PythonFactory`, `PythonPatternFactory` and `PythonPattern` serve the `ast`, `libcst` and tree-sitter parsers at once.
They are split, so that each binding has its own.

#### `recipes` API

Each recipe package exports its recipe; `renaissance.recipes` itself exports nothing.

| Recipe                 | Public API                                                           |
| ---------------------- | -------------------------------------------------------------------- |
| `cleanup_refactoring`  | `CleanupRefactoring`                                                 |
| `python_refactoring`   | `PythonRefactoring`                                                  |
| `unit_to_pytest`       | `UnitToPytest`                                                       |
| `refactor_actions`     | `ASTRefactorActions`                                                 |
| `python_extractor`     | `PythonExtractor`                                                    |
| `code_graph_extractor` | `BaseCodeGraphExtractor` and its subclasses for Python, Java and C++ |
| `cli`                  | `refactor`                                                           |
| `examples`             | none                                                                 |

### Tests

```text
test/
├── unit/                       # mirrors the source tree
│   ├── core/
│   │   ├── model/
│   │   ├── pattern/
│   │   ├── match/
│   │   ├── rewrite/
│   │   └── processing/
│   ├── parser_bindings/
│   │   ├── clang/libclang/
│   │   ├── clang/json_ast/
│   │   ├── python/ast/
│   │   ├── python/libcst/
│   │   ├── tree_sitter/
│   │   ├── project/
│   │   └── shared/
│   ├── recipes/
│   │   └── <recipe>/
├── features/                   # was features/ at the root: *.feature, steps/, targets/
├── tools/                      # mirrors tools/: the tests of each tool, shared/ mirrors tools/shared/
└── test_data/
```

Decisions:

- `test/` has one directory per kind of test: `unit/` for the code under `src/`, `features/` for the end-to-end tests,
  and `tools/` for the guard rails. `test_data/` holds input files shared by the tests.
- A unit test lives in the directory of the unit it tests, not of the parser it happens to use.
  A test of the matcher that parses C++ is a test of `core.match`.
- The tests of a module `x` are in `test_x.py` when they fit in one file, and in `test_x___<aspect>.py`, one file per aspect,
  when they do not. Several files help to organize the tests and keep them maintainable. The triple underscore separates the
  module from the aspect. An aspect is lower case words separated by `_`.
- A unit test follows the dependency rules of the unit it tests. A unit test of the core therefore uses test doubles, such as
  `test/unit/core/model/shared/infra_syntax_node.py`, instead of a parser binding. The core tests that still parse real code
  are known violations.
- Feature tests are end to end. They may import from every layer.
- The layering rules are checked for `src/`, for the unit tests and for the tools and their tests.
- That `test/unit/` mirrors the source tree, and `test/tools/` mirrors `tools/`, including the test files of each module, is
  checked by the [layout check](../tools/check_layout.md).

### Documentation

```text
docs/
├── user/                       # how to use Renaissance.Py, and its public API
│   ├── concepts/
│   ├── features/
│   ├── workflows/
│   ├── core/                   # mirrors renaissance.core: <package>/<package>.md
│   ├── parser_bindings/        # mirrors renaissance.parser_bindings: <binding>/<binding>.md
│   └── recipes/                # mirrors renaissance.recipes: <package>/<package>.md
├── developer/                  # the internal rules and structure of Renaissance.Py
│   ├── architecture/           # including adr/, modules/ and this page
│   ├── core/                   # mirrors renaissance.core: <package>/<module>.md
│   ├── parser_bindings/        # mirrors renaissance.parser_bindings: <binding>/<module>.md
│   ├── recipes/                # mirrors renaissance.recipes: <package>/<module>.md
│   ├── feature_test_map/
│   ├── tools/                  # mirrors tools/
│   └── coding_conventions.md
└── documentation_system/
```

The readers:

| Reader                                                                          | Reads                              |
| ------------------------------------------------------------------------------- | ---------------------------------- |
| End user, who runs a command line                                               | `docs/user/`                       |
| Out-of-tree recipe author or parser binder                                      | `docs/user/`                       |
| In-tree recipe author or parser binder, maintainer, architect or tool developer | `docs/user/` and `docs/developer/` |

Decisions:

- A package has a user page, `docs/user/<layer>/<package>/<package>.md`. It describes the package for its users and renders
  its public API, its `__all__`, with mkdocstrings, so the code is the single source of truth of the API. It follows the
  [package template](../../documentation_system/templates/package_template.md).
- A module has a developer page, `docs/developer/<layer>/<package>/<module>.md`. Pages per aspect, `<module>___<aspect>.md`,
  may be added beside it. It follows the [code module template](../../documentation_system/templates/code_module_template.md).
- A package that only groups packages, such as `core`, has no pages.
- The pages of the end users, `concepts/`, `features/` and `workflows/`, do not name the parser; which parser is used is an
  implementation detail. They may state which languages are supported. The user pages of the parser bindings describe their
  public API for out-of-tree authors.
- The user documentation does not describe the tools; they serve the development of Renaissance.Py, not its use.
  Only `docs/developer/tools/` documents them.
- `concepts/`, `features/` and `workflows/` remain organised by task. `docs/developer/architecture/modules/` describes groups
  of modules across packages.
- That these directories mirror the code is checked by the [layout check](../tools/check_layout.md).

For example, `src/renaissance/recipes/python_extractor/python_extractor.py` is described by
`docs/developer/recipes/python_extractor/python_extractor.md`, and its package by
`docs/user/recipes/python_extractor/python_extractor.md`. `src/renaissance/core/match/match_finder.py` is described by
`docs/developer/core/match/match_finder.md`, beside which `match_finder___<aspect>.md` may be added, and its package by
`docs/user/core/match/match.md`.

### Tools

```text
tools/                          # the guard rails, one module per tool, run as python -m tools.<tool>
└── shared/                     # functionality that several tools share; no tools
```

`tools/` stays at the repository root, outside `src/`. Its tools are guard rails, independent of everything else:

- a tool imports only the standard library, third-party packages, other tools and `tools.shared`: nothing from `renaissance`,
  `rejuvenation` or the tests;
- nothing outside the tools imports a tool, except its own tests in `test/tools/`;
- the tests in `test/tools/` import nothing from `renaissance`, `rejuvenation` or the other tests.

A tool reads the repository as files, for example `pyproject.toml`, and never as Python modules.
The [layering check](../tools/check_layering.md) enforces these rules, except for imports from `features/`, which it cannot analyse.

## Invariants / guarantees

- `core` imports nothing from `parser_bindings` or `recipes`.
- Within `core`, a sub-package imports only the sub-packages below it.
- No parser binding imports from another parser binding.
- A recipe imports from a parser binding only if it declares that it depends on that binding.
- Code outside a package imports only the package's public API.
- Every module under `src/` belongs to exactly one layer, and every module under `parser_bindings/` to exactly one binding or
  to `shared/`.
- `parser_bindings/shared/` imports nothing from Renaissance.Py, and only the parser bindings import it.
- The unit tests and the documentation mirror the code: the developer documentation per module, the user documentation per
  package.
- The tools and their tests are independent of the rest of the repository, and only the developer documentation describes them.
- The core contains no language- or parser-specific facts.

## Known violations

The migration to this structure moves code; it does not fix violations.
A violation that remains after a step of the migration is recorded as a known violation.
Once the structure is in place, each known violation gets an issue.

At the time of writing, the current code violates this structure as follows.
The violations an import check can find are the `ignore_imports` entries of the contracts in `pyproject.toml`, each with its
reason. They include recipes that import parser bindings, and unit tests of the core that parse real code.

### Imports between parser bindings

Today the `ast` and `libcst` parsers share one package, `integrations/python/ast/`, and the libclang and JSON AST parsers share
`integrations/clang/`.
Imports within these packages are not yet visible to an import check; they become violations once they are split per parser.

| Importing module                          | Imported                                       | Resolution                                                                        |
| ----------------------------------------- | ---------------------------------------------- | --------------------------------------------------------------------------------- |
| `integrations/python/ast/cst_node`        | `PYTHON_KIND_MAP`, shared with the `ast` nodes | one map per binding (issue 266)                                                   |
| `integrations/python/ast/factory`         | `ast`, `libcst` and tree-sitter nodes          | one factory and pattern factory per binding                                       |
| `integrations/clang/clang_ast_node`       | `CLANG_KIND_MAP`, `predicates`, `cpp_utils`    | one map, one set of predicates and one `CPPUtils` per binding                     |
| `integrations/clang/clang_json_ast_node`  | `CLANG_KIND_MAP`, `predicates`, `cpp_utils`    | as above                                                                          |
| `integrations/clang/c_pattern_factory`    | `predicates`, `cpp_utils`, shared by both      | one pattern factory per binding                                                   |
| `integrations/clang/clang_adapter`        | `integrations/tree_sitter/lst`                 | clang gets its own node type; `LSTNode` classifies kinds with the tree-sitter map |

When the migration splits these packages, these imports become visible, and are recorded as `ignore_imports` entries.

### Language-specific facts in the core

| Module                         | Symbol                                                  | Fact                                        |
| ------------------------------ | ------------------------------------------------------- | ------------------------------------------- |
| `core/rewrite/ast_rewriter.py` | `get_comment_location`, `__get_comment_after_location`  | comment delimiters `//`, `/* */`, `#`       |
| `core/rewrite/ast_rewriter.py` | `__get_depth`                                           | clang kinds `CompoundStmt`, `COMPOUND_STMT` |
| `core/match/match_finder.py`   | `_TOP_LEVEL_KINDS`                                      | root kinds `Module`, `TRANSLATION_UNIT`     |
| `core/match/match_finder.py`   | `pattern_kind`                                          | parser kinds `MatchOne`, `MatchAll`         |
| `core/match/match_finder.py`   | `IRRELEVANT_PROPS`                                      | clang and tree-sitter property names        |

## Related features

## Related tests

## Related code

- `[tool.importlinter]` in `pyproject.toml`
- `[tool.check_layout]` in `pyproject.toml`

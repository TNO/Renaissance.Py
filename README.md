# Renaissance.Py

[![code quality](https://github.com/TNO/Renaissance.Py/actions/workflows/code-quality.yml/badge.svg)](https://github.com/TNO/Renaissance.Py/actions/workflows/code-quality.yml)
[![Coverage report](https://img.shields.io/badge/coverage-report-informational.svg)](https://tno.github.io/Renaissance.Py/coverage/)
[![docs quality](https://github.com/TNO/Renaissance.Py/actions/workflows/docs-quality.yml/badge.svg)](https://github.com/TNO/Renaissance.Py/actions/workflows/docs-quality.yml)
[![docs](https://img.shields.io/badge/docs-mkdocs-blue.svg)](https://tno.github.io/Renaissance.Py/)
[![License: EPL 2.0](https://img.shields.io/badge/License-EPL_2.0-red.svg)](https://opensource.org/license/epl-2-0)

Renaissance.Py is a library and tool for software analysis and transformation.
Renaissance.Py provides AST matching for multiple programming languages.
Renaissance.Py combines the insights obtain with
Renaissance and [Renaissance-Ada](https://github.com/TNO/Renaissance-Ada).

## Licensing

### Github Repository

This repository is licensed under the Eclipse Public License 2.0 (EPL-2.0) as described in [LICENSE](LICENSE).

### Dual Licensing

The copyright holder may also offer this software under separate license terms.
Such alternative licenses are only granted on request and only through a separate written agreement
and are not available through this GitHub repository.
For licensing inquiries please contact: [Jos Hegge](https://esi.tno.nl/about-us/our-team/jos-hegge/)

### Contributions

To ensure that the project can continue to be distributed under non-restrictive OS licenses and
for certain applications closed source licenses, all contributions must be submitted under
the MIT License or BSD 3-Clause License and must comply with the contribution policy
described in [CONTRIBUTING.md](CONTRIBUTING.md).

Contributions that are subject to additional restrictions or incompatible license terms will not be accepted.

## Old / Misc

This project is experimental in nature and aims to explore
various concepts and techniques to apply renaissance pattern matching
in a generic way using multiple abstract syntax trees.

## Prerequisites

The Python dependencies, including the pinned `libclang` library used by `ClangASTNode`, are installed by `uv sync`.

The `clang` compiler driver is a separate, external requirement: `ClangJsonASTNode` runs it as a subprocess to obtain a JSON AST dump.
It should have the same LLVM major version as the bundled library. Print the version to install:

```powershell
uv run python -c "from importlib.metadata import version; print('.'.join(version('libclang-ng').split('.')[:3]))"
```

Then install that version. `winget` requires the exact version, while the other installers take the major version:

```powershell
winget install LLVM.LLVM --version 22.1.4
```

```bash
# Debian, Ubuntu, or WSL
wget https://apt.llvm.org/llvm.sh && chmod +x llvm.sh && sudo ./llvm.sh 22
```

```bash
# macOS
brew install llvm@22
```

Open a new terminal and check that `clang --version` reports the expected version.
On Windows the installer does not add LLVM to `PATH`, so add `C:\Program Files\LLVM\bin` to it yourself.
See [Clang prerequisites](docs/developer/modules/parser-and-ast.md#clang-prerequisites) for selecting a specific driver
when it is not on `PATH`.

The code for the experiments is located in the [src](./src) folder.

## Description

This project is a generic approach to refactor code bases with a generic AST structure.
It uses `TNO Renaissance` pattern matching.
Currently, clang native and clang python bindings are supported.

## How to add a different binding

You'll need to implement a concrete class for syntax_tree.ASTNode.
Follow the implementations of `ClangASTNode` and `ClangJsonASTNode` as an example.
If the concrete AST has a different language then also a `PatternFactory` must be added. See `CPatternFactory` for inspiration.

## Installation Procedure

The project is managed with [uv](https://docs.astral.sh/uv/). From the project directory:

```sh
uv sync --group dev
```

This creates the virtual environment, installs the interpreter pinned by `requires-python`, and installs the development tools.

## Configuration and Verification

Two steps are needed.
By following these steps, you will have configured, installed, and verified the installation for the project.

### Configure the Environment

- Open Visual Studio Code (VSCode).
- Ensure that the Python extension is installed.
- Open the project folder in VSCode, or run the following command in the project directory:

  ```sh
  code .
  ```

- Select the interpreter from the `.venv` directory.

### Verify the Installation

- Open the integrated terminal in VSCode.
- Run the following command to execute the tests:

  ```sh
  uv run pytest
  ```

- Check the output to ensure all tests pass successfully.
  Failing `clang_json` tests indicate that the `clang` driver is missing from `PATH`; see [Prerequisites](#prerequisites).

## TODO

An incomplete list of todo's:

- Improve the structure of the archive. The structure is reflected in both code and documentation.
  The last three items are absent in the user's documentation / only present in the developer's documentation as
  they are implementation details.
  See [110](https://github.com/TNO/Renaissance.Py/issues/110) and
  [187](https://github.com/TNO/Renaissance.Py/issues/187) for background information.
    - The renaissance core, the language agnostic part, containing among others AST-based pattern matching.
    - Recipes that analyse and/or transform code. Recipes can use other recipes - for higher efficiency and quality.
    - Parser bindings to connect different parsers to the core.
    - Tools that are needed in the development: They safe guard the renaissance development.
    - Tests including unit and feature tests, which internal structure reflects the structure of the whole archive.
- Improve the nodeprotocol
    - The nodeprotocol currently has mutable attributes, while most parser have readonly attributes - The protocol must get readonly attributes.
    - The nodeprotocol doesn't link an AST node to a TextSegment of the code - This link has to be added
      (probably through inheritance as an ASTNode is a TextSegment).
- Remove all issues detected by Ruff and Pyright
    - Do we want a union, e.g., X &#124; Sequence[X], or just a Sequence[X] as type hint -
      as a single element of X can always be turned into a sequence of X elements?
- Introduce the pattern class. Currently a pattern is just an ASTNode, yet a pattern is NOT an ASTNode.
  A pattern has placeholders.
    - A pattern should also have a semantic kind to ensure that exotic patterns, like created with PatternFactory.create_statement("$placeholder"),
      will only match a statement node and not every AST node.
- Improve rewriter to support both AST-based and character-based code rewritting
  (see [user documentation for details.](https://tno.github.io/Renaissance.Py/user/concepts/rewrite-semantics/))
- Improve the rewriter such that the rewriter and the parser have exactly the same (internal) representation of the code,
  as difference in representations can result in subtle errors.
- Improve pattern matcher to report multiple assignments to placeholders.
  This aspect is crucial for quality. For example, when looking for instances of

  ```python
    if $cond:
      $f($$before, $trueArg, $$after)
    else:
      $f($$before, $falseArg, $$after)
  ```

  we didn't considered the corner cases where both branches were identical.
  Fortunately, we assert that we expected only one match, and hence were pointed to these unexpected corner cases.
- Make a recursive find and replace.
    - Repeat until convergence and recursive find and replace can yield different results.
    - See the implementation in Renaissance-Ada as example.
- Make interface and implementation in Python for variable read and written by a code snippet (sequence of AST Node)
- Add tools for guard railing
    - A tool should check that the code in the renaissance core is independent of all other code.
- Minor
    - The get_properties methods of both `ClangASTNode` and `ClangJsonASTNode` are not complete yet. This might cause mismatches in the `Match_Finder`
    - C++ constructs have not been tested yet
    - An example of how to use includes in a `Pattern` must be added
    - Tests need to be added for macro handling
    - The methods `get_references` and `referred_by` must be added to `ASTNode` and implemented in the concrete classes
    - Test cases for multiple match patterns need to be added. Currently, there is only one working case in the examples
    - Comments in Clang appear incorrectly in the `ASTShower`. This seems to be a Clang issue, which is surprising

## Usage

```bash
cli <command> <src> <other-args>
```

### Inspect

Inspect the AST of a source file.

```bash
cli inspect features/targets/demo.py pass
```

it will show ast of demo.py and focus on 'pass' statements

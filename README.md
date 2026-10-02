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

## Setup for WSL
```bash
sudo apt-get install -y build-essential clang
```


The code for the experiments is located in the [src](./src) folder.

# Description
This project is a generic approach to refactor code bases with a generic AST structure.
It uses `TNO Renaissance` pattern matching.
Currently, clang native and clang python bindings are supported.

# How to add a different binding
You'll need to implement a concrete class for syntax_tree.ASTNode.
Follow the implementations of `ClangASTNode` and `ClangJsonASTNode` as an example.
If the concrete AST has a different language then also a `PatternFactory` must be added. See `CPatternFactory` for inspiration.

## Installation Procedure
To install the necessary dependencies, follow these steps:

1. **Run the Installation Script**
    - Navigate to the project directory.
    - Execute the `install.bat` script by double-clicking it or running the following command in the terminal:
      ```sh
      ./install.bat
      ```

## Configuration and Verification

1. **Configure the Environment**
    - Open Visual Studio Code (VSCode).
    - Ensure that the Python extension is installed.
    - Open the project folder in VSCode.
    - alternatively in shell goto <root>/python folder and
      ```sh
      code .
      ```

2. **Verify the Installation**
    - Open the integrated terminal in VSCode.
    - Run the following command to execute the tests:
      ```sh
      python -m unittest discover
      ```
    - Check the output to ensure all tests pass successfully.

By following these steps, you will have installed and verified the setup for the project.


## TODO

An incomplete list of todo's:

* The get_properties methods of both `ClangASTNode` and `ClangJsonASTNode` are not complete yet. This might cause mismatches in the `Match_Finder`
* C++ constructs have not been tested yet
* An example of how to use includes in a `Pattern` must be added
* Tests need to be added for macro handling
* The methods `get_references` and `referred_by` must be added to `ASTNode` and implemented in the concrete classes
* Test cases for multiple match patterns need to be added. Currently, there is only one working case in the examples
* Comments in Clang appear incorrectly in the `ASTShower`. This seems to be a Clang issue, which is surprising

## Usage

cli <command> <src> <other-args>

### Inspect

Inspect the AST of a source file.
```bash
cli inspect features/targets/demo.py pass
```
it will show ast of demo.py and focus on 'pass' statements

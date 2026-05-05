# Renaissance Experiments

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
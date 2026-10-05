# Change Log

## Breaking changes

* Removed the nominal AST hierarchy in `renaissance.integrations.types`, including `ast_type`, `KIND_MAP`, and class-based kind finder APIs.
* Use `NodeProtocol`, `SemanticKind`, `PatternKind`, `parser_kind`, and parser-local predicates instead.

## Plan for next sprints

11-05-2026

* [X] use type hierarchy to find type concisely instead of regexp
* [X] use hypothesis instead of parameterized test to get better coverage
* [X] convert more complex cases of TAUT test case and reviewed the conversion by Harry
* [X] restructure with root namespace so that it can be packaged
* [X] apply ASTProtocol to Python and ~~Clang Node~~
* [X] add ADR and set up ADR discussion process
* [X] update test to pytest using python refactoring
* [X] created a package with callable cli
* [X] expand matcher and other utils to use lst nodes
* [X] convert simple case of TAUT test case and reviewed the conversion by Harry

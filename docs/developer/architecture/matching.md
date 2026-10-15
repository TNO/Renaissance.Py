<!--
Copyright (C) 2024-2026 TNO

Licensed under the terms specified in the LICENSE file in the root directory
of this repository, also available at:
https://github.com/TNO/Renaissance.Py/blob/main/LICENSE
-->

# Matching of code

{ #dev-architecture-code-matching }

**Stable ID:** `ARCH-CODE-MATCHING`

Developing parsers is time-consuming.
We have decided to reuse existing parsers.

## MISC

We should make clear

* What is the desired behaviour for a particular language, e.g., for [Python](https://docs.python.org/3/)?
* What is behaviour "enforced" on use by using existing parser for a particular language, e.g., of the [ast parser for Python](https://docs.python.org/3/library/ast.html)?

# Copyright (C) 2024-2026 TNO
#
# Licensed under the terms specified in the LICENSE file in the root directory
# of this repository, also available at:
# https://github.com/TNO/Renaissance.Py/blob/main/LICENSE

"""AI: Example script demonstrating parsing and visualizing C++ source with the Clang LST adapter."""

import clang

from renaissance.integrations.clang.clang_adapter import ClangAdapter
from renaissance.syntax_tree import ASTShower

adapter = ClangAdapter(clang.__file__.replace("__init__.py", "native"))
lst = adapter.parse("features/targets/cpp_example.cpp")

ASTShower.show_node(lst.root)

# Copyright (C) 2024-2026 TNO
#
# Licensed under the terms specified in the LICENSE file in the root directory
# of this repository, also available at:
# https://github.com/TNO/Renaissance.Py/blob/main/LICENSE

"""Builds a codebase graph of Python modules from the Python standard library ast parser."""

from renaissance.recipes.python_extractor.python_extractor import PythonExtractor

__all__ = [
    "PythonExtractor",
]

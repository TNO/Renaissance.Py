# Copyright (C) 2024-2026 TNO
#
# Licensed under the terms specified in the LICENSE file in the root directory
# of this repository, also available at:
# https://github.com/TNO/Renaissance.Py/blob/main/LICENSE

"""The rewriter: changing the code, by replacing byte ranges of its content."""

from renaissance.core.rewrite.rewriter import Rewrite, Rewriter

__all__ = [
    "Rewrite",
    "Rewriter",
]

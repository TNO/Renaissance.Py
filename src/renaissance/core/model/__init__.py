# Copyright (C) 2024-2026 TNO
#
# Licensed under the terms specified in the LICENSE file in the root directory
# of this repository, also available at:
# https://github.com/TNO/Renaissance.Py/blob/main/LICENSE

"""The syntax tree model: the vocabulary and structure of nodes, shared by all parser bindings."""

from .node_protocol import NodeProtocol
from .semantic_kind import SemanticKind

__all__ = ["NodeProtocol", "SemanticKind"]

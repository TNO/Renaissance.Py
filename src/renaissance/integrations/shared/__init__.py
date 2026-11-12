# Copyright (C) 2024-2026 TNO
#
# Licensed under the terms specified in the LICENSE file in the root directory
# of this repository, also available at:
# https://github.com/TNO/Renaissance.Py/blob/main/LICENSE

"""The helpers that several parser bindings share.

It imports nothing from Renaissance.Py, and only the parser bindings import it.
"""

from renaissance.integrations.shared.equal import equal_in_children, equal_in_properties

__all__ = ["equal_in_children", "equal_in_properties"]

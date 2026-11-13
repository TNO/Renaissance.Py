# Copyright (C) 2024-2026 TNO
#
# Licensed under the terms specified in the LICENSE file in the root directory
# of this repository, also available at:
# https://github.com/TNO/Renaissance.Py/blob/main/LICENSE

"""AI: Placeholder helpers: conversion between dollar signs and match symbols, and placeholder detection."""

MATCH_ONE = "_MatchOne__"
MATCH_ALL = "_MatchAll__"


def replace_dollar(text: str) -> str:
    """Replace dollar-sign placeholders in the given text with their corresponding match symbols.

    Two literal dollar-sign characters (`$$`) are replaced with MATCH_ALL; a single literal dollar-sign
    character (`$`) is replaced with MATCH_ONE.
    """
    return text.replace("$$", MATCH_ALL).replace("$", MATCH_ONE)


def use_dollar(text: str) -> str:
    """Replace match symbols in the given text with their corresponding dollar-sign placeholders.

    MATCH_ALL is replaced with two literal dollar-sign characters (`$$`); MATCH_ONE is replaced with a
    single literal dollar-sign character (`$`).
    """
    return text.replace(MATCH_ALL, "$$").replace(MATCH_ONE, "$")


def detect_placeholder(signature: str, original_node_type: str) -> tuple[bool, str, str]:
    """Detect if the given signature represents a placeholder symbol.

    Returns:
        (is_placeholder, coerced_node_type, placeholder_name_or_signature)

    """
    if not signature:
        return False, original_node_type, ""
    if signature.startswith((MATCH_ALL, "$$")) and " " not in signature and "(" not in signature:
        # legacy compatibility
        return True, MATCH_ALL, signature
    if signature.startswith((MATCH_ONE, "$")) and " " not in signature and "(" not in signature:
        return True, MATCH_ONE, signature
    return False, original_node_type, "-"

# lst_toolkit/src/utils/placeholders.py
from typing import Tuple


def detect_placeholder(
    signature: str, original_node_type: str
) -> Tuple[bool, str, str]:
    """
    Detect if the given signature represents a placeholder symbol.

    Returns:
        (is_placeholder, coerced_node_type, placeholder_name_or_signature)
    """
    if not signature:
        return (False, original_node_type, "")

    # Accept both styles:
    #   - "__PHL__Name"  (requested)
    #   - "$X"           (requested)
    # Keep backward-compatibility with "__PLH_" if it already appears in patterns.
    if signature.startswith("__PHL__"):
        return (True, "placeholder", signature[len("__PHL__") :])
    if signature.startswith("__PLH_"):  # legacy compatibility
        return (True, "placeholder", signature[len("__PLH_") :])
    if signature.startswith("$") and len(signature) > 1:
        return (True, "placeholder", signature[1:])
    return (False, original_node_type, "")

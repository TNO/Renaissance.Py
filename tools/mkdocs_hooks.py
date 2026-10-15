# Copyright (C) 2024-2026 TNO
#
# Licensed under the terms specified in the LICENSE file in the root directory
# of this repository, also available at:
# https://github.com/TNO/Renaissance.Py/blob/main/LICENSE

"""MkDocs hooks for renaissance.py."""

from __future__ import annotations

import datetime
from typing import Any

from mkdocs.config.defaults import MkDocsConfig
from mkdocs.plugins import event_priority, get_plugin_logger
from mkdocs.utils.cache import download_and_cache_url

log = get_plugin_logger(__name__)

# Matches the cache duration mkdocstrings itself uses, so a successful probe warms its cache.
_CACHE_DURATION = datetime.timedelta(days=1)


@event_priority(100)  # Must run before the mkdocstrings plugin reads its own configuration.
def on_config(config: MkDocsConfig) -> MkDocsConfig:
    """Drop external inventories that cannot be fetched.

    mkdocstrings logs an error when an inventory download fails, which aborts `mkdocs build --strict`.
    An outage of, for example, docs.python.org should only cost us the cross-reference hyperlinks,
    not the whole build.
    """
    mkdocstrings = config.plugins.get("mkdocstrings")
    if mkdocstrings is None:
        return config

    for handler_name, handler_config in mkdocstrings.config.handlers.items():
        inventories = handler_config.get("inventories")
        if not inventories:
            continue
        handler_config["inventories"] = [inv for inv in inventories if _is_available(inv, handler_name)]

    return config


def _is_available(inventory: str | dict[str, Any], handler_name: str) -> bool:
    url = inventory if isinstance(inventory, str) else inventory["url"]
    try:
        download_and_cache_url(url, _CACHE_DURATION)
    except Exception as error:  # noqa: BLE001 - any failure means we cannot link to it
        # Logged below warning level on purpose: --strict must not fail on an unreachable third party.
        log.info(
            "Inventory %s is unavailable for handler '%s' (%s); cross-references to it will render unlinked",
            url,
            handler_name,
            error,
        )
        return False
    return True

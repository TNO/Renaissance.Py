"""Tests that the legacy renaissance.integrations.types module has been removed."""

import importlib

import pytest


def test_legacy_type_module_is_removed():
    """AI: Assert the removed legacy renaissance.integrations.types module can no longer be imported."""
    with pytest.raises(ModuleNotFoundError):
        importlib.import_module("renaissance.integrations.types")

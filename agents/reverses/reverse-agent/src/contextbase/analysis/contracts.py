"""Compatibility alias for contextbase_runtime.contracts."""
import importlib
import sys

_implementation = importlib.import_module("contextbase_runtime.contracts")
sys.modules[__name__] = _implementation

"""Compatibility alias for contextbase_runtime.sources."""
import importlib
import sys

_implementation = importlib.import_module("contextbase_runtime.sources")
sys.modules[__name__] = _implementation

"""Compatibility alias for contextbase_runtime.storage."""
import importlib
import sys

_implementation = importlib.import_module("contextbase_runtime.storage")
sys.modules[__name__] = _implementation

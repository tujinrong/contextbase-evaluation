"""Compatibility alias for contextbase_runtime.controller."""
import importlib
import sys

_implementation = importlib.import_module("contextbase_runtime.controller")
sys.modules[__name__] = _implementation

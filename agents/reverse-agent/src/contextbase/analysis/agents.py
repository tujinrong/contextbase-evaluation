"""Compatibility alias for contextbase_runtime.agents."""
import importlib
import sys

_implementation = importlib.import_module("contextbase_runtime.agents")
sys.modules[__name__] = _implementation

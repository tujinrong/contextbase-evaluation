"""Compatibility alias for the shared Codex transport."""
import importlib
import sys

sys.modules[__name__] = importlib.import_module("contextbase_runtime.provider")

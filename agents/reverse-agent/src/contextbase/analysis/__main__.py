"""Compatibility alias for contextbase_runtime.__main__."""
import importlib
import sys

_implementation = importlib.import_module("contextbase_runtime.__main__")
if __name__ == "__main__":
    raise SystemExit(_implementation.main())
sys.modules[__name__] = _implementation

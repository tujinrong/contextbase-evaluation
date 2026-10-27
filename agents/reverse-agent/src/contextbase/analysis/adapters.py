"""Compatibility alias for contextbase_runtime.adapters."""
import importlib
import sys

_implementation = importlib.import_module("contextbase_runtime.adapters")
if __name__ == "__main__":
    sys.stdin.reconfigure(encoding="utf-8")
    sys.stdout.reconfigure(encoding="utf-8")
    raise SystemExit(_implementation._worker_main())
sys.modules[__name__] = _implementation

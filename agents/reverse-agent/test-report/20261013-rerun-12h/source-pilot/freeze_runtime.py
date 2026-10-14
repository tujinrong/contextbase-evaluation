"""Freeze engine code as byte-identical runtime material, never application input."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import sys


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


parser = argparse.ArgumentParser()
parser.add_argument("--source", required=True, type=Path)
parser.add_argument("--destination", required=True, type=Path)
parser.add_argument("--report", required=True, type=Path)
args = parser.parse_args()
source = args.source.resolve()
destination = args.destination.resolve()
if destination.exists() or args.report.exists() or destination == source or source in destination.parents:
    raise ValueError("fresh freeze/report outside engine source is required")
all_paths = list(source.rglob("*"))
if any(path.is_symlink() or getattr(path.lstat(), "st_file_attributes", 0) & 0x400 for path in all_paths):
    raise ValueError("runtime sources must be regular files")
paths = sorted(path for path in all_paths if path.is_file() and "__pycache__" not in path.parts
               and path.suffix.lower() not in {".pyc", ".pyo"})
before = {path.relative_to(source).as_posix(): digest(path) for path in paths}
shutil.copytree(source, destination, ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo"))
copied = {path.relative_to(destination).as_posix(): digest(path) for path in destination.rglob("*") if path.is_file()}
after = {path.relative_to(source).as_posix(): digest(path) for path in paths}
if before != copied or before != after:
    raise ValueError("runtime source changed during freeze or copy is not byte-identical")
# This script runs before contextbase import, so this checks frozen resolution.
sys.path.insert(0, str(destination))
module_names = ("contextbase", "contextbase.__main__", "contextbase.ai", "contextbase.ai.__main__",
                "contextbase.ai.workflow", "contextbase.ai.provider", "contextbase.ai.prompts",
                "contextbase.ai.schemas", "contextbase.ai.validation", "contextbase.ai.iteration",
                "contextbase.ai.document_contract", "docsite", "specgen")
imports = {name: importlib.util.find_spec(name).origin for name in module_names}
if not all(str(destination) in str(path) for path in imports.values()):
    raise ValueError("engine imports are not entirely resolved to the frozen runtime")
report = {"schema": "source-pilot-frozen-runtime/1", "createdAt": datetime.now(timezone.utc).isoformat(),
          "source": str(source), "destination": str(destination), "fileCount": len(before),
          "files": copied, "sourceUnchangedDuringFreeze": before == after, "byteIdenticalCopy": before == copied,
          "imports": imports, "pythonExecutable": sys.executable,
          "scope": "full agents/reverse-agent/src excluding bytecode caches; application source is not copied here"}
args.report.parent.mkdir(parents=True, exist_ok=True)
with args.report.open("x", encoding="utf-8", newline="\n") as stream:
    json.dump(report, stream, ensure_ascii=False, indent=2)
    stream.write("\n")
print(json.dumps({"fileCount": len(before), "byteIdenticalCopy": before == copied,
                  "destination": str(destination), "imports": imports}, ensure_ascii=False))

"""Collect immutable source bytes; does not infer or assemble specification prose."""
from __future__ import annotations

import argparse
import importlib.metadata
import json
from pathlib import Path
import subprocess
import sys

from contextbase.ai import capsule
from contextbase.ai.provider import resolve_cli


parser = argparse.ArgumentParser()
parser.add_argument("--source", required=True, type=Path)
parser.add_argument("--snapshot", required=True, type=Path)
parser.add_argument("--report", required=True, type=Path)
args = parser.parse_args()
excluded = capsule.EXCLUDED_DIRECTORIES | {"maintenance"}
manifest = capsule.create(args.source, args.snapshot, project_id="test-project1",
                          excluded_directories=excluded)
state = capsule.verification_state(args.snapshot)
runtime = {
    "pythonExecutable": sys.executable,
    "pythonVersion": sys.version,
    "codexExecutable": str(resolve_cli()),
    "dependencies": {name: importlib.metadata.version(name) for name in
                     ("jsonschema", "beautifulsoup4", "markdown-it-py", "tinycss2", "Pillow")},
}
report = {
    "schema": "source-pilot-preparation/1",
    "projectId": "test-project1",
    "method": "CSharp_ASPNET",
    "mode": "source-only",
    "deadline": "2026-10-13T20:15:58Z",
    "sourceRoot": str(args.source.resolve()),
    "snapshot": str(args.snapshot.resolve()),
    "snapshotState": state,
    "snapshotFiles": len(manifest["files"]),
    "snapshotBytes": sum(entry["bytes"] for entry in manifest["files"]),
    "excludedDirectoryNames": sorted(excluded),
    "excludedMaterials": manifest["omitted"],
    "referenceSpecificationIncluded": False,
    "sourceBytesModified": False,
    "inputCodeExecutionPerformed": False,
    "semanticAnalysisPerformedByPython": False,
    "pilotDocumentPaths": ["基本設計書/01_学生検索画面.md", "詳細仕様書/CSharp_ASPNET/01_学生検索画面.md"],
    "runtime": runtime,
}
capsule.write_json(args.report, report)
print(json.dumps({"snapshot": report["snapshot"], "files": report["snapshotFiles"],
                  "bytes": report["snapshotBytes"], "state": state, "runtime": runtime}, ensure_ascii=False))

"""Record an existing AI CLI stage, engine hashes, and unchanged allowed source bytes."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

from contextbase.ai import capsule
import contextbase.ai


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def engine_state() -> list[dict]:
    directory = Path(contextbase.ai.__file__).resolve().parent
    return [{"path": str(path), "sha256": digest(path)} for path in sorted(directory.glob("*.py"))]


parser = argparse.ArgumentParser()
parser.add_argument("--receipt", required=True, type=Path)
parser.add_argument("--log", required=True, type=Path)
parser.add_argument("--snapshot", required=True, type=Path)
parser.add_argument("cli_arguments", nargs=argparse.REMAINDER)
args = parser.parse_args()
command_arguments = args.cli_arguments[1:] if args.cli_arguments[:1] == ["--"] else args.cli_arguments
if not command_arguments:
    parser.error("an AI CLI command is required after --")
manifest = capsule.verify(args.snapshot)
state = capsule.verification_state(args.snapshot)
original_root = Path(manifest["sourceRoot"])
original_before = {entry["path"]: digest(original_root / entry["path"]) for entry in manifest["files"]}
if original_before != {entry["path"]: entry["sha256"] for entry in manifest["files"]}:
    raise ValueError("allowed original sources differ from the sealed snapshot before this stage")
code_before = engine_state()
start = time.perf_counter()
started = datetime.now(timezone.utc).isoformat()
command = [sys.executable, "-X", "utf8", "-m", "contextbase", "ai", *command_arguments]
args.log.parent.mkdir(parents=True, exist_ok=True)
with args.log.open("xb") as stream:
    completed = subprocess.run(command, stdin=subprocess.DEVNULL, stdout=stream, stderr=subprocess.STDOUT)
original_after = {entry["path"]: digest(original_root / entry["path"]) for entry in manifest["files"]}
after = capsule.verification_state(args.snapshot)
cli_result = None
for line in reversed(args.log.read_text(encoding="utf-8").splitlines()):
    if line.strip():
        try:
            cli_result = json.loads(line)
        except ValueError:
            pass
        break
receipt = {
    "schema": "source-pilot-ai-stage-run/1",
    "startedAt": started,
    "endedAt": datetime.now(timezone.utc).isoformat(),
    "seconds": round(time.perf_counter() - start, 3),
    "command": command,
    "exitCode": completed.returncode,
    "cliResultStatus": cli_result.get("status") if isinstance(cli_result, dict) else None,
    "cliLog": str(args.log.resolve()),
    "cliLogSha256": digest(args.log),
    "snapshotBefore": state,
    "snapshotAfter": after,
    "snapshotUnchanged": state == after,
    "sourceBefore": original_before,
    "sourceAfter": original_after,
    "allowedOriginalSourceUnchanged": original_before == original_after,
    "engineBefore": code_before,
    "engineAfter": engine_state(),
    "inputProgramExecutionPerformed": False,
    "semanticProseAssembledByRunner": False,
}
capsule.write_json(args.receipt, receipt)
print(json.dumps({"exitCode": completed.returncode, "receipt": str(args.receipt),
                  "cliResultStatus": receipt["cliResultStatus"],
                  "snapshotUnchanged": state == after,
                  "allowedOriginalSourceUnchanged": original_before == original_after}, ensure_ascii=False))
raise SystemExit(completed.returncode or (0 if state == after and original_before == original_after else 1))

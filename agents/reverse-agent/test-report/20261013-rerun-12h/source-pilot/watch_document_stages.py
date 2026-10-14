"""Observe one fresh AI document/review pair and verify saved manuscript SHA."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import time


parser = argparse.ArgumentParser()
parser.add_argument("--job", required=True, type=Path)
parser.add_argument("--review-job", required=True, type=Path)
parser.add_argument("--output", required=True, type=Path)
parser.add_argument("--audit", required=True, type=Path)
parser.add_argument("--deadline", required=True)
args = parser.parse_args()
deadline = datetime.fromisoformat(args.deadline.replace("Z", "+00:00"))
seen: set[str] = set()
paths = (args.job / "draft-result.json", args.review_job / "review-handoff.json")
with args.audit.open("x", encoding="utf-8", newline="\n") as audit:
    while datetime.now(timezone.utc) < deadline:
        for path in paths:
            if str(path) in seen or not path.is_file():
                continue
            try:
                value = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                continue
            event = {"observedAt": datetime.now(timezone.utc).isoformat(), "job": str(args.job),
                     "artifact": str(path.resolve()), "stage": path.name,
                     "artifactSha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                     "status": value.get("status"), "documentId": value.get("documentId")}
            if path.name == "draft-result.json":
                document = args.output / value["path"]
                digest = hashlib.sha256(document.read_bytes()).hexdigest()
                if digest != value["contentSha256"]:
                    raise ValueError("Saved AI manuscript differs from draft-result")
                event.update(documentFile=str(document.resolve()), contentSha256=digest,
                             structureFindings=value["structureFindings"], analysisFacts=value["analysisFacts"],
                             analysisExecutedInThisJob=value["analysisExecutedInThisJob"])
            else:
                event.update(approved=value["approved"], documentFile=value["documentFile"],
                             documentSha256=value["documentSha256"], reviewScope=value["reviewScope"])
            line = json.dumps(event, ensure_ascii=False)
            audit.write(line + "\n")
            audit.flush()
            print(line, flush=True)
            seen.add(str(path))
        if len(seen) == len(paths):
            break
        time.sleep(10)

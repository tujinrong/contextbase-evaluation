"""Observe AI-authored batch artifacts without assembling manuscript prose."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import time


parser = argparse.ArgumentParser()
parser.add_argument("--jobs", required=True, type=Path)
parser.add_argument("--output", required=True, type=Path)
parser.add_argument("--audit", required=True, type=Path)
parser.add_argument("--deadline", required=True)
args = parser.parse_args()
deadline = datetime.fromisoformat(args.deadline.replace("Z", "+00:00"))
seen: set[str] = set()
args.audit.parent.mkdir(parents=True, exist_ok=True)
with args.audit.open("x", encoding="utf-8", newline="\n") as audit:
    while datetime.now(timezone.utc) < deadline:
        paths = sorted(args.jobs.glob("*/draft-result.json"))
        paths += sorted(args.jobs.glob("*/independent-review/review-handoff.json"))
        paths += sorted(args.jobs.glob("progress/*.json"))
        complete = args.jobs / "batch-result.json"
        if complete.is_file():
            paths.append(complete)
        for path in paths:
            if str(path) in seen:
                continue
            try:
                value = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                continue
            event = {
                "observedAt": datetime.now(timezone.utc).isoformat(),
                "artifact": str(path.resolve()),
                "artifactSha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "stage": path.name,
                "status": value.get("status"),
                "documentId": value.get("documentId"),
            }
            if path.name == "draft-result.json":
                document = args.output / value["path"]
                content_sha = hashlib.sha256(document.read_bytes()).hexdigest()
                if content_sha != value["contentSha256"]:
                    raise ValueError("Saved AI manuscript differs from its draft result")
                event.update(
                    documentFile=str(document.resolve()),
                    contentSha256=content_sha,
                    structureFindings=value["structureFindings"],
                    analysisFacts=value["analysisFacts"],
                )
            if path.name == "review-handoff.json":
                event.update(
                    approved=value["approved"],
                    documentFile=value["documentFile"],
                    documentSha256=value["documentSha256"],
                    reviewScope=value["reviewScope"],
                )
            line = json.dumps(event, ensure_ascii=False)
            audit.write(line + "\n")
            audit.flush()
            print(line, flush=True)
            seen.add(str(path))
        if complete.is_file() and str(complete) in seen:
            break
        time.sleep(10)

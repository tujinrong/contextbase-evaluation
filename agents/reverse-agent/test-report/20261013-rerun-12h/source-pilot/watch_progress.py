"""Observe saved AI stage artifacts; never read or assemble specification bodies."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import time


parser = argparse.ArgumentParser()
parser.add_argument("--jobs", required=True, type=Path)
parser.add_argument("--drafts", required=True, type=Path)
parser.add_argument("--audit", required=True, type=Path)
parser.add_argument("--deadline", required=True)
args = parser.parse_args()
deadline = datetime.fromisoformat(args.deadline.replace("Z", "+00:00"))
names = ("search-basic-02", "search-detail-02")
seen = set()
args.audit.parent.mkdir(parents=True, exist_ok=True)
with args.audit.open("x", encoding="utf-8", newline="\n") as audit:
    while datetime.now(timezone.utc) < deadline:
        for name in names:
            root = args.jobs / name
            paths = sorted(root.glob("round-*/draft-result.json"))
            paths += sorted(root.glob("round-*/independent-review/review-handoff.json"))
            if (root / "iteration-result.json").is_file():
                paths.append(root / "iteration-result.json")
            for path in paths:
                if str(path) in seen:
                    continue
                try:
                    value = json.loads(path.read_text(encoding="utf-8"))
                except (OSError, ValueError):
                    continue
                event = {"observedAt": datetime.now(timezone.utc).isoformat(), "job": name,
                         "artifact": str(path.resolve()), "artifactSha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                         "stage": path.name, "status": value.get("status"), "documentId": value.get("documentId")}
                if path.name == "draft-result.json":
                    document = args.drafts / name / path.parent.name / value["path"]
                    actual_sha = hashlib.sha256(document.read_bytes()).hexdigest()
                    if actual_sha != value["contentSha256"]:
                        raise ValueError("saved AI manuscript differs from its draft result")
                    event.update(documentFile=str(document.resolve()), contentSha256=actual_sha,
                                 structureFindings=value["structureFindings"], analysisFacts=value["analysisFacts"])
                if path.name == "review-handoff.json":
                    event.update(approved=value["approved"], documentFile=value["documentFile"],
                                 documentSha256=value["documentSha256"], reviewScope=value["reviewScope"])
                if path.name == "iteration-result.json":
                    event.update(selectedDocument=value["selectedDocument"])
                line = json.dumps(event, ensure_ascii=False)
                audit.write(line + "\n")
                audit.flush()
                print(line, flush=True)
                seen.add(str(path))
        if all(str(args.jobs / name / "iteration-result.json") in seen for name in names):
            break
        time.sleep(10)

"""Observe the fresh checkpoint-reusing document and review CLI stages."""
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
seen: set[str] = set()
names = ("search-basic-03", "search-detail-03")
with args.audit.open("x", encoding="utf-8", newline="\n") as audit:
    while datetime.now(timezone.utc) < deadline:
        for name in names:
            candidates = [args.jobs / name / "draft-result.json", args.jobs / (name + "-review") / "review-handoff.json"]
            for path in candidates:
                if str(path) in seen or not path.is_file():
                    continue
                try:
                    value = json.loads(path.read_text(encoding="utf-8"))
                except (OSError, ValueError):
                    continue
                event = {"observedAt": datetime.now(timezone.utc).isoformat(), "job": name,
                         "artifact": str(path.resolve()), "stage": path.name,
                         "artifactSha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                         "status": value.get("status"), "documentId": value.get("documentId")}
                if path.name == "draft-result.json":
                    document = args.drafts / name / value["path"]
                    digest = hashlib.sha256(document.read_bytes()).hexdigest()
                    if digest != value["contentSha256"]:
                        raise ValueError("AI manuscript differs from draft-result")
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
        if len(seen) == 4:
            break
        time.sleep(10)

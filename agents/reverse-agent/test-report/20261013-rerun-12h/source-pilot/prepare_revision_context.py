"""Pin existing AI draft/reviews as data; never assemble or change manuscript prose."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path


parser = argparse.ArgumentParser()
parser.add_argument("--document", required=True, type=Path)
parser.add_argument("--draft-result", required=True, type=Path)
parser.add_argument("--review", required=True, type=Path)
parser.add_argument("--output", required=True, type=Path)
parser.add_argument("--additional-audit", type=Path)
parser.add_argument("--additional-context", type=Path)
parser.add_argument("--structural-audit", type=Path)
args = parser.parse_args()
if args.output.exists():
    raise FileExistsError("revision context must use a fresh path")
original = args.document.read_bytes()
digest = hashlib.sha256(original).hexdigest()
draft = json.loads(args.draft_result.read_text(encoding="utf-8"))
if digest != draft["contentSha256"]:
    raise ValueError("AI manuscript bytes differ from the saved draft result")
value = {
    "classification": "SOURCE_ONLY_PINNED_AI_DRAFT_AND_SOURCE_REVIEW",
    "createdAt": datetime.now(timezone.utc).isoformat(),
    "previousDraft": original.decode("utf-8"),
    "previousDraftSha256": digest,
    "previousDraftFile": str(args.document.resolve()),
    "previousDraftResultFile": str(args.draft_result.resolve()),
    "previousIndependentReview": json.loads(args.review.read_text(encoding="utf-8")),
    "structuralFindings": draft["structureFindings"],
    "snapshot": draft["snapshot"],
    "semanticProseAssembledByPython": False,
    "reviewScope": "text-source-and-structure",
}
if args.structural_audit is not None:
    audit = json.loads(args.structural_audit.read_text(encoding="utf-8"))
    matches = [item for item in audit["documents"] if item["documentId"] == draft["documentId"]
               and item["documentSha256"] == digest]
    if len(matches) != 1:
        raise ValueError("structural audit must match this exact saved manuscript")
    value["structuralFindings"] = matches[0]["findings"]
    value["currentStructuralAudit"] = matches[0]
    value["currentStructuralAuditFile"] = str(args.structural_audit.resolve())
    value["currentStructuralAuditSha256"] = hashlib.sha256(args.structural_audit.read_bytes()).hexdigest()
for key, path in (("additionalSourceAudit", args.additional_audit),
                  ("additionalRevisionContext", args.additional_context)):
    if path is not None:
        value[key] = json.loads(path.read_text(encoding="utf-8"))
        value[key + "Sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
        value[key + "File"] = str(path.resolve())
with args.output.open("x", encoding="utf-8", newline="\n") as stream:
    json.dump(value, stream, ensure_ascii=False, indent=2)
    stream.write("\n")
if args.document.read_bytes() != original:
    raise ValueError("pinned manuscript changed while preparing revision context")
print(json.dumps({"contextFile": str(args.output.resolve()), "previousDraftSha256": digest,
                  "draftBytesUnchanged": True, "semanticProseAssembledByPython": False}, ensure_ascii=False))

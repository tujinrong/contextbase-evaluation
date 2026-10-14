"""Read source-only AI metadata and validate current draft bytes without editing."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

from contextbase.ai import validation
from contextbase.ai.validation import validate_document

parser = argparse.ArgumentParser()
parser.add_argument("--output", required=True, type=Path)
args = parser.parse_args()
report = Path(__file__).resolve().parent
repo = report.parents[4]
runtime = Path(validation.__file__).resolve().parents[2]
receipts = [(p, json.loads(p.read_text(encoding="utf-8"))) for p in report.glob("runtime-code-*.json")]
receipts = [(p, v) for p, v in receipts if Path(v["destination"]).resolve() == runtime]
if len(receipts) != 1:
    raise ValueError("inventory must use one exact recorded frozen runtime")
runtime_receipt, runtime_record = receipts[0]
runtime_before = {p.relative_to(runtime).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                  for p in runtime.rglob("*") if p.is_file() and "__pycache__" not in p.parts
                  and p.suffix.lower() not in {".pyc", ".pyo"}}
if runtime_before != runtime_record["files"]:
    raise ValueError("inventory frozen runtime differs from its complete SHA receipt")
base = repo / "agents/reverse-agent/.tmp/20261013-rerun-12h/source-only"
draft_root = repo / "test-project1/spec-analysis/CSharp_ASPNET/20261013-rerun-12h/source-only/drafts"
plans = [(base / "jobs/search-plan-01/plan-verified.json"),
         (base / "jobs/remaining-plan-01/plan-verified.json")]
docs = [item for path in plans for item in json.loads(path.read_text(encoding="utf-8"))["documents"]]
results = []
for path in (base / "jobs").rglob("draft-result.json"):
    value = json.loads(path.read_text(encoding="utf-8"))
    if value.get("snapshot", {}).get("mode") != "source-only":
        raise ValueError("inventory role may not inspect other reference modes")
    results.append((path.stat().st_mtime_ns, path, value))
review_handoffs = []
for path in (base / "jobs").rglob("review-handoff.json"):
    review_handoffs.append((path, json.loads(path.read_text(encoding="utf-8"))))
pending = {
    "CSHARP_ASPNET-BAS-STU-01": "search-basic-08 source/structure review approved; fresh r15 all32 native geometry PASS; source07 audited v6 static projection active",
    "CSHARP_ASPNET-DET-CSharp_ASPNET-SCR-STU-001": "search-detail-09 source/structure review approved; exact new native pending; fresh v6 independent code pin review pending; static states held",
    "CSHARP_ASPNET-BAS-STU-02": "remaining-register-basic-06 saved source/structure review approved; exact new native geometry pending",
    "CSHARP_ASPNET-BAS-STU-03": "remaining-table-index-04 source/structure review approved; parent visual/formal assessment pending",
    "CSHARP_ASPNET-BAS-STU-03-M_CLASS": "remaining-mclass-04 source/structure review approved; parent visual/formal assessment pending",
    "CSHARP_ASPNET-BAS-STU-03-M_CODE": "remaining-mcode-04 source/structure review approved; parent visual/formal assessment pending",
    "CSHARP_ASPNET-BAS-STU-03-M_STUDENT": "remaining-mstudent-04 source/structure review approved; parent visual/formal assessment pending; old invalid-location review retained",
    "CSHARP_ASPNET-BAS-STU-03-M_CODE_CATEGORY": "no new body revision planned; parent visual/formal evaluation pending",
    "CSHARP_ASPNET-BAS-STU-03-T_OPERATION_LOG": "remaining-oplog-04 source/structure approved by fresh review-r02; first transport failure preserved and not adopted; parent native/formal pending",
    "CSHARP_ASPNET-BAS-STU-04": "remaining-code-design-04 source/structure review approved; parent native/formal pending",
    "CSHARP_ASPNET-DET-CSharp_ASPNET-SCR-STU-002": "remaining-register-detail-05 source review major1 requires active source09 remaining-register-detail-06 branch value-transfer repair",
}
entries = []
for doc in docs:
    candidates = sorted((r for r in results if r[2]["documentId"] == doc["id"]), reverse=True)
    item = {"documentId": doc["id"], "canonicalPath": doc["path"], "kind": doc["kind"],
            "adopted": False, "pendingWork": pending.get(doc["id"], "initial AI batch generation/review pending")}
    if candidates:
        _, result_path, draft = candidates[0]
        job_parts = result_path.relative_to(base / "jobs").parts
        if job_parts[0] == "remaining-batch-03":
            document = draft_root / "remaining-batch-03" / doc["path"]
        elif job_parts[0] in {"search-basic-02", "search-detail-02"}:
            document = draft_root / job_parts[0] / "round-01" / doc["path"]
        else:
            document = draft_root / job_parts[0] / doc["path"]
        raw = document.read_bytes()
        digest = hashlib.sha256(raw).hexdigest()
        if digest != draft["contentSha256"]:
            raise ValueError("saved draft bytes differ from draft result")
        reviews = [(p, v) for p, v in review_handoffs if v.get("documentSha256") == digest]
        item.update(documentFile=str(document), documentSha256=digest, draftResultFile=str(result_path),
                    analysisFacts=draft["analysisFacts"],
                    currentStructureFindings=validate_document(raw.decode("utf-8"), doc["path"],
                        expected_document_id=doc["id"], expected_kind=doc["kind"]),
                    reviewHandoffs=[{"file": str(p), "approved": v["approved"], "scope": v["reviewScope"]} for p, v in reviews],
                    documentBytesUnchanged=(document.read_bytes() == raw))
    else:
        item["initialBatchJob"] = str(base / "jobs/remaining-batch-03" / hashlib.sha256(doc["id"].encode()).hexdigest()[:16])
    entries.append(item)
value = {"classification": "SOURCE_ONLY_CURRENT_DRAFT_CANDIDATE_INVENTORY_NOT_ADOPTION",
         "createdAt": datetime.now(timezone.utc).isoformat(), "snapshotManifestSha256": "2f64e2211b1fcd7850203927fc75b5a7f2ce37457cc2afe88c8065d9f931273b",
         "runtimeFreezeReceipt": str(runtime_receipt), "runtimeAllFilesMatchReceipt": True,
         "actualValidatorImport": str(Path(validation.__file__).resolve()),
         "generationWorkers": {"remainingInitialBatch": "finished INCOMPLETE; preserved", "remainingRepairWriters": 0,
             "remainingRepairReviews": 0, "registerBasicGeometryRevision": 0, "searchDetailRevision": 0, "registerDetailRevision": "source09 remaining-register-detail-06 writer active",
             "staticProjection": "basic08 state01 active; detail final parent held"},
         "documents": entries, "savedDistinctDocumentCount": sum("documentFile" in e for e in entries),
         "semanticProseAssembledByPython": False, "formallyEvaluatedByOriginalRubric": False}
runtime_after = {p.relative_to(runtime).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                 for p in runtime.rglob("*") if p.is_file() and "__pycache__" not in p.parts
                 and p.suffix.lower() not in {".pyc", ".pyo"}}
if runtime_after != runtime_before:
    raise ValueError("frozen runtime changed during inventory inspection")
value["frozenRuntimeUnchanged"] = True
with args.output.open("x", encoding="utf-8", newline="\n") as stream:
    json.dump(value, stream, ensure_ascii=False, indent=2)
    stream.write("\n")
print(json.dumps({"inventory": str(args.output), "savedDistinctDocumentCount": value["savedDistinctDocumentCount"],
                  "status": "NOT_ADOPTED"}, ensure_ascii=False))

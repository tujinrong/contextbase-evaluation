"""Compare only recorded actual scalar properties and verify their source/evidence binding."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import os

ROOT = Path(__file__).resolve().parents[2]
def read(p): return json.loads(p.read_text(encoding="utf-8-sig"))
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def proof(p): return {"file": p.relative_to(ROOT).as_posix(), "sha256": sha(p)}

actual_file = ROOT / "build/test-results/independent-additional-interactions/partial-observations.json"
contract_file = ROOT / "tests/ui-contract.json"
actual, contract = read(actual_file), read(contract_file)
rules = {r["id"]: r for r in contract["rules"]}
issues, evidence, comparisons, complete = [], {}, 0, []
if actual["artifact"]["sha256"] != os.environ["SP2_EXPECTED_PUBLISH_SHA"]:
    issues.append({"code": "ARTIFACT_SHA"})
if actual["contractSha256"] != sha(contract_file) or actual["inputManifestSha256"] != sha(ROOT / "build/generation/inputs.json"):
    issues.append({"code": "CONTRACT_INPUT_SHA"})
for source in actual["measurementSources"]:
    if sha(ROOT / source["file"]) != source["sha256"]: issues.append({"code": "SOURCE_SHA", "file": source["file"]})
for frozen in [actual["existing337Unchanged"], actual["existingInventoryUnchanged"]]:
    if sha(ROOT / frozen["file"]) != frozen["sha256"]: issues.append({"code": "FROZEN_BASELINE_SHA", "file": frozen["file"]})
for obs in actual["observations"]:
    rule = rules[obs["ruleId"]]
    if obs["target"] != rule["target"]: issues.append({"code": "TARGET", "ruleId": rule["id"]})
    for key, value in obs["properties"].items():
        expected = rule["properties"][key]
        comparisons += 1
        if expected["op"] != "eq" or type(value) is not type(expected["value"]) or value != expected["value"]:
            issues.append({"code": "ACTUAL_DIFF", "ruleId": rule["id"], "property": key, "actual": value})
    if set(obs["properties"]) == set(rule["properties"]): complete.append(rule["id"])
    for item in obs["evidence"]: evidence[item["file"]] = item["sha256"]
    raw = read(ROOT / obs["evidence"][0]["file"])
    sql_delta = raw["actual"].get("sqlDelta")
    if "automaticSearchRequests" in obs["properties"]:
        if not sql_delta or not sql_delta["verified"] or not sql_delta["before"] or obs["properties"]["automaticSearchRequests"] != sql_delta["executedSearchQueries"]:
            issues.append({"code": "UNPROVEN_SQL_COUNTER", "ruleId": rule["id"]})
    if rule["id"] == "DUI11.state-expiry":
        detail = raw["actual"]
        counted = detail["observedSavePosts"] - detail["explicitSaveClicks"] + max(0, detail["observedCancelPosts"] - detail["explicitReloadClicks"] - detail["explicitDiscardChoiceClicks"])
        if counted != obs["properties"]["automaticReposts"] or detail["observationWindowMs"] <= 0 or not detail["dbUnchanged"]:
            issues.append({"code": "EXPIRY_COUNTER_OR_DATA"})
    if rule["id"] == "DUI11.tabs":
        detail = raw["actual"]
        if not all(detail[k] for k in ["sameAuthenticatedContext", "independentEditStateAndLease", "originalDomUnchanged", "businessDbUnchanged"]):
            issues.append({"code": "TAB_DRAFT_PRECONDITION"})
for file, digest in evidence.items():
    p = (ROOT / file).resolve()
    if not p.is_relative_to((ROOT / "build/test-results").resolve()) or sha(p) != digest:
        issues.append({"code": "EVIDENCE_SHA", "file": file})
if actual["errors"] or any(c["status"] == "PRECONDITION_OR_EXECUTION_FAILURE" for c in actual["cases"]): issues.append({"code": "CASE_ERRORS"})
record = {"schemaVersion": 1, "projectId": "sample-project2", "profileId": "CSharp_ASPNET", "runId": contract["runId"],
          "recordedAt": datetime.now(timezone.utc).isoformat(), "reviewer": "ui_quality_audit",
          "status": "PASS_RECORDED_VALUES_WITH_EXPLICIT_PARTIAL_RULES" if not issues else "FAIL_ADDITIONAL_ACTUAL_REVIEW",
          "artifact": actual["artifact"], "contractSha256": actual["contractSha256"], "inputManifestSha256": actual["inputManifestSha256"],
          "evidence": [proof(actual_file)], "measurementSources": actual["measurementSources"], "reviewSource": proof(Path(__file__)),
          "recordedRuleTargets": len(actual["observations"]), "comparedRecordedProperties": comparisons,
          "actualValueMismatches": len(issues), "boundEvidenceFiles": len(evidence), "completeRules": complete,
          "partialRules": actual["notMeasured"], "issues": issues,
          "limits": ["SQL DMV deltas apply only to exact owned DB and the finite recorded operation windows; all pre-existing plan keys must survive and remain nondecreasing.",
                     "Automatic repost count subtracts explicit Save/Reload/Discard POSTs and includes only the finite operation plus700ms idle window, not an unbounded future guarantee.",
                     "The one saved new employee and temporary read-fault rename are confined to the owned Audit additional fixture; the table is restored in finally.",
                     "Unsaved EditDraft isolation supplies one property only. Server copy-state invariance belongs to the separate observer; no physical IME, OS clipboard or native BFCache is inferred.",
                     "Recorded values are compared after collection. The collector never receives expected value/operator; full UI acceptance remains pending."], "formalScore": None}
(ROOT / "build/test-results/independent-additional-interactions/review.json").write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"status": record["status"], "properties": comparisons, "completeRules": complete, "partialRules": len(actual["notMeasured"]), "issues": issues}))
raise SystemExit(bool(issues))

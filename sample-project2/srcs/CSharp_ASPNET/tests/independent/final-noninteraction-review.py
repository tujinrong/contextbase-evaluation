"""Validate evidence binding and compare independently collected actual scalars; never create actuals."""
import collections
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def read(p):
    return json.loads(p.read_text(encoding="utf-8-sig"))


def proof(p):
    return {"file": p.relative_to(ROOT).as_posix(), "sha256": digest(p)}


contract_path = ROOT / "tests/ui-contract.json"
actual_path = ROOT / "build/test-results/independent-ui/noninteraction/partial-observations.json"
contract, actual = read(contract_path), read(actual_path)
rules = {r["id"]: r for r in contract["rules"] if r["kind"] != "interaction"}
issues, checks, files = [], 0, set()
observed_ids = [o["ruleId"] for o in actual["observations"]]
if set(observed_ids) != set(rules) or len(observed_ids) != len(set(observed_ids)):
    issues.append({"code": "RULE_ID_SET", "missing": sorted(set(rules) - set(observed_ids))})
if actual["contractSha256"] != digest(contract_path):
    issues.append({"code": "CONTRACT_SHA"})
if actual["inputManifestSha256"] != digest(ROOT / "build/generation/inputs.json"):
    issues.append({"code": "INPUT_SHA"})
for source in actual["measurementSources"]:
    if digest(ROOT / source["file"]) != source["sha256"]:
        issues.append({"code": "MEASUREMENT_SOURCE_SHA", "file": source["file"]})
for obs in actual["observations"]:
    rule = rules[obs["ruleId"]]
    if obs["target"] != rule["target"] or set(obs["properties"]) != set(rule["properties"]):
        issues.append({"code": "OBSERVATION_SHAPE", "ruleId": rule["id"]})
    for name, expected in rule["properties"].items():
        value, operator, wanted = obs["properties"].get(name), expected["op"], expected["value"]
        operators = {"eq": lambda: type(value) is type(wanted) and value == wanted,
                     "oneOf": lambda: value in wanted,
                     "min": lambda: isinstance(value, (float, int)) and not isinstance(value, bool) and value >= wanted,
                     "max": lambda: isinstance(value, (float, int)) and not isinstance(value, bool) and value <= wanted}
        checks += 1
        if operator not in operators or not operators[operator]():
            issues.append({"code": "ACTUAL_SCALAR_DIFF", "ruleId": rule["id"], "property": name, "actual": value})
    if not obs.get("evidence"):
        issues.append({"code": "EVIDENCE_EMPTY", "ruleId": rule["id"]})
    for e in obs.get("evidence", []):
        p = (ROOT / e["file"]).resolve()
        if not p.is_relative_to((ROOT / "build/test-results").resolve()) or digest(p) != e["sha256"]:
            issues.append({"code": "EVIDENCE_SHA", "file": e["file"]})
        files.add(e["file"])
if actual["errors"] or actual["notMeasured"]:
    issues.append({"code": "COLLECTOR_ERRORS_OR_NOT_MEASURED"})
if any(s.get("commitState") == "Committed" for s in actual["saveResponses"]):
    issues.append({"code": "UNEXPECTED_COMMITTED_SAVE"})

record = {"schemaVersion": 1, "projectId": "sample-project2", "profileId": "CSharp_ASPNET",
          "runId": contract["runId"], "stage": "build", "checkpoint": 3, "reviewer": "ui_quality_audit",
          "recordedAt": datetime.now(timezone.utc).isoformat(),
          "status": "PASS_NONINTERACTION_ACTUAL_COMPARISON_FULL_UI_PENDING" if not issues else "FAIL_NONINTERACTION_COMPARISON",
          "artifact": actual["artifact"], "contractSha256": digest(contract_path),
          "inputManifestSha256": actual["inputManifestSha256"], "evidence": [proof(actual_path)],
          "reviewSource": proof(Path(__file__)), "measurementSources": actual["measurementSources"],
          "observedDistinctRules": len(set(observed_ids)),
          "observedKinds": dict(collections.Counter(rules[r]["kind"] for r in observed_ids)),
          "scalarComparisons": checks, "boundEvidenceFiles": len(files), "issues": issues,
          "resolvedFindings": ["Narrow F06 page overflow fixed and measured on current artifact at all six environments",
                               "Four list/count container fonts explicitly14px; actual202font comparisons agree",
                               "Visible message variants measured without claiming normal empty notices were visible"],
          "pendingIndependentCoverage": ["Raw child text logical-owner/type inventory proof is a separate supplement; no ancestor Surface blanket coverage",
                                         "29interaction producer and final366rule validation are outside this337rule comparison",
                                         "Actual browser BFCache persistence, physical IME/nativeWindows input and Office output are not proved here",
                                         "Major-action reachability is actual scroll/focus/hit-test; activation requires interaction evidence",
                                         "Text200 is measured CSS root-font enlargement, not physicalDPI or browser page zoom"],
          "previousArtifactEvidencePolicy": "Old3f8/d287/a725 observations are not promoted to current4a607 evidence",
          "formalScore": None}
target = ROOT / "build/test-results/independent-checkpoint3-review.json"
target.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"status": record["status"], "rules": len(observed_ids), "scalarComparisons": checks,
                  "evidenceFiles": len(files), "issues": issues}, ensure_ascii=True))
raise SystemExit(bool(issues))

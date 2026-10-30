"""Review actual supplementary inventory and its evidence; never manufacture measured values."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def read(p):
    return json.loads(p.read_text(encoding="utf-8-sig"))


actual_path = ROOT / "build/test-results/independent-ui/component-inventory-supplement.json"
contract_path = ROOT / "tests/ui-contract.json"
x, contract = read(actual_path), read(contract_path)
expected = {c["id"]: c for c in contract["components"]}
components = x["components"]
issues, evidence = [], {}
if set(c["id"] for c in components) != set(expected) or len({c["id"] for c in components}) != len(components):
    issues.append({"code": "COMPONENT_ID_SET"})
if x["contractSha256"] != sha(contract_path) or x["inputManifestSha256"] != sha(ROOT / "build/generation/inputs.json"):
    issues.append({"code": "CONTRACT_OR_INPUT_SHA"})
for source in x["measurementSources"] + x["frozen337SourcesUnchanged"]:
    if sha(ROOT / source["file"]) != source["sha256"]:
        issues.append({"code": "SOURCE_OR_FROZEN337_SHA", "file": source["file"]})
for c in components:
    e = expected[c["id"]]
    if c["kind"] != e["kind"] or c["textCapable"] is not e["textCapable"]:
        issues.append({"code": "NATIVE_KIND_OR_TEXT_DIFF", "id": c["id"], "actualKind": c["kind"]})
    if c["preparedState"] != e["state"] or c["visibleCount"] <= 0:
        issues.append({"code": "STATE_OR_VISIBILITY", "id": c["id"]})
    if c["textCapable"] and not any(m["visible"] and (m["directTextPresent"] or m["childTextPresent"] or m["nativeTag"] in {"input", "select", "textarea"}) for m in c["members"]):
        issues.append({"code": "NO_ACTUAL_TEXT_CAPABILITY_PROOF", "id": c["id"]})
    for item in c["evidence"]:
        evidence[item["file"]] = item["sha256"]
owner_count, direct_count = 0, 0
for state in x["states"]:
    if state.get("preparationFailed") or state.get("unresolved"):
        issues.append({"code": "UNPREPARED_OR_UNRESOLVED_STATE", "state": state["state"]})
    for item in state.get("evidence", []):
        evidence[item["file"]] = item["sha256"]
        if not item["file"].endswith(".json"):
            continue
        measured = read(ROOT / item["file"])
        for entry in measured["childOwnership"]:
            if entry.get("grantsOtherStateCoverage") is not False:
                issues.append({"code": "CROSS_STATE_COVERAGE_PROMOTION"})
            if entry.get("category") == "DIRECT_CURRENT_DOM_MATCH":
                direct_count += 1
                continue
            owner_count += 1
            if not entry["containmentObserved"] or not entry["ownerComponentIds"] or entry["textCapable"] and not entry["tupleEqual"]:
                issues.append({"code": "CHILD_OWNER_PROOF", "state": state["state"]})
    environment = state.get("environment")
    if environment and (not environment["cssResolution"] or not environment["cssResolution"]["exactQueryMatches"] or environment["dpi"] <= 0 or environment["scale"] <= 0):
        issues.append({"code": "CSS_RESOLUTION_OR_REPORTED_SCALE", "state": state["state"]})
for file, digest in evidence.items():
    target = (ROOT / file).resolve()
    if not target.is_relative_to((ROOT / "build/test-results").resolve()) or sha(target) != digest:
        issues.append({"code": "EVIDENCE_SHA", "file": file})
if x["notMeasured"] or x["errors"] or any(r.get("commitState") == "Committed" for r in x["saveResponses"]):
    issues.append({"code": "MISSING_ERRORS_OR_COMMITTED_SAVE"})
record = {"schemaVersion": 1, "projectId": "sample-project2", "profileId": "CSharp_ASPNET", "runId": contract["runId"],
          "reviewer": "ui_quality_audit", "recordedAt": datetime.now(timezone.utc).isoformat(),
          "status": "PASS_COMPONENT_INVENTORY_AND_CSS_RESOLUTION_FULL_UI_PENDING" if not issues else "FAIL_COMPONENT_INVENTORY_REVIEW",
          "artifact": x["artifact"], "contractSha256": x["contractSha256"], "inputManifestSha256": x["inputManifestSha256"],
          "measurementSources": x["measurementSources"], "reviewSource": {"file": Path(__file__).relative_to(ROOT).as_posix(), "sha256": sha(Path(__file__))},
          "evidence": [{"file": actual_path.relative_to(ROOT).as_posix(), "sha256": sha(actual_path)}],
          "logicalComponentsCompared": len(components), "componentKindAndTextComparisons": len(components) * 2,
          "explicitChildOwnerComparisons": owner_count, "directCurrentDomMembers": direct_count,
          "stateEvidenceCases": len(x["states"]), "boundEvidenceFiles": len(evidence), "environment": x["environment"], "issues": issues,
          "scope": "Actual logical native compatibility and explicit child-owner font equality only. Generic other-state selector matches do not grant that state coverage. DPI is browser CSS resolution verified by actual media queries; scale is actual devicePixelRatio, not a physical OS display setting. Existing337 results are unchanged. Missing mandatory interaction rules remain missing; no fullUI PASS is inferred.",
          "formalScore": None}
target = ROOT / "build/test-results/independent-ui/component-inventory-review.json"
target.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"status": record["status"], "components": len(components), "explicitChildOwners": owner_count,
                  "directMembers": direct_count, "evidenceFiles": len(evidence), "issues": issues}, ensure_ascii=True))
raise SystemExit(bool(issues))

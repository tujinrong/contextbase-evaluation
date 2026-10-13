"""Round6 read-only evidence preparation; no application/provider/render calls."""
from pathlib import Path
import hashlib
import json
from datetime import datetime, timezone

ROOT = Path(r"D:\開発\contextbase-evaluation").resolve()
BASE = ROOT / "agents/reverse-agent/test-report/20261013-session-pilot-01"
REPORT = BASE / "focus-review-round-06"
SCOPE_PATH = BASE / "focus-round-06/scope.json"
HANDOFF_PATH = BASE / "focus-continuation-handoff-10.json"
CAP = ROOT / "agents/reverse-agent/.tmp/20261013-tuning-01/capsules/CSharp_ASPNET-assisted"

def now():
    return datetime.now(timezone.utc).isoformat()

def read_json(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))

def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def confined(base, relative):
    path = (base / relative).resolve()
    if not path.is_relative_to(base.resolve()):
        raise ValueError("Path escapes its declared root")
    return path

def save(name, data):
    with (REPORT / name).open("x", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")

started = now()
scope_hash = sha(SCOPE_PATH)
scope = read_json(SCOPE_PATH)
handoff_hash = sha(HANDOFF_PATH)
# Only current job/identity/deadline fields are used; historical grade metadata
# in this coordination record is not evidence or input to this review.
handoff = read_json(HANDOFF_PATH)
config_path = confined(ROOT, scope["configPath"])
config = read_json(config_path)
jobs = confined(ROOT, config["jobs"])
output = confined(ROOT, config["output"])
assert handoff["activeConfig"] == scope["configPath"]
assert handoff["activeJobRoot"] == config["jobs"]
assert handoff["processSessionId"] == 33341
assert handoff["renderProcessSessionId"] == 68890
assert config["revision"] == "6.0"
assert scope["deadline"] == "2026-10-13T03:20:58Z"
assert len(scope["inputPins"]) == 8 and len(scope["runtimeFiles"]) == 13

pins = []
def pin(path, expected, kind):
    actual = sha(path)
    assert actual == expected, str(path)
    pins.append({"path":path.relative_to(ROOT).as_posix(),"sha256":actual,"bytes":path.stat().st_size,"kind":kind})

pin(SCOPE_PATH, scope_hash, "launch-scope")
pin(config_path, scope["configSha256"], "launch-config")
pin(confined(ROOT, config["plan"]), scope["planSha256"], "ai-derived-bound-plan")
pin(confined(ROOT, scope["preservedRunnerPath"]), scope["runnerSha256"], "saved-current-runner")
pin(CAP / "manifest.json", scope["snapshot"]["manifestSha256"], "capsule-manifest")
for item in scope["inputPins"]:
    pin(confined(ROOT, item["path"]), item["sha256"], "actual-launch-input")
for item in scope["runtimeFiles"]:
    pin(confined(jobs, item["runtimePath"]), item["sha256"], "actual-frozen-runtime")

manifest = read_json(CAP / "manifest.json")
assert manifest["schema"] == "reverse-ai-source-capsule/1"
assert manifest["mode"] == "training-assisted"
assert len(manifest["files"]) == 43 and len(manifest["referenceFiles"]) == 11
assert manifest["trainingReferenceAuthorizedByUser"] is True
capsule_pins = []
for item in manifest["files"]:
    relative = "sources/" + item["path"]
    path = confined(CAP, relative)
    actual = sha(path)
    assert actual == item["sha256"], relative
    capsule_pins.append({"path":relative,"sha256":actual,"bytes":path.stat().st_size,"basis":"raw-source"})
for item in manifest["referenceFiles"]:
    assert item["basis"] == "user-authorized-training-reference"
    path = confined(CAP, item["path"])
    assert path.is_relative_to(CAP / "reference-designs")
    actual = sha(path)
    assert actual == item["sha256"], item["path"]
    capsule_pins.append({"path":item["path"],"sha256":actual,"bytes":path.stat().st_size,"basis":item["basis"]})

# Previous report supplies an inventory only; every current source hash is new.
inventory = read_json(BASE / "focus-review-round-05/source-pins-before.json")
assert len(inventory["files"]) == 32
source_pins = []
for item in inventory["files"]:
    path = confined(CAP, item["path"])
    assert path.is_relative_to(CAP / "sources")
    current = sha(path)
    declared = next(p for p in capsule_pins if p["path"] == item["path"])
    assert current == declared["sha256"]
    source_pins.append({"path":item["path"],"sha256":current,"bytes":path.stat().st_size})

protected_path = BASE / "protected-before.json"
baseline_hash = sha(protected_path)
baseline = read_json(protected_path)
assert len(baseline) == 179 and len({p["path"] for p in baseline}) == 179
protected = []
for item in baseline:
    path = Path(item["path"]).resolve()
    assert path.is_relative_to(ROOT)
    current = sha(path) if path.is_file() else None
    protected.append({"path":str(path),"expectedSha256":item["sha256"],"currentSha256":current,"status":"MISSING" if current is None else "UNCHANGED" if current == item["sha256"] else "CHANGED"})
assert sha(protected_path) == baseline_hash

drift = [p["path"] for p in pins if sha(confined(ROOT,p["path"])) != p["sha256"]]
capsule_drift = [p["path"] for p in capsule_pins if sha(confined(CAP,p["path"])) != p["sha256"]]
assert not drift and not capsule_drift
assert sha(SCOPE_PATH) == scope_hash
preparation = {
    "schema":"reverse-independent-source-native-review-preparation/1",
    "round":6,"projectId":"test-project1","profile":"CSharp_ASPNET",
    "capturedAt":now(),"startedAt":started,
    "status":"WAITING_FOR_COMPLETED_NEW_MD_AND_RENDERED_PNG",
    "deadline":scope["deadline"],"jobs":config["jobs"],"output":config["output"],
    "referenceMode":"training-assisted","snapshotScope":scope["snapshot"]["scope"],
    "approved":None,"visualFidelityVerified":False,"imagesActuallyViewed":0,
    "documents":[{"documentId":doc,"sourceReviewCompleted":None,"approved":None,"imagesActuallyViewed":0} for doc in scope["documents"]],
    "coordinationIdentity":{"handoffPath":HANDOFF_PATH.relative_to(ROOT).as_posix(),"observedHandoffSha256":handoff_hash,"generationSessionId":33341,"renderSessionId":68890,"activeConfig":scope["configPath"]},
    "currentScopeChecks":[
        "Fresh completed AI raw/draft-result/published Markdown/render sourceSHA identity before freezing each new document",
        "All new layouts, processing diagrams, SQL/ER diagrams and full-text tiles actually viewed at original resolution with per-file SHA/time",
        "Source request/model/normalization/SQL type and parameter/display field traceability; document/source/rendered conditions and return values",
        "Late context revalidation and ReturnRevision NULL/value merges; Reset FormGuard400; preSQL wait cancellation; catch precedence and Unknown/SystemError cells",
        "Static routes, shared Layout/CSS/DOM, native date controls and shown modes; no invented runtime guarantees",
        "If used, authorized reference11 design-specific display/IO/shared contract/verification responsibilities recorded as separate reference-intent comparison"
    ],
    "retainedLimits":["No previous Round5 image/approval reuse", "Undrawn mode combinations, narrow widths and live HTTP/binder/DB/commit/rollback/delivery unknown", "Source-only observations and authorized-reference design meaning are separate scopes", "Formal semantic grading not performed by this agent", "No new review begins at or after deadline; partial actual coverage remains approval null"],
    "sourceProgramExecuted":False,"databaseExecuted":False,"duplicateAiOrRenderingStarted":False,"sourceOrMdOrProductionEdited":False,
    "protectedSemanticContentsRead":False,"evaluationExpectationsRead":False
}
save("source-pins-before.json",{"schema":"reverse-ai-review-source-starting-pins/1","capturedAt":now(),"round":6,"snapshot":str(CAP.relative_to(ROOT)).replace("\\","/"),"purpose":"Fresh starting hashes; old list is inventory only, not semantic coverage or approval","files":source_pins})
save("capsule-material-pins.json",{"schema":"reverse-independent-capsule-material-pins/1","capturedAt":now(),"sourceCount":43,"authorizedReferenceCount":11,"semanticContentsReadByThisPreparation":False,"files":capsule_pins,"drift":capsule_drift})
save("preparation-validation.json",{"schema":"reverse-independent-launch-pins-check/1","capturedAt":now(),"round":6,"actualInputCount":8,"actualFrozenRuntimeCount":13,"controlPins":5,"pins":pins,"beforeAfterMatch":not drift,"drift":drift,"savedRunnerIsCurrentRound6":True,"historicalMethodTestsAppliedToNewRuntime":False})
save("review-preparation.json",preparation)
protected_record={"schema":"reverse-independent-protected-sha-check/1","checkedAt":now(),"round":6,"phase":"PREPARATION","baselinePath":str(protected_path),"baselineSha256":baseline_hash,"checkScope":"SHA256 only against179 original pins; no protected contents decoded or semantically read","total":179,"unchanged":sum(p["status"]=="UNCHANGED" for p in protected),"changed":sum(p["status"]=="CHANGED" for p in protected),"missing":sum(p["status"]=="MISSING" for p in protected),"evaluatorContentsSemanticallyRead":False,"originalSpecContentsSemanticallyRead":False,"applicationExecuted":False,"results":protected}
with (BASE / "focus-protected-check-06.json").open("x",encoding="utf-8",newline="\n") as f:
    json.dump(protected_record,f,ensure_ascii=False,indent=2);f.write("\n")
print(json.dumps({"source32":len(source_pins),"capsule43plus11":len(capsule_pins),"launchPins":len(pins),"unchangedProtected":protected_record["unchanged"],"changedProtected":protected_record["changed"],"missingProtected":protected_record["missing"],"approval":None,"images":0}))

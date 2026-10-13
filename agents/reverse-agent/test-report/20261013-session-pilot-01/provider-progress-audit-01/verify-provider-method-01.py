"""Run provider method regressions and preserve exclusive logs and code pins."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import sys
import time
import unittest

report = Path(__file__).resolve().parent
agent = report.parents[2]
repo = agent.parents[1]
audit = json.loads((report / "audit.json").read_text(encoding="utf-8"))
paths = [repo / item["path"] if "path" in item else Path(item["absolutePath"])
         for item in audit["currentAndFrozenCodePins"]]
paths.append(Path(__file__).resolve())

def pins():
    return [{"path": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
            for path in paths]

before = pins()
start = time.monotonic()
with (report / "implementation-tests-02.log").open("x", encoding="utf-8", newline="\n") as stream:
    suite = unittest.defaultTestLoader.loadTestsFromName("contextbase.tests.test_ai_provider")
    result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
after = pins()
drift = [pin["path"] for pin, new in zip(before, after) if pin != new]
frozen_originals = {str(repo / item["path"]): item["sha256"] for item in audit["currentAndFrozenCodePins"]
                    if "path" in item and ("/runtime-code/" in item["path"] or item["path"].endswith("/runner-source.py"))}
frozen_drift = [pin["path"] for pin in after if pin["path"] in frozen_originals and
                pin["sha256"] != frozen_originals[pin["path"]]]
record = {
    "schema": "reverse-agent-provider-method-check/1",
    "createdAt": datetime.now(timezone.utc).isoformat(),
    "pythonExecutable": sys.executable,
    "pythonVersion": sys.version,
    "testsRun": result.testsRun,
    "failures": len(result.failures),
    "errors": len(result.errors),
    "skips": len(result.skipped),
    "seconds": round(time.monotonic() - start, 6),
    "beforePins": before,
    "afterPins": after,
    "codeDriftDuringCheck": drift,
    "frozenRound5ComparedPins": len(frozen_originals),
    "frozenRound5DriftSinceAudit": frozen_drift,
    "result": "PASS" if result.wasSuccessful() and not drift and not frozen_drift else "FAIL",
    "failedTests": [str(test) for test, _ in result.failures + result.errors],
    "scope": "provider methods and local synthetic transport children; no model or business application execution",
    "initialFailedProviderSha256": "9e5a10ab196cf30127a4596ba77538bb9c9e772f783aea240c25baa25bccf26d",
    "initialFailedTestSha256": "2a5f79276282aeb531a05f6f52f1d429f0ad12da2a370c324825cbe42a9e7942",
    "logSha256": hashlib.sha256((report / "implementation-tests-02.log").read_bytes()).hexdigest()
}
with (report / "implementation-tests-02.json").open("x", encoding="utf-8", newline="\n") as stream:
    json.dump(record, stream, ensure_ascii=False, indent=2, allow_nan=False)
    stream.write("\n")
print(json.dumps({key: record[key] for key in ("testsRun", "failures", "errors", "skips", "seconds", "result", "codeDriftDuringCheck", "frozenRound5DriftSinceAudit")}, ensure_ascii=False))
sys.exit(0 if record["result"] == "PASS" else 1)

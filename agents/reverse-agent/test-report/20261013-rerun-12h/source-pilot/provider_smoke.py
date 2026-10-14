"""Run the existing provider in a sealed source-only workspace."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from contextbase.ai import capsule
from contextbase.ai.provider import run_job


parser = argparse.ArgumentParser()
parser.add_argument("--snapshot", required=True, type=Path)
parser.add_argument("--job", required=True, type=Path)
parser.add_argument("--report", required=True, type=Path)
args = parser.parse_args()
before = capsule.verification_state(args.snapshot)
schema = {"type": "object", "properties": {"status": {"type": "string", "enum": ["SOURCE_ONLY_READY"]}},
          "required": ["status"], "additionalProperties": False}
result = run_job(args.snapshot, args.job,
                "Read manifest.json only to confirm mode=source-only. Return the JSON status SOURCE_ONLY_READY. "
                "Do not read any source files, execute source programs, or change files.", schema, 180)
after = capsule.verification_state(args.snapshot)
capsule.write_json(args.report, {"schema": "source-pilot-provider-smoke/1", "before": before, "after": after,
                               "unchanged": before == after, "exitCode": result["exit_code"],
                               "providerMetadata": result["metadata"], "usage": result["usage"]})
print(json.dumps({"status": result["metadata"]["status"], "exitCode": result["exit_code"],
                  "unchanged": before == after, "job": str(args.job)}, ensure_ascii=False))
raise SystemExit(0 if result["metadata"]["status"] == "passed" and before == after else 1)

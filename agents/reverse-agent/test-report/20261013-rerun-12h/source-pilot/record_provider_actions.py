"""Retain provider command observations separately from source evidence claims."""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path


parser = argparse.ArgumentParser()
parser.add_argument("--events", required=True, type=Path)
parser.add_argument("--output", required=True, type=Path)
parser.add_argument("--snapshot", required=True, type=Path)
args = parser.parse_args()
raw = args.events.read_bytes()
commands = []
types: Counter[str] = Counter()
event_types: Counter[str] = Counter()
for number, line in enumerate(raw.decode("utf-8").splitlines(), 1):
    value = json.loads(line)
    event_types[value.get("type", "missing")] += 1
    if value.get("type") != "item.completed":
        continue
    item = value.get("item", {})
    types[item.get("type", "missing")] += 1
    if item.get("type") == "command_execution":
        output = item.get("aggregated_output", "")
        commands.append({
            "eventLine": number,
            "command": item.get("command"),
            "exitCode": item.get("exit_code"),
            "outputCharacters": len(output),
            "outputSha256": hashlib.sha256(output.encode("utf-8")).hexdigest(),
        })
record = {
    "schema": "source-pilot-provider-action-observation/1",
    "createdAt": datetime.now(timezone.utc).isoformat(),
    "events": str(args.events.resolve()),
    "eventsSha256": hashlib.sha256(raw).hexdigest(),
    "snapshot": str(args.snapshot.resolve()),
    "eventTypes": dict(event_types),
    "completedItemTypes": dict(types),
    "commands": commands,
    "completedCommands": len(commands),
    "failedCommands": sum(item["exitCode"] != 0 for item in commands),
    "auditScope": "provider recorded tool actions; not a filesystem access trace or isolation proof",
    "commandReviewStatus": "retained-for-agent-review",
    "failedReadAttemptsAreSourceReadEvidence": False,
}
with args.output.open("x", encoding="utf-8", newline="\n") as stream:
    json.dump(record, stream, ensure_ascii=False, indent=2)
    stream.write("\n")
print(json.dumps({
    "output": str(args.output.resolve()),
    "completedCommands": record["completedCommands"],
    "failedCommands": record["failedCommands"],
    "completedItemTypes": record["completedItemTypes"],
}, ensure_ascii=False))

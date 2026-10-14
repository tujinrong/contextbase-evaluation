"""Bundle pre-existing revision control data with SHA pins, never manuscript prose."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("--context", action="append", required=True, type=Path)
parser.add_argument("--output", required=True, type=Path)
args = parser.parse_args()
value = {"classification": "SOURCE_ONLY_SHA_PINNED_REVISION_SCOPE_BUNDLE",
         "createdAt": datetime.now(timezone.utc).isoformat(), "contexts": [],
         "semanticProseAssembledByPython": False, "expectedRubricIncluded": False}
for path in args.context:
    data = path.read_bytes()
    value["contexts"].append({"file": str(path.resolve()), "sha256": hashlib.sha256(data).hexdigest(),
                              "value": json.loads(data.decode("utf-8"))})
with args.output.open("x", encoding="utf-8", newline="\n") as stream:
    json.dump(value, stream, ensure_ascii=False, indent=2)
    stream.write("\n")
print(json.dumps({"scope": str(args.output), "sha256": hashlib.sha256(args.output.read_bytes()).hexdigest()}, ensure_ascii=False))

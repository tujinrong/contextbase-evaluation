"""Hash/validate AI-authored audit data; no business extraction or application execution."""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace", type=Path, required=True)
    args = parser.parse_args()
    folder = Path(__file__).resolve().parent
    checklist = folder / "checklist.v1.json"
    seal_file = folder / "checklist.v1.seal.json"
    if seal_file.exists():
        raise SystemExit("Existing audit seal must not be overwritten")
    data = json.loads(checklist.read_text(encoding="utf-8"))
    snapshot = (args.workspace / data["snapshot"]).resolve()
    refs = data["evidenceCatalogue"]
    files: dict[str, dict[str, object]] = {}
    for ref in refs.values():
        relative = ref["path"]
        source = (snapshot / "sources" / relative).resolve()
        indexed = (snapshot / "indexed" / (relative + ".txt")).resolve()
        if not source.is_relative_to(snapshot / "sources") or not indexed.is_relative_to(snapshot / "indexed"):
            raise ValueError("Evidence escaped authorized source roots")
        raw = source.read_bytes()
        lines = raw.decode("utf-8-sig").splitlines()
        indexed_bytes = indexed.read_bytes()
        indexed_lines = indexed_bytes.decode("utf-8-sig").splitlines()
        expected = [f"{number:06d} | {line}" for number, line in enumerate(lines, 1)]
        if indexed_lines != expected:
            raise ValueError(f"Indexed evidence differs from source: {relative}")
        start, end = ref["start"], ref["end"]
        if not 1 <= start <= end <= len(lines):
            raise ValueError(f"Invalid evidence range: {relative}:{start}-{end}")
        ref["sourceSha256"] = sha(raw)
        ref["indexedSha256"] = sha(indexed_bytes)
        ref["lineRangeSha256"] = sha(("\n".join(lines[start-1:end]) + "\n").encode("utf-8"))
        ref["rangeHashEncoding"] = "UTF-8, no BOM, LF join, final LF, exact source text within inclusive lines"
        files[relative] = {"path": relative, "sourceSha256": sha(raw), "indexedSha256": sha(indexed_bytes), "lineCount": len(lines)}
    counts: dict[str, int] = {}
    for section in ("fieldCatalogue", "obligations", "unknownsAndSourceDiscrepancies", "visualChecks"):
        records = data[section]
        ids = [record["id"] for record in records]
        if len(ids) != len(set(ids)):
            raise ValueError(f"Duplicate stable IDs: {section}")
        for record in records:
            if not record["evidenceRefs"]:
                raise ValueError(f"Missing source evidence: {record['id']}")
            if not all(key in refs for key in record["evidenceRefs"]):
                raise ValueError(f"Unknown evidence reference: {record['id']}")
        counts[section] = len(records)
    now = datetime.now(timezone.utc).isoformat()
    data["lockedAtUtc"] = now
    data["sourceFiles"] = [files[key] for key in sorted(files)]
    data["integrity"] = {"sourceIndexedMatches": True, "inclusiveRangesChecked": True, "stableIdsUnique": True, "evidenceReferencesChecked": True, "counts": counts, "sourceFilesReadAndHashed": len(files), "globalSnapshotSealRead": False}
    checklist.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    seal = {"schema": "reverse-source-audit-seal/1", "lockedAtUtc": now, "checklist": checklist.name, "sha256": sha(checklist.read_bytes()), "counts": counts, "sourceFiles": data["sourceFiles"], "readScope": ["snapshot/sources", "snapshot/indexed"], "firstDraftReadBeforeLock": False}
    seal_file.write_text(json.dumps(seal, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"seal": str(seal_file), "sha256": seal["sha256"], "counts": counts, "sourceFiles": len(files)}, ensure_ascii=False))


if __name__ == "__main__":
    main()

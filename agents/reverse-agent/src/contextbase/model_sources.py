"""Build a restricted filename-to-C#-model source index from selected inventory."""
from __future__ import annotations
from collections import defaultdict
from pathlib import Path
import re
from specgen.common import decode_source


def collect_model_sources(root: Path, cfg: dict, survey: dict) -> dict[str, tuple[str, str]]:
    inputroot = (root / cfg["input"]).resolve()
    candidates = defaultdict(list)
    for entry in survey["inventory"]:
        name = entry["path"]
        if entry["status"] != "selected" or not name.endswith(".cs"):
            continue
        path = root / cfg["input"] / name
        if path.is_symlink() or not path.resolve().is_relative_to(inputroot):
            raise ValueError("Model source escapes input root")
        data = path.read_bytes()
        if len(data) > cfg.get("max_file_bytes", 8000000):
            continue
        text, _ = decode_source(data)
        typ = path.stem
        # Only a class declared in its identically named file is accepted.
        if re.search(r"\b(?:class|record)\s+" + re.escape(typ) + r"\b", text):
            candidates[typ].append((text, name))
    return {name: entries[0] for name, entries in candidates.items() if len(entries) == 1}

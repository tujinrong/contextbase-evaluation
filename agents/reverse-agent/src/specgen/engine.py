"""Discovery, resumable per-file analysis, output ownership and project generation."""
from __future__ import annotations

import fnmatch
import json
import os
import sys
import tomllib
from pathlib import Path
from typing import Any
from . import __version__
from .analyze import analyze
from .common import (EXCLUDED_DIRS, EXTENSIONS, atomic_write, decode_source, digest,
                     empty_analysis, safe_id, stable_json)
from .render import esc, feature_docs, header, qa_doc, render_tables, table


def matches(path: str, pattern: str) -> bool:
    return fnmatch.fnmatchcase(path, pattern) or (pattern.startswith("**/") and fnmatch.fnmatchcase(path, pattern[3:]))


def config(root: Path, name: str) -> dict[str, Any]:
    root = root.resolve()  # Normalize aliases (including Windows short paths) before containment checks.
    file = (root / name).resolve()
    if not file.is_relative_to(root):
        raise ValueError("設定ファイルは --root 配下に置いてください")
    with file.open("rb") as stream:
        cfg = tomllib.load(stream)
    allowed = {"input", "output", "qa", "report", "state", "exclude", "max_file_bytes", "projects", "features"}
    if set(cfg) - allowed:
        raise ValueError("不明な設定キー: " + ", ".join(sorted(set(cfg) - allowed)))
    directories = []
    for key in ("input", "output", "qa", "report", "state"):
        value = cfg.setdefault(key, ".specgen-state" if key == "state" else key)
        p = (root / value).resolve()
        if p == root or not p.is_relative_to(root):
            raise ValueError(f"{key}: root自身・root外は指定できません")
        for other in directories:
            if p.is_relative_to(other) or other.is_relative_to(p):
                raise ValueError("input/output/qa/report/state は相互に重ならない場所にしてください")
        directories.append(p)
        cfg[key] = p.relative_to(root).as_posix()
    cfg.setdefault("exclude", [])
    cfg.setdefault("max_file_bytes", 2_000_000)
    if not isinstance(cfg["max_file_bytes"], int) or cfg["max_file_bytes"] <= 0:
        raise ValueError("max_file_bytes は正の整数が必要です")
    for feature in cfg.get("features", []):
        if not feature.get("id") or not feature.get("paths") or not isinstance(feature["paths"], list):
            raise ValueError("features には id と paths 配列が必要です")
    return cfg


def projects(root: Path, cfg: dict) -> list[dict]:
    root = root.resolve()  # Normalize aliases (including Windows short paths) before containment checks.
    source = root / cfg["input"]
    result = []
    if not source.is_dir():
        raise ValueError(f"入力ディレクトリがありません: {cfg['input']}")
    if cfg.get("projects"):
        for item in cfg["projects"]:
            path = (source / item["path"]).resolve()
            if not path.is_relative_to(source) or not path.is_dir():
                raise ValueError(f"project path 不正: {item['path']}")
            result.append(dict(name=item["name"], directory=path, root_only=False))
    else:
        for p in sorted(source.iterdir()):
            if p.is_dir() and not p.is_symlink() and p.name not in EXCLUDED_DIRS:
                result.append(dict(name=p.name, directory=p, root_only=False))
        if any(p.is_file() and p.suffix.lower() in EXTENSIONS for p in source.iterdir()):
            result.append(dict(name="_root", directory=source, root_only=True))
    ids = [safe_id(p["name"]).casefold() for p in result]
    if len(ids) != len(set(ids)):
        raise ValueError("プロジェクト名が重複しています（大文字小文字も区別しません）")
    return result


def inventory(root: Path, project: dict, cfg: dict) -> list[dict]:
    root = root.resolve()  # Normalize aliases (including Windows short paths) before containment checks.
    output = []
    base = project["directory"]
    for directory, dirs, files in os.walk(base, followlinks=False):
        kept = []
        for name in sorted(dirs):
            p = Path(directory) / name
            rel = p.relative_to(base).as_posix()
            reason = ("symlink" if p.is_symlink() else "除外ディレクトリ" if name in EXCLUDED_DIRS or any(matches(rel, pat) or matches(rel + "/", pat) for pat in cfg["exclude"]) else "")
            if reason:
                output.append(dict(path=p.relative_to(root).as_posix(), relative=rel, reason=reason, selected=False))
            elif not project["root_only"]:
                kept.append(name)
        dirs[:] = kept
        for name in sorted(files):
            p = Path(directory) / name
            rel = p.relative_to(base).as_posix()
            reason = ("symlink" if p.is_symlink() else "除外パターン" if any(matches(rel, pat) for pat in cfg["exclude"]) else "対象外拡張子" if p.suffix.lower() not in EXTENSIONS else "")
            output.append(dict(path=p.relative_to(root).as_posix(), relative=rel, selected=not reason, reason=reason))
    return output


class Writer:
    def __init__(self, root: Path, state: Path, force: bool = False, allowed: tuple[Path, ...] = ()):
        self.allowed = allowed or (root / "output", root / "qa", root / "report")
        self.root, self.state, self.force = root, state, force
        self.manifest = state / "outputs.json"
        try:
            self.previous = json.loads(self.manifest.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            self.previous = {}
        self.current: dict[str, str] = {}
        self.conflicts: list[str] = []
        self.written = 0

    def write(self, path: Path, text: str) -> None:
        if not any(path.resolve().is_relative_to(p) for p in self.allowed) or path.is_symlink():
            raise ValueError("生成先のsymlink/root外への書込を拒否しました")
        key = path.relative_to(self.root).as_posix()
        desired = digest(text)
        self.current[key] = desired
        if path.exists():
            actual = digest(path.read_bytes())
            if actual != desired and actual != self.previous.get(key) and not self.force:
                self.conflicts.append(key)
                self.current[key] = self.previous.get(key, "")
                return
        self.written += int(atomic_write(path, text))
        # Record ownership immediately so interrupted runs remain resumable.
        atomic_write(self.manifest, stable_json(self.previous | self.current))

    def finish(self, clean: bool) -> list[str]:
        stale = sorted(set(self.previous) - set(self.current))
        retained = {}
        allowed = (".md", ".json")
        for key in stale:
            path = self.root / key
            valid = any(path.resolve().is_relative_to(p) for p in self.allowed) and not path.is_symlink()
            if clean and valid and path.is_file() and path.suffix in allowed and digest(path.read_bytes()) == self.previous[key]:
                path.unlink()
            else:
                retained[key] = self.previous[key]
        atomic_write(self.manifest, stable_json(retained | self.current))
        return sorted(retained)


def group_features(project: dict, files: list[dict], cfg: dict) -> list[dict]:
    result, used = [], set()
    for mapping in cfg.get("features", []):
        if not matches(project["name"], mapping.get("project", "*")):
            continue
        selected = [f for f in files if any(matches(f["relative"], pat) for pat in mapping["paths"])]
        if selected:
            result.append(dict(id=safe_id(mapping["id"]), name=mapping.get("name", mapping["id"]),
                summary=mapping.get("summary", ""), files=selected, origin="設定による機能割当"))
            used.update(f["path"] for f in selected)
    for file in files:
        if file["path"] not in used:
            result.append(dict(id="source_" + safe_id(file["relative"]), name=file["relative"], summary="",
                files=[file], origin="ソースファイル単位の暫定機能（業務境界は要確認）"))
    ids = [f["id"].casefold() for f in result]
    if len(ids) != len(set(ids)):
        raise ValueError("機能IDが重複しています")
    return result


def run(root: Path, cfg: dict, *, force: bool = False, strict: bool = False, clean: bool = False) -> dict:
    root = root.resolve()  # Normalize aliases (including Windows short paths) before containment checks.
    state = root / cfg["state"]
    state.mkdir(parents=True, exist_ok=True)
    lock = state.with_name(state.name + ".lock")
    try:
        descriptor = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError as exc:
        raise ValueError(f"実行ロックが存在します: {lock.name}。他の実行がないことを確認してから削除してください") from exc
    os.write(descriptor, f"pid={os.getpid()}\n".encode())
    os.close(descriptor)
    try:
        return _run(root, cfg, force=force, strict=strict, clean=clean)
    finally:
        lock.unlink(missing_ok=True)


def _run(root: Path, cfg: dict, *, force: bool, strict: bool, clean: bool) -> dict:
    state = root / cfg["state"]
    writer = Writer(root, state, force, tuple(root / cfg[k] for k in ("output", "qa", "report")))
    if (state / "files").is_symlink():
        raise ValueError("キャッシュディレクトリのsymlinkは許可しません")
    code_hash = digest("".join(p.name + digest(p.read_bytes()) for p in sorted(Path(__file__).parent.glob("*.py"))))
    signature = digest(stable_json(cfg) + code_hash + sys.version.split()[0])
    summary = dict(version=__version__, status="empty", parsed=0, cached=0, errors=0, partial=0, projects=[], conflicts=[])
    project_list = projects(root, cfg)
    for project in project_list:
        records, scan = [], inventory(root, project, cfg)
        for item in scan:
            if not item["selected"]:
                continue
            path = root / item["path"]
            cache_file = state / "files" / (digest(item["path"]) + ".json")
            record = empty_analysis(item["path"], EXTENSIONS[path.suffix.lower()])
            key = ""
            try:
                if path.stat().st_size > cfg["max_file_bytes"]:
                    raise ValueError("max_file_bytes を超えています。設定を見直して再実行してください")
                raw = path.read_bytes()
                sha = digest(raw)
                key = digest(signature + sha + item["path"])
                cached = None
                if not force and cache_file.exists():
                    try:
                        cached = json.loads(cache_file.read_text(encoding="utf-8"))
                    except (OSError, ValueError):
                        pass
                if isinstance(cached, dict) and cached.get("key") == key and isinstance(cached.get("analysis"), dict) and cached["analysis"].get("status") in {"ok", "partial"} and cached.get("integrity") == digest(stable_json(cached["analysis"])):
                    record = cached["analysis"]
                    summary["cached"] += 1
                else:
                    text, encoding = decode_source(raw)
                    record = analyze(text, item["path"], record["language"])
                    record.update(encoding=encoding, sha256=sha)
                    summary["parsed"] += 1
                record["relative"] = item["relative"]
            except Exception as exc:
                record.update(status="error", warnings=[f"{type(exc).__name__}: {exc}"], sha256="未取得", relative=item["relative"])
            atomic_write(cache_file, stable_json(dict(key=key, analysis=record, integrity=digest(stable_json(record)))))
            records.append(record)
            summary["errors"] += int(record["status"] == "error")
            summary["partial"] += int(record["status"] == "partial" or bool(record["warnings"]) and record["status"] != "error")
        features = group_features(project, records, cfg)
        project_id = safe_id(project["name"])
        declarations = [dict(t, path=f["path"]) for f in records for t in f["tables"]]
        base = root / cfg["output"] / project_id
        index = header(project["name"] + " — 仕様書一覧")
        index += "## 機能一覧\n\n"
        for feature in features:
            folder = base / "機能" / feature["id"]
            for filename, content in feature_docs(root, folder, feature, declarations).items():
                writer.write(folder / filename, content)
            writer.write(root / cfg["qa"] / project_id / (feature["id"] + ".md"), qa_doc(feature))
            index += f"- {esc(feature['name'])}: [基本設計書](機能/{feature['id']}/基本設計書.md) / [詳細仕様書](機能/{feature['id']}/詳細仕様書.md) / [テーブル仕様書](機能/{feature['id']}/テーブル仕様書.md)\n"
        if records:
            all_refs = [dict(c, path=f["path"]) for f in records for c in f["crud"]]
            writer.write(base / "テーブル一覧.md", render_tables(root, base / "テーブル一覧.md", declarations, all_refs))
            writer.write(base / "README.md", index + "\n[プロジェクト全体のテーブル宣言](テーブル一覧.md)\n")
        report_base = root / cfg["report"] / project_id
        unmatched = [m["id"] for m in cfg.get("features", []) if matches(project["name"], m.get("project", "*")) and not any(any(matches(f["relative"], p) for p in m["paths"]) for f in records)]
        detail = dict(project=project["name"], files=len(records), features=len(features), tables=len(declarations),
                      errors=sum(f["status"] == "error" for f in records),
                      partial=sum(f["status"] == "partial" or bool(f["warnings"]) for f in records),
                      unmatched_feature_mappings=unmatched, inventory=scan)
        detail["status"] = "empty" if not records else "error" if detail["errors"] else "partial" if detail["partial"] or unmatched else "ok"
        if unmatched:
            summary["partial"] += 1
        manifest = dict(detail, sources=[{k: f.get(k) for k in ("path", "sha256", "language", "status", "encoding", "warnings")} for f in records])
        writer.write(report_base / "manifest.json", stable_json(manifest))
        report_text = header(project["name"] + " — 解析報告") + table(["項目", "結果"], [[k, v] for k, v in detail.items() if k != "inventory"])
        report_text += "\n## ファイルごとの解析結果\n\n" + table(["ソース", "状態", "警告"], [[f["path"], f["status"], "; ".join(f["warnings"])] for f in records])
        report_text += "\n## 対象外・除外\n\n" + table(["パス", "理由"], [[s["path"], s["reason"]] for s in scan if not s["selected"]])
        writer.write(report_base / "解析報告.md", report_text)
        summary["projects"].append({k: v for k, v in detail.items() if k != "inventory"})
    total = sum(p["files"] for p in summary["projects"])
    summary["status"] = "empty" if not total else "error" if summary["errors"] else "partial" if summary["partial"] else "ok"
    home = "# 生成された仕様書\n\n"
    home += "実プロジェクトのソースがありません。`input/<プロジェクト名>/` に配置後、生成コマンドを実行してください。実仕様書はまだ生成していません。\n" if not total else "静的解析版です。未確定事項は qa、対象範囲・解析エラーは report を参照してください。\n\n"
    for p in summary["projects"]:
        if p["files"]:
            home += f"- [{esc(p['project'])}]({safe_id(p['project'])}/README.md) — {p['features']}機能 / 状態: {p['status']}\n"
    writer.write(root / cfg["output"] / "README.md", home)
    # This report changes on a warm run; specification documents do not.
    summary["conflicts"] = writer.conflicts
    if writer.conflicts:
        summary["status"] = "conflict"
    summary["exit_code"] = 1 if summary["errors"] or writer.conflicts or strict and summary["status"] != "ok" else 0
    result_path = root / cfg["report"] / "実行結果.json"
    # Reserve the report before stale detection.
    result_key = result_path.relative_to(root).as_posix()
    writer.current[result_key] = writer.previous.get(result_key, "")
    summary["obsolete_outputs"] = writer.finish(clean)
    writer.write(result_path, stable_json(summary))
    if writer.conflicts:
        summary.update(status="conflict", exit_code=1)
    return summary

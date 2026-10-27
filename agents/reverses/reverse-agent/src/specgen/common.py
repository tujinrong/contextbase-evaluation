"""Small, dependency-free utilities. Never import or execute input code."""
from __future__ import annotations

import hashlib
import json
import os
import re
from pathlib import Path
from typing import Any

EXTENSIONS = {".py": "Python", ".java": "Java", ".cs": "C#", ".js": "JavaScript",
              ".jsx": "JavaScript", ".ts": "TypeScript", ".tsx": "TypeScript", ".sql": "SQL"}
EXCLUDED_DIRS = {".git", ".svn", "node_modules", "vendor", ".venv", "venv", "__pycache__",
                 "bin", "obj", "dist", "build", "coverage", ".next", ".specgen-state"}


def digest(value: bytes | str) -> str:
    return hashlib.sha256(value.encode("utf-8") if isinstance(value, str) else value).hexdigest()


def stable_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def atomic_write(path: Path, content: str) -> bool:
    """Replace atomically; leave identical files and their timestamps untouched."""
    if path.exists() and path.read_text(encoding="utf-8") == content:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + f".tmp-{os.getpid()}")
    try:
        with temp.open("w", encoding="utf-8", newline="\n") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp, path)
    finally:
        temp.unlink(missing_ok=True)
    return True


def safe_id(name: str) -> str:
    if re.fullmatch(r"[\w-]+", name, re.UNICODE) and len(name) <= 80:
        return name
    stem = re.sub(r"[^\w-]+", "_", name, flags=re.UNICODE).strip("_")[:64] or "item"
    return stem + "_" + digest(name)[:10]


def snippet(text: str, limit: int = 360) -> str:
    """Best-effort masking, not a secret scanner. Full source is not cached."""
    text = re.sub(r"(?i)((?:password|passwd|secret|api_?key|access_?token|connectionstring)\s*[=:]\s*)"
                  r"(['\"])(.*?)\2", r"\1'[REDACTED]'", text)
    text = re.sub(r"(://)[^/@\s]+:[^/@\s]+@", r"\1[REDACTED]@", text)
    text = " ".join(text.split())
    return text if len(text) <= limit else text[:limit] + " …（省略）"


def decode_source(data: bytes) -> tuple[str, str]:
    if data.startswith((b"\xff\xfe", b"\xfe\xff")):
        return data.decode("utf-16"), "utf-16"
    if b"\0" in data:
        raise ValueError("NUL を含むためバイナリ、または未対応エンコーディングです")
    for encoding in ("utf-8-sig", "cp932"):
        try:
            return data.decode(encoding), encoding
        except UnicodeDecodeError:
            pass
    raise ValueError("UTF-8 / UTF-16(BOM付) / CP932 として読み取れません")


def empty_analysis(path: str, language: str) -> dict[str, Any]:
    return dict(path=path, language=language, status="ok", symbols=[], tables=[], crud=[], warnings=[])


# Tokens retain line/offset positions. Strings/comments are indivisible, so braces,
# commas and SQL keywords inside them cannot corrupt structural matching.
TOKEN = re.compile(
    r"(?P<comment>//[^\n]*|/\*[\s\S]*?\*/)"
    r"|(?P<string>@\"(?:\"\"|[^\"])*\"|'(?:''|\\.|[^'\\])*'|\"(?:\"\"|\\.|[^\"\\])*\"|`(?:\\.|[^`\\])*`)"
    r"|(?P<word>[\w$\uFF3F]+)|(?P<symbol>=>|\?\.|::|==|!=|<=|>=|&&|\|\||[^\s])", re.UNICODE)


SQL_TOKEN = re.compile(TOKEN.pattern.replace(r"//[^\n]*|", r"--[^\n]*|//[^\n]*|"), re.UNICODE)


def tokens(text: str, sql: bool = False) -> list[dict[str, Any]]:
    import bisect
    newlines = [-1] + [m.start() for m in re.finditer("\n", text)]
    return [dict(text=m.group(), kind=m.lastgroup, start=m.start(), end=m.end(),
                 line=bisect.bisect_left(newlines, m.start()))
            for m in (SQL_TOKEN if sql else TOKEN).finditer(text) if m.lastgroup != "comment"]


def pairs(items: list[dict[str, Any]]) -> dict[int, int]:
    opened: list[tuple[str, int]] = []
    result: dict[int, int] = {}
    for i, item in enumerate(items):
        value = item["text"]
        if item["kind"] == "symbol" and value in ("(", "[", "{"):
            opened.append((value, i))
        elif item["kind"] == "symbol" and value in (")", "]", "}"):
            if opened and opened[-1][0] == {")": "(", "]": "[", "}": "{"}[value]:
                _, start = opened.pop()
                result[start] = i
                result[i] = start
    return result


def split_top(text: str, delimiter: str = ",") -> list[str]:
    items = tokens(text)
    matching = pairs(items)
    parts, start, i = [], 0, 0
    while i < len(items):
        if items[i]["text"] in ("(", "[", "{") and i in matching:
            i = matching[i] + 1
            continue
        if items[i]["text"] == delimiter and items[i]["kind"] == "symbol":
            parts.append(text[start:items[i]["start"]].strip())
            start = items[i]["end"]
        i += 1
    parts.append(text[start:].strip())
    return [p for p in parts if p]

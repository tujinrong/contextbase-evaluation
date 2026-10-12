"""Conservative SQL declarations and literal DML extraction; no database access."""
from __future__ import annotations

import re
from typing import Any
from .common import SQL_TOKEN, pairs, snippet, split_top, tokens

IDENT = r'(?:\[[^\]]+\]|"(?:""|[^"])+"|`[^`]+`|[\w$#\u203F\u2040\u2054\uFE33\uFE34\uFE4D-\uFE4F\uFF3F]+)'
QUALIFIED = IDENT + r'(?:\s*\.\s*' + IDENT + r')*'


def identifier(value: str) -> str:
    return ".".join(p.strip().strip('[]`"') for p in re.split(r"\s*\.\s*", value.strip()))


def mask_literals(value: str) -> str:
    chars = list(value)
    for match in SQL_TOKEN.finditer(value):
        if match.lastgroup == "comment" or match.lastgroup == "string" and match.group().startswith("'"):
            for j in range(match.start(), match.end()):
                if chars[j] != "\n":
                    chars[j] = " "
    masked = "".join(chars)
    ts = tokens(masked, sql=True)
    for start, end in pairs(ts).items():
        if start < end:
            for j in range(ts[start]["start"], ts[end]["end"]):
                if chars[j] != "\n":
                    chars[j] = " "
    return "".join(chars)


def sql_facts(text: str, base_line: int = 1, ddl: bool = True) -> tuple[list[dict], list[dict], list[str]]:
    """Report CREATE TABLE declarations, not a replayed final migration schema."""
    ts = tokens(text, sql=True)
    pm = pairs(ts)
    tables, crud, warnings = [], [], []
    # Remove comments while preserving offsets and newlines; blank literals for DML.
    structural = list(text)
    for match in SQL_TOKEN.finditer(text):
        if match.lastgroup == "comment":
            for j in range(match.start(), match.end()):
                if structural[j] != "\n":
                    structural[j] = " "
    clean = "".join(structural)
    masked = list(clean)
    for token in ts:
        if token["kind"] == "string" and token["text"].startswith("'"):
            masked[token["start"]:token["end"]] = " " * (token["end"] - token["start"])
    dml_text = "".join(masked)
    # CREATE TABLE is detected by tokens rather than inside SQL string literals.
    for i, token in enumerate(ts):
        if not ddl or token["kind"] != "word" or token["text"].upper() != "CREATE":
            continue
        j = i + 1
        while j < len(ts) and ts[j]["text"].upper() in {"TEMP", "TEMPORARY", "GLOBAL", "LOCAL", "UNLOGGED"}:
            j += 1
        if j >= len(ts) or ts[j]["text"].upper() != "TABLE":
            continue
        tail = clean[ts[j]["end"]:]
        match = re.match(r"\s+(?:IF\s+NOT\s+EXISTS\s+)?(" + QUALIFIED + r")\s*\(", tail, re.I)
        if not match:
            warnings.append(f"L{token['line'] + base_line - 1}: CREATE TABLE の形式が未対応です")
            continue
        opening = ts[j]["end"] + match.end() - 1
        op = next((k for k in range(j + 1, len(ts)) if ts[k]["start"] == opening), None)
        if op is None or op not in pm:
            warnings.append(f"L{token['line'] + base_line - 1}: CREATE TABLE の括弧が閉じていません")
            continue
        closing = ts[pm[op]]["start"]
        name = identifier(match.group(1))
        body = clean[opening + 1:closing]
        columns, constraints = [], []
        search_at = opening + 1
        for part in split_top(body):
            pos = clean.find(part, search_at, closing)
            line = clean.count("\n", 0, max(pos, opening)) + base_line
            search_at = max(search_at, pos + len(part))
            if re.match(r"^(?:CONSTRAINT|PRIMARY|FOREIGN|UNIQUE|CHECK|KEY|INDEX|EXCLUDE)\b", part, re.I):
                constraints.append(snippet(part, 1000))
                continue
            col = re.match(r"^(" + IDENT + r")\s+(.+)$", part, re.S)
            if not col:
                warnings.append(f"L{line}: 列定義を解釈できません: {snippet(part)}")
                continue
            column_name, definition = identifier(col.group(1)), col.group(2)
            structural_def = mask_literals(definition)
            stop = re.search(r"\b(?:NOT\s+NULL|NULL|DEFAULT|PRIMARY\s+KEY|UNIQUE|REFERENCES|CHECK|CONSTRAINT|COMMENT|COLLATE|GENERATED|IDENTITY|AUTO_INCREMENT)\b", structural_def, re.I)
            datatype = definition[:stop.start()].strip() if stop else definition.strip()
            default = re.search(r"\bDEFAULT\b", structural_def, re.I)
            default_value = "未明記"
            if default:
                rest = structural_def[default.end():]
                stop_default = re.search(r"\b(?:NOT\s+NULL|PRIMARY|UNIQUE|REFERENCES|CHECK|COMMENT|CONSTRAINT)\b", rest, re.I)
                ending = default.end() + stop_default.start() if stop_default else len(definition)
                default_value = snippet(definition[default.end():ending].strip())
            nullable_def = structural_def[:default.start()] + structural_def[ending:] if default else structural_def
            nullable = "NOT NULL" if re.search(r"\bNOT\s+NULL\b", nullable_def, re.I) else ("NULL明記" if re.search(r"\bNULL\b", nullable_def, re.I) else "未明記（DB方言依存）")
            columns.append(dict(name=column_name, type=snippet(datatype), nullable=nullable,
                                default=default_value,
                                definition=snippet(part, 1200), line=line,
                                primary_key=bool(re.search(r"\bPRIMARY\s+KEY\b", structural_def, re.I))))
        for constraint in constraints:
            pk = re.search(r"\bPRIMARY\s+KEY\s*\(([^)]+)\)", constraint, re.I)
            if pk:
                names = [identifier(v) for v in split_top(pk.group(1))]
                for column in columns:
                    if column["name"] in names:
                        column["primary_key"] = True
                        # Do not infer PK nullability; SQLite and DB options differ.
        tables.append(dict(name=name, columns=columns, constraints=constraints, indexes=[],
                           line=token["line"] + base_line - 1,
                           end_line=ts[pm[op]]["line"] + base_line - 1, origin="CREATE TABLE 宣言"))
    # Capture separate indexes without silently treating them as columns.
    for match in re.finditer(r"\bCREATE\s+(UNIQUE\s+)?INDEX\s+(?:IF\s+NOT\s+EXISTS\s+)?(" + IDENT + r")\s+ON\s+(" + QUALIFIED + r")\s*\(([^;]+?)\)", dml_text, re.I):
        name = identifier(match.group(3))
        for table in tables:
            if table["name"] == name:
                table["indexes"].append(snippet(match.group(), 1000))
    # Literal SQL references. CTE aliases are excluded, dynamic identifiers aren't guessed.
    ctes = {m.group(1).casefold() for m in re.finditer(r"(?:\bWITH|,)\s*(\w+)\s+AS\s*\(", dml_text, re.I)}
    patterns = [(r"\bINSERT\s+INTO\s+", "C"), (r"\bUPDATE\s+", "U"),
                (r"\bDELETE\s+FROM\s+", "D"), (r"\b(?:FROM|JOIN)\s+", "R"),
                (r"\bMERGE\s+INTO\s+", "MERGE（要確認）")]
    for prefix, operation in patterns:
        for match in re.finditer(prefix + "(" + QUALIFIED + ")", dml_text, re.I):
            # SQL scalar functions use FROM with a field, not a table (TRIM/EXTRACT).
            if operation == "R" and re.search(r"\b(?:TRIM|EXTRACT|SUBSTRING)\s*\([^)]*$",dml_text[:match.start()],re.I):
                continue
            table = identifier(match.group(1))
            if table.casefold() in ctes or table.upper() in {"SELECT", "SET", "IF", "CASCADE", "RESTRICT", "NO"}:
                continue
            if operation == "U" and re.search(r"(?:ON|FOR)\s*$", dml_text[max(0, match.start() - 12):match.start()], re.I):
                continue
            if operation == "R" and re.search(r"DELETE\s*$", dml_text[max(0, match.start() - 12):match.start()], re.I):
                continue
            crud.append(dict(table=table, operation=operation, line=base_line + text.count("\n", 0, match.start()),
                             evidence="SQLリテラル／SQLファイルの静的参照"))
    if ddl and re.search(r"\b(?:ALTER\s+TABLE|DROP\s+TABLE|CREATE\s+(?:OR\s+REPLACE\s+)?(?:VIEW|PROCEDURE|FUNCTION|TRIGGER))\b", dml_text, re.I):
        warnings.append("ALTER/DROP/VIEW/ストアド等を検出。マイグレーション実行順・最終スキーマ・ストアド内部仕様は未確定です")
    return tables, crud, warnings

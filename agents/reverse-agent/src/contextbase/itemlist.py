"""Language-neutral basic item tables, based on the source-to-doc-v2 contract.

Facts are supplied by adapters. Unknown database relationships and requiredness
are never filled from a similarly named project or from a control's name.
"""
from __future__ import annotations

import html
from collections.abc import Iterable, Mapping
from typing import Any

HEADERS = ("No", "グループ", "項目名", "種類", "入出力", "DB連携項目",
           "候補取得元", "必須", "形式・桁", "説明")
NA = "‐"  # U+2010, as required by v2 (not an ASCII hyphen).
UNKNOWN = "未確認"
IO_VALUES = frozenset(("I", "O", "I／O", NA))
ROLE_IO = {"input": "I", "display": "O", "operation": NA,
           "input_output": "I／O", "static": "O"}
TYPES = {"text": "TextBox", "input": "TextBox", "number": "NumberBox",
         "textarea": "TextArea", "select": "ComboBox", "checkbox": "CheckBox",
         "radio": "RadioButton", "button": "Button", "submit": "Button",
         "reset": "Button", "output": "Label", "label": "Label",
         "textbox": "TextBox", "combobox": "ComboBox", "commandbutton": "Button",
         "optionbutton": "RadioButton", "date": "DateInput", "password": "PasswordBox"}


def cell(value: Any) -> str:
    """Escape data, including pipes/backticks, without allowing active HTML."""
    return (html.escape(str(value), quote=False).replace("|", "&#124;")
            .replace("`", "&#96;").replace("\r\n", "\n").replace("\r", "\n")
            .replace("\n", "<br>"))


def normalize(item: Mapping[str, Any], number: int, group: str = "") -> dict[str, Any]:
    if not isinstance(number, int) or number < 1:
        raise ValueError("Item numbers must start at 1")
    name = str(item.get("name", item.get("label", ""))).strip()
    if not name:
        raise ValueError(f"Item {number}: display name is missing")
    role = item.get("role")
    io = item.get("io") or ROLE_IO.get(role)
    # Do not confuse 'unknown' with 'not applicable'. Adapters must resolve role.
    if io not in IO_VALUES:
        raise ValueError(f"Item {number} ({name}): explicit I/O or a supported role is required")
    typ = str(item.get("type", ""))
    typ = TYPES.get(typ.lower(), typ or UNKNOWN)
    operation = role == "operation" or typ == "Button"
    static = role == "static"
    if operation and io != NA:
        raise ValueError(f"Item {number}: an operation button must use U+2010 for I/O")
    required = item.get("required", UNKNOWN)
    if io not in {"I", "I／O"}:
        required = NA
    elif required is True:
        required = "必須"
    elif required is False:
        required = "画面属性に指定なし（業務必須は未確認）"
    elif required is None or required == "":
        required = UNKNOWN
    db = item.get("db", item.get("data", UNKNOWN))
    choices = item.get("choices", item.get("candidate_source", NA))
    if operation or static:
        db, choices = NA, NA
    elif db is None or db == "":
        db = UNKNOWN
    length = item.get("format", item.get("length", UNKNOWN))
    if operation or static:
        length = NA
    description = item.get("description")
    if not description:
        description = (f"「{name}」の操作を受け付ける。業務結果は要確認。" if operation else
                       f"{name}を画面に表示する。" if io == "O" else
                       f"{name}を入力・選択する。業務上の制約は確認済みの範囲だけを記載する。")
    return {"number": number,
            "group": item.get("group") or group or ("画面操作" if operation else "見出し・説明" if static else "画面項目"),
            "name": name, "type": typ, "io": io, "db": db,
            "choices": choices, "required": required, "format": length or UNKNOWN,
            "description": description,
            "evidence": item.get("evidence", []),
            "warnings": item.get("warnings", [])}


def render(items: Iterable[Mapping[str, Any]], *, group: str = "", start: int = 1) -> str:
    rows = [normalize(item, start + i, group) for i, item in enumerate(items)]
    keys = ("number", "group", "name", "type", "io", "db", "choices", "required", "format", "description")
    text = "| " + " | ".join(HEADERS) + " |\n"
    text += "| " + " | ".join("---" for _ in HEADERS) + " |\n"
    text += "".join("| " + " | ".join(cell(row[key]) for key in keys) + " |\n" for row in rows)
    return text

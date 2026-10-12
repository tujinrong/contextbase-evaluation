"""Presentation functions migrated from source-to-doc-v2/render_document_xlsx.py.

Upstream revision: 7bf3a20b724264c773edea1ee8193cb8a3bd4ca5
Upstream blob: b69b1a81ef3b9adf49088ea2582ed0c95b44eec8
This is an explicit dependency-free extraction, not the full upstream module.
The workbook I/O, application-specific controller and Word/PDF services are
not imported. Functions below are actually used by render_document_xlsx.py.
"""
from __future__ import annotations
import re
import unicodedata

MAX_TEXT_TEMPLATE_COLUMN = 62
TEXT_CONTENT_START_COLUMN = 2
TEXT_TABLE_START_COLUMN = 3
CENTER_ALIGNED_TABLE_HEADERS = {"No", "PK", "主キー", "入出力", "必須", "形式・桁"}
SECTION_HEADING_FILL = "D9D9D9"
SUBSECTION_HEADING_FILL = "EDEDED"
BODY_COLOR = "404040"
BLUE = "1F3864"
FIXED_BODY_ROW_HEIGHT = 16.5


def safe_sheet_title(title: str, used: set[str]) -> str:
    value = re.sub(r"[:\\/?*\[\]\x00-\x1f]", "_", title).strip(" '") or "Sheet"
    value = value[:31]
    original = value
    suffix = 2
    while value.casefold() in {name.casefold() for name in used}:
        tail = f"_{suffix}"
        value = original[: 31 - len(tail)] + tail
        suffix += 1
    used.add(value)
    return value


def proportional_spans(total_cols: int, weights: list[float], min_span: int = 1) -> list[int]:
    if total_cols <= 0 or not weights:
        return []
    positive = [max(0.1, float(weight)) for weight in weights]
    total_weight = sum(positive) or 1.0
    spans = [max(min_span, int(round(weight / total_weight * total_cols))) for weight in positive]
    while sum(spans) > total_cols:
        candidates = [index for index, span in enumerate(spans) if span > min_span]
        if not candidates:
            break
        index = max(candidates, key=lambda item: spans[item])
        spans[index] -= 1
    while sum(spans) < total_cols:
        ratios = [positive[index] / max(1, spans[index]) for index in range(len(spans))]
        spans[max(range(len(spans)), key=lambda item: ratios[item])] += 1
    return spans


def text_width(value: str) -> int:
    # The upstream plain_text dependency is replaced by the local Markdown parser.
    return sum(2 if unicodedata.east_asian_width(ch) in {"F", "W", "A"} else 1 for ch in str(value))


HEADER_BANDS = [
    ("A1:J1", "section", "title"), ("K1:N1", "機能名", "header"),
    ("O1:AD1", "functionName", "body"), ("AE1:AH1", "機能ID", "header"),
    ("AI1:AR1", "functionId", "body"), ("AS1:AV1", "作成者", "header"),
    ("AW1:AZ1", "author", "body"), ("BA1:BD1", "作成日", "header"),
    ("BE1:BJ1", "generatedAt", "body"),
]
# Directly measured from the uploaded V2 workbook (list sheet is not a 62-grid).
ITEM_WIDTHS = [6, 16, 22, 20, 16, 18.66, 22.53, 16, 18, 61]
COVER_MERGES = ['O6:AU9','O12:W14','X12:AU14','O15:W17','X15:AU17',
                'O18:W20','X18:AU20','O23:Y23','Z23:AJ23','AK23:AU23',
                'O24:Y28','Z24:AJ28','AK24:AU28','O36:AU36']

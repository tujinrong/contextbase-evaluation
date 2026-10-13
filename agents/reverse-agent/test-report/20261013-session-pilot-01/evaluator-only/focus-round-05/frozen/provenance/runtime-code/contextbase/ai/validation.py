"""Nonrewriting, domain-neutral Markdown structure and reference checks.

An empty findings list is structural success only.  This module neither proves
source fidelity nor approves business meaning or Mermaid diagram semantics.
"""
from __future__ import annotations

from collections import Counter
import html
from html.parser import HTMLParser
import json
from pathlib import PurePosixPath
import posixpath
import re
from urllib.parse import unquote, urlsplit

from markdown_it import MarkdownIt
import tinycss2


META = re.compile(r"<!--\s*spec-meta:\s*(.*?)-->", re.S)
DELIMITER = re.compile(r":?-{3,}:?")
RESERVED = re.compile(r"(?:CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(?:\..*)?", re.I)


def _canonical_document_path(value: str) -> bool:
    if not value or re.search(r'[\\:<>"|?*\x00-\x1f]', value):
        return False
    path = PurePosixPath(value)
    return (
        not path.is_absolute() and path.suffix.lower() == ".md"
        and str(path) == value and not any(part in {".", ".."} for part in path.parts)
        and not any(part.endswith((" ", ".")) or RESERVED.fullmatch(part) for part in path.parts)
    )


def _json_unique(raw: str) -> dict:
    def pairs(values):
        result = {}
        for key, value in values:
            if key in result:
                raise ValueError("Duplicate JSON member")
            result[key] = value
        return result

    def constant(_value):
        raise ValueError("Non-finite JSON number")

    value = json.loads(raw, object_pairs_hook=pairs, parse_constant=constant)
    if not isinstance(value, dict):
        raise ValueError("Metadata must be an object")
    return value


def _text(inline) -> str:
    return "".join(child.content for child in inline.children or [] if child.type in {"text", "code_inline"}).strip()


def _cells(line: str) -> list[str]:
    """Split the original row; unlike rendered tokens, never fill missing cells."""
    row = line.strip()
    if row.startswith("|"):
        row = row[1:]
    if row.endswith("|") and len(re.search(r"\\*$", row[:-1])[0]) % 2 == 0:
        row = row[:-1]
    result, cell, escaped = [], [], False
    for char in row:
        if char == "|" and not escaped:
            result.append("".join(cell).strip())
            cell = []
        else:
            cell.append(char)
        escaped = char == "\\" and not escaped
    result.append("".join(cell).strip())
    return result


def _visible_table_rows(tokens, table) -> list[list[str]]:
    """Use the real table lexer for display identity, retaining raw rows separately."""
    rows, current = [], []
    for token in tokens[tokens.index(table) + 1:]:
        if token.type == "table_close" and token.level == table.level:
            break
        if token.type == "tr_open":
            current = []
        elif token.type == "inline":
            current.append(_text(token))
        elif token.type == "tr_close":
            rows.append(current)
    return rows


def _css_references(css: str) -> list[str]:
    """Inspect actual CSS URL tokens, not strings or commented examples."""
    references = []
    pending = list(tinycss2.parse_component_value_list(css, skip_comments=True))
    while pending:
        token = pending.pop()
        if token.type == "url":
            references.append(token.value)
        elif token.type == "function":
            arguments = [arg for arg in token.arguments if arg.type not in {"whitespace", "comment"}]
            if token.lower_name == "url" and len(arguments) == 1 and arguments[0].type == "string":
                references.append(arguments[0].value)
            else:
                pending.extend(token.arguments)
        elif hasattr(token, "content"):
            pending.extend(token.content)
    return references


def _unsafe_reference(value: str, document_path: str) -> bool:
    value = html.unescape(value).strip()
    # Detect encoded traversal/drive paths without accessing a target file.
    for _ in range(3):
        decoded = unquote(value)
        if decoded == value:
            break
        value = decoded
    if any(ord(char) < 32 for char in value) or "\\" in value:
        return True
    try:
        uri = urlsplit(value)
    except ValueError:
        return True
    if uri.scheme:
        if uri.scheme.lower() in {"https", "http"}:
            return not bool(uri.netloc)
        return uri.scheme.lower() != "mailto"
    if uri.netloc or uri.path.startswith("/"):
        return True
    if not uri.path:
        return False
    if ":" in uri.path:
        return True
    resolved = posixpath.normpath(posixpath.join(posixpath.dirname(document_path), uri.path))
    if resolved == ".." or resolved.startswith("../"):
        return True
    return any(part.casefold() == "spec-eval" or RESERVED.fullmatch(part) for part in PurePosixPath(resolved).parts)


def _inert_header_metadata(attrs) -> bool:
    """Only encoding/viewport metadata may remain in a static HTML projection."""
    pairs = attrs.items() if isinstance(attrs, dict) else attrs
    normalized = {}
    for name, value in pairs:
        name = name.lower()
        if name in normalized or not isinstance(value, str):
            return False
        normalized[name] = value.strip()
    if set(normalized) == {"charset"}:
        return normalized["charset"].lower() in {"utf-8", "utf8"}
    return (set(normalized) == {"name", "content"}
            and normalized["name"].lower() == "viewport"
            and len(normalized["content"]) <= 1024)


class _HtmlReferences(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.references = []
        self.active_content = False
        self.css = []
        self.in_style = False

    def handle_starttag(self, tag, attrs):
        if tag.lower() == "style":
            self.in_style = True
        if tag.lower() in {"script", "iframe", "object", "embed"}:
            self.active_content = True
        if tag.lower() == "meta" and not _inert_header_metadata(attrs):
            self.active_content = True
        for key, value in attrs:
            if key.lower().startswith("on"):
                self.active_content = True
            if key.lower() in {"action", "formaction"}:
                self.active_content = True
            if value is not None and key.lower() in {"src", "href", "action", "formaction", "poster", "xlink:href"}:
                self.references.append(value)
            if value is not None and key.lower() == "srcset":
                self.references.extend(part.strip().split()[0] for part in value.split(",") if part.strip())
            if value is not None and key.lower() == "style":
                self.css.append(value)

    def handle_endtag(self, tag):
        if tag.lower() == "style":
            self.in_style = False

    def handle_data(self, value):
        if self.in_style:
            self.css.append(value)

    handle_startendtag = handle_starttag


def validate_document(content: str, path: str, *, expected_document_id: str | None = None) -> list[dict]:
    """Return severity/code/detail/location findings; never edit the input text."""
    if not isinstance(content, str):
        raise TypeError("content must be a string")
    if expected_document_id is not None:
        if not isinstance(expected_document_id, str):
            raise TypeError("expected_document_id must be a string or None")
        if not expected_document_id.strip():
            raise ValueError("expected_document_id must be nonempty")
    path = str(path)
    findings = []

    def add(code, detail, line=1):
        findings.append({"severity": "ERROR", "code": code, "detail": detail, "location": f"{path}:{line}"})

    if not _canonical_document_path(path):
        add("DOC_PATH", "Output must be a canonical relative Markdown path inside its publication root")
    if "\x00" in content:
        add("DOC_CONTROL", "NUL is not permitted in a text document")
    md = MarkdownIt("commonmark", {"html": True}).enable("table")
    # Parse even prohibited URI schemes so this audit can report them.  No
    # rendering or URL access takes place; the reference check rejects them.
    md.validateLink = lambda _target: True
    tokens = md.parse(content)
    lines = content.splitlines()
    # A successful table parse can silently discard extra cells, including
    # unescaped pipes inside code spans. Check original top-level rows in both
    # GRID and LIST chapters; do not rewrite the content or forbid padding.
    for table in tokens:
        if table.type != 'table_open' or table.level != 0 or table.map is None:
            continue
        start, end = table.map
        width = len(_cells(lines[start]))
        for offset, line in enumerate(lines[start + 2:end], start + 3):
            if len(_cells(line)) > width:
                add('TABLE_CELL_OVERFLOW',
                    'Original Markdown row has more cells than its header; the renderer discards excess data. Escape literal pipes, including code-span pipes.',
                    offset)
    comments = []
    for token in tokens:
        fragments = [token] if token.type in {"html_block", "html_inline"} else [child for child in token.children or [] if child.type == "html_inline"]
        for fragment in fragments:
            for match in META.finditer(fragment.content):
                line = (token.map or [0])[0] + fragment.content.count("\n", 0, match.start()) + 1
                comments.append((match.group(1), line))
    meta = None
    if len(comments) != 1:
        add("META_COUNT", "Exactly one real spec-meta comment is required; fenced examples do not count")
    else:
        raw, meta_line = comments[0]
        try:
            meta = _json_unique(raw)
        except ValueError:
            add("META_JSON", "spec-meta must be a JSON object without duplicate members or non-finite numbers", meta_line)
        first = content.lstrip("\ufeff \t\r\n")
        if not re.match(r"<!--\s*spec-meta:", first):
            add("META_POSITION", "spec-meta must precede the title and body", meta_line)
    titles = [token for token in tokens if token.type == "heading_open" and token.tag == "h1" and token.level == 0]
    if len(titles) != 1:
        add("TITLE_COUNT", "Exactly one document title is required")
    chapters = []
    for index, token in enumerate(tokens):
        if token.type == "heading_open" and token.tag == "h2" and token.level == 0:
            chapters.append({"heading": _text(tokens[index + 1]), "line": token.map[0] + 1, "start": token.map[0], "index": index})
    for name, count in Counter(chapter["heading"] for chapter in chapters).items():
        if count > 1:
            add("HEADING_DUPLICATE", "A main chapter heading occurs more than once: " + name)
    declarations = []
    if meta is not None:
        for field in ("schema", "documentId", "version", "path"):
            if not isinstance(meta.get(field), str) or not meta[field].strip():
                add("META_FIELD", "Nonempty metadata string is required: " + field)
        if expected_document_id is not None and meta.get("documentId") != expected_document_id:
            add("META_DOCUMENT_ID", "Metadata documentId must equal the source-derived bound document identity", meta_line)
        if not isinstance(meta.get("schema"), str) or meta["schema"] not in {"spec-md/1.0", "spec-md/1.1"}:
            add("META_SCHEMA", "Unsupported spec-meta schema")
        if meta.get("path") != path or not isinstance(meta.get("path"), str) or not _canonical_document_path(meta.get("path", "")):
            add("META_PATH", "Metadata path must equal the canonical output path")
        sheets = meta.get("sheets")
        if not isinstance(sheets, list) or not sheets:
            add("META_SHEETS", "A nonempty sheets declaration is required")
            sheets = []
        sheet_names = []
        table_layout = meta.get("schema") == "spec-md/1.1" and meta.get("layout") == "TABLE"
        for sheet in sheets:
            if not isinstance(sheet, dict):
                add("META_SHEET", "Each sheet declaration must be an object")
                continue
            name = sheet.get("sheet")
            if not isinstance(name, str) or not name or len(name) > 31 or re.search(r"[/\\?*:\[\]]", name) or name.startswith("'") or name.endswith("'"):
                add("SHEET_NAME", "Sheet names must be nonempty, at most 31 characters and Excel-safe")
            else:
                sheet_names.append(name.casefold())
            if not table_layout:
                declarations.append(sheet)
        if len(sheet_names) != len(set(sheet_names)):
            add("SHEET_DUPLICATE", "Sheet names must be unique without case sensitivity")
        if table_layout:
            if len(sheets) != 1:
                add("TABLE_LAYOUT", "TABLE layout requires exactly one sheet")
            sections = meta.get("sections")
            if not isinstance(sections, list) or not sections:
                add("TABLE_LAYOUT", "TABLE layout requires explicit HEADER/LIST section declarations")
            else:
                declarations = sections
        for declaration in declarations:
            if not isinstance(declaration, dict) or not isinstance(declaration.get("heading"), str) or not declaration["heading"].strip():
                add("META_HEADING", "Each chapter declaration requires a nonempty heading")
            elif not isinstance(declaration.get("kind"), str) or declaration["kind"] not in ({"HEADER", "LIST"} if table_layout else {"GRID", "LIST"}):
                add("META_KIND", "Chapter kinds must match the declared document layout")
        declared = [d["heading"] for d in declarations if isinstance(d, dict) and isinstance(d.get("heading"), str)]
        observed = [c["heading"] for c in chapters]
        if len(declared) != len(set(declared)):
            add("META_HEADING_DUPLICATE", "Each chapter may be declared only once")
        if Counter(declared) != Counter(observed):
            add("CHAPTER_MAPPING", "Actual h2 chapters and declared headings must correspond one to one")
        elif declared != observed:
            add("CHAPTER_ORDER", "Sheet/section declaration order must match the main chapter order")
    declaration_map = {d["heading"]: d for d in declarations if isinstance(d, dict) and isinstance(d.get("heading"), str)}
    for chapter_number, chapter in enumerate(chapters):
        declaration = declaration_map.get(chapter["heading"], {})
        if declaration.get("kind") != "LIST":
            continue
        stop = chapters[chapter_number + 1]["start"] if chapter_number + 1 < len(chapters) else len(lines)
        token_stop = chapters[chapter_number + 1]["index"] if chapter_number + 1 < len(chapters) else len(tokens)
        section_tokens = tokens[chapter["index"] + 3:token_stop]
        tables = [token for token in section_tokens if token.type == "table_open" and token.level == 0]
        if len(tables) != 1:
            add("LIST_TABLE_COUNT", "A LIST chapter must contain exactly one top-level Markdown table", chapter["line"])
            continue
        table = tables[0]
        start, end = table.map
        if any(line.strip() for line in lines[chapter["start"] + 1:start] + lines[end:stop]):
            add("LIST_EXTRA_CONTENT", "A LIST chapter may contain only its table and blank surrounding lines", chapter["line"])
        rows = [_cells(line) for line in lines[start:end]]
        if len(rows) < 2 or any(not DELIMITER.fullmatch(cell) for cell in rows[1]):
            add("LIST_DELIMITER", "A Markdown table requires one valid delimiter row", start + 1)
            continue
        visible_rows = _visible_table_rows(section_tokens, table)
        headers = visible_rows[0] if visible_rows else []
        if not all(headers) or len(headers) != len(set(headers)):
            add("LIST_HEADERS", "Table headers must be nonempty and unique", start + 1)
        for offset, row in enumerate(rows):
            if len(row) != len(headers):
                add("LIST_RECTANGLE", "Original table rows must all have the same column count; parser padding is not accepted", start + offset + 1)
            if offset == 1:
                continue
            for cell in row:
                inline = md.parseInline(cell)[0]
                for child in inline.children or []:
                    if child.type == "image" or (child.type == "html_inline" and not re.fullmatch(r"<br\s*/?>", child.content, re.I)):
                        add("LIST_INLINE_CONTENT", "Images and HTML other than a plain br element are forbidden in LIST cells", start + offset + 1)
        keys = declaration.get("key", [headers[0]] if headers else [])
        if not isinstance(keys, list) or not keys or any(not isinstance(key, str) or key not in headers for key in keys) or len(keys) != len(set(keys)):
            add("LIST_KEY", "LIST keys must identify one or more distinct existing header columns", start + 1)
        else:
            indexes = [headers.index(key) for key in keys]
            values = set()
            for offset, row in enumerate(rows[2:], 2):
                if len(row) != len(headers):
                    continue
                if offset - 1 >= len(visible_rows):
                    add("LIST_PARSE_COVERAGE", "Every original data row must have a corresponding parsed table row", start + offset + 1)
                    continue
                value = tuple(visible_rows[offset - 1][index] for index in indexes)
                if not all(value):
                    add("LIST_KEY_EMPTY", "Each key component must be explicitly populated", start + offset + 1)
                elif value in values:
                    add("LIST_KEY_DUPLICATE", "Declared keys must be unique within the LIST table", start + offset + 1)
                values.add(value)
        if meta and meta.get("layout") == "TABLE" and "columns" in meta and meta["columns"] != headers:
            add("TABLE_COLUMNS", "TABLE column declarations must equal the original detail-table headers", start + 1)
    # Parse actual Markdown/HTML reference attributes only; code examples are data.
    for token in tokens:
        line = (token.map or [0])[0] + 1
        for child in token.children or []:
            if child.type in {"image", "link_open"}:
                attribute = "src" if child.type == "image" else "href"
                value = child.attrGet(attribute)
                if value and _unsafe_reference(value, path):
                    add("REFERENCE_PATH", "A Markdown reference uses an unsafe or protected target", line)
        fragments = [token.content] if token.type == "html_block" else [c.content for c in token.children or [] if c.type == "html_inline"]
        for fragment in fragments:
            parser = _HtmlReferences()
            parser.feed(fragment)
            if parser.active_content:
                add("HTML_ACTIVE", "Published screen markup must be static, without scripts, active handlers or submission targets", line)
            for value in parser.references:
                if _unsafe_reference(value, path):
                    add("REFERENCE_PATH", "An HTML reference uses an unsafe or protected target", line)
            for css in parser.css:
                for value in _css_references(css):
                    if _unsafe_reference(value, path):
                        add("REFERENCE_PATH", "A CSS reference uses an unsafe or protected target", line)
    return findings

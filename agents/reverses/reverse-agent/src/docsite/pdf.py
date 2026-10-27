"""Offline, staged PDF publication from verified docsite HTML.

Run `python -m docsite.pdf --root .`. Input is never executed. The output tree
is replaced only after every selected Markdown document has a readable PDF.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import logging
import os
from pathlib import Path
import shutil
import tempfile
from urllib.parse import unquote, urljoin, urlsplit
from urllib.request import url2pathname

VERSION = "1.1.0"
PRINT_CSS = r'''
@page {
  size: PAPER;
  margin: 12mm 12mm 15mm;
  @bottom-left { content: "CONTEXTBASE / 仕様書"; font-size: 8pt; color: #52616b; }
  @bottom-right { content: counter(page) " / " counter(pages); font-size: 8pt; }
}
html, body { background: white !important; color: #17212b; margin: 0 !important;
  font-family: "Noto Sans CJK JP", "Yu Gothic", "Meiryo", sans-serif !important;
  font-size: 9pt !important; line-height: 1.55; }
.topbar, .toc, .no-print { display: none !important; }
.page-shell, main.document, article.doc-body { display: block !important;
  width: auto !important; max-width: none !important; min-width: 0 !important;
  margin: 0 !important; padding: 0 !important; border: 0 !important; box-shadow: none !important; }
h1 { font-size: 22pt !important; margin: 0 0 8mm; border-bottom: 2pt solid #254858; padding-bottom: 3mm; }
h2 { font-size: 14pt !important; margin: 7mm 0 3mm; }
h3 { font-size: 11pt !important; margin: 5mm 0 2mm; }
h1, h2, h3, h4, summary { break-after: avoid; }
p { orphans: 3; widows: 3; }
details, details > * { display: block !important; }
.table-scroll, .table-wrap, .screen-layout, .ext-grid-scroll { overflow: visible !important;
  max-width: 100% !important; min-width: 0 !important; }
table { width: 100% !important; max-width: 100% !important; min-width: 0 !important;
  table-layout: fixed !important; border-collapse: collapse; font-size: 8pt !important; }
thead { display: table-header-group; }
tfoot { display: table-footer-group; }
tr { break-inside: avoid; }
th, td { border: 0.5pt solid #aebbc3 !important; padding: 1.7mm !important;
  white-space: normal !important; overflow: visible !important; overflow-wrap: anywhere;
  word-break: normal; vertical-align: top; height: auto !important; }
th { background: #eaf0f3 !important; font-weight: 700; }
table.v2-items th:nth-child(1) { width: 3%; }
table.v2-items th:nth-child(2) { width: 8%; }
table.v2-items th:nth-child(3) { width: 10%; }
table.v2-items th:nth-child(4) { width: 7%; }
table.v2-items th:nth-child(5) { width: 5%; }
table.v2-items th:nth-child(6) { width: 10%; }
table.v2-items th:nth-child(7) { width: 10%; }
table.v2-items th:nth-child(8) { width: 6%; }
table.v2-items th:nth-child(9) { width: 11%; }
table.v2-items th:nth-child(10) { width: 20%; }
.screen-layout .ext-screen { width: 100% !important; max-width: 100% !important; }
.screen-layout .ext-modal-body { height: auto !important; overflow: visible !important; padding: 0 3mm !important; }
.screen-layout .ext-grid col { width: auto !important; }
.screen-layout .ext-footer, .screen-layout th[data-fixed] { position: static !important; }
img, svg { max-width: 100% !important; height: auto; }
pre, code { white-space: pre-wrap !important; overflow-wrap: anywhere; font-size: 8pt; }
a { color: #254858; text-decoration: none; }
'''


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def json_write(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def safe_root(root: Path, path: Path) -> Path:
    root = root.resolve()
    absolute = Path(os.path.abspath(path))
    if not absolute.is_relative_to(root):
        raise ValueError("Path escapes publication root: " + str(path))
    for component in (absolute, *absolute.parents):
        if component == root:
            break
        if component.is_symlink():
            raise ValueError("Publication paths must not contain symlinks: " + str(path))
    resolved = absolute.resolve()
    if not resolved.is_relative_to(root):
        raise ValueError("Path escapes publication root: " + str(path))
    return resolved


class OfflineFetcher:
    def __init__(self, root: Path):
        self.root = root.resolve()
        self.errors: list[str] = []

    def __call__(self, url: str):
        from weasyprint import default_url_fetcher
        try:
            parsed = urlsplit(url)
            if parsed.scheme == "data":
                if not url.startswith("data:image/") or len(url) > 8_000_000:
                    raise ValueError("Only bounded image data URLs are permitted")
            elif parsed.scheme == "file" and parsed.netloc in {"", "localhost"}:
                path = safe_root(self.root, Path(url2pathname(unquote(parsed.path))))
                if not path.is_file() or path.stat().st_size > 20_000_000:
                    raise ValueError("Missing or oversized asset: " + str(path))
                if path.suffix.lower() not in {".css", ".svg", ".png", ".jpg", ".jpeg", ".gif", ".webp", ".woff", ".woff2", ".ttf", ".otf"}:
                    raise ValueError("Unsupported publication asset: " + str(path))
            else:
                raise ValueError("External resources are disabled")
            return default_url_fetcher(url)
        except Exception as exc:
            # WeasyPrint may catch fetch exceptions: fail publication explicitly.
            self.errors.append(str(exc))
            raise


class CaptureErrors(logging.Handler):
    def __init__(self):
        super().__init__(logging.WARNING)
        self.errors = []

    def emit(self, record):
        message = record.getMessage()
        if record.levelno >= logging.ERROR or any(x in message.lower() for x in ("no glyph", "missing glyph", ".notdef")):
            self.errors.append(message)


def prepare_html(text: str, source: Path, htmlroot: Path, documents: set[Path], paper: str):
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(text, "html.parser")
    for node in soup.select("script, base, link[rel~=attachment], .topbar, .toc"):
        node.decompose()
    for node in soup.find_all("details"):
        node["open"] = "open"
    max_columns = 0
    item_values = []
    for table in soup.find_all("table"):
        first = table.find("tr")
        headers = [x.get_text(" ", strip=True) for x in first.find_all(["th", "td"], recursive=False)] if first else []
        max_columns = max(max_columns, len(headers))
        if headers == ["No", "グループ", "項目名", "種類", "入出力", "DB連携項目", "候補取得元", "必須", "形式・桁", "説明"]:
            table["class"] = list(table.get("class", [])) + ["v2-items"]
            for row in table.find_all("tr")[1:]:
                values = row.find_all(["td", "th"], recursive=False)
                if len(values) != 10:
                    raise ValueError("Item table does not have ten columns")
                item_values.extend(x.get_text(" ", strip=True) for x in values if x.get_text(strip=True))
    for link in soup.find_all("a", href=True):
        uri = urlsplit(urljoin(source.as_uri(), link["href"]))
        if uri.scheme == "file":
            target = Path(url2pathname(unquote(uri.path))).resolve()
            if target in documents:
                relative = os.path.relpath(target.with_suffix(".pdf"), source.parent).replace(os.sep, "/")
                link["href"] = relative + ("#" + uri.fragment if uri.fragment else "")
    selected = ("A4 landscape" if max_columns >= 8 or soup.select_one(".screen-layout") else "A4") if paper == "auto" else paper
    heading = soup.find("h1")
    title = heading.get_text(" ", strip=True) if heading else source.stem
    return str(soup), selected, item_values, title


def portable_links(data: bytes, source: Path, documents: set[Path]) -> bytes:
    """Use relative PDF file actions, not build-machine absolute file URLs.

    Cross-document links open page one. In-document destinations are preserved.
    """
    from pypdf import PdfReader, PdfWriter
    from pypdf.generic import DictionaryObject, NameObject, TextStringObject, ArrayObject, NumberObject
    reader = PdfReader(io.BytesIO(data))
    writer = PdfWriter(clone_from=reader)
    changed = False
    for page in writer.pages:
        for ref in page.get("/Annots", []):
            annotation = ref.get_object()
            action = annotation.get("/A")
            if not action or action.get("/S") != "/URI":
                continue
            uri = urlsplit(str(action.get("/URI", "")))
            if uri.scheme != "file" or uri.netloc not in {"", "localhost"}:
                continue
            target = Path(url2pathname(unquote(uri.path))).resolve()
            if target.suffix.lower() != ".pdf" or target.with_suffix(".html") not in documents:
                continue
            relative = os.path.relpath(target, source.parent).replace(os.sep, "/")
            annotation[NameObject("/A")] = DictionaryObject({
                NameObject("/S"): NameObject("/GoToR"),
                NameObject("/F"): TextStringObject(relative),
                NameObject("/D"): ArrayObject([NumberObject(0), NameObject("/Fit")])})
            changed = True
    if not changed:
        return data
    stream = io.BytesIO()
    writer.write(stream)
    return stream.getvalue()


def validate_pdf(data: bytes, values: list[str], title: str) -> dict:
    from pypdf import PdfReader
    if not data.startswith(b"%PDF-"):
        raise ValueError("PDF header is missing")
    reader = PdfReader(io.BytesIO(data), strict=True)
    if not reader.pages:
        raise ValueError("PDF has no pages")
    text = "\n".join(page.extract_text() or "" for page in reader.pages)
    normalize = lambda x: "".join(x.replace("\u00ad", "").split())
    haystack = normalize(text)
    missing = [x for x in [title, *values] if normalize(x) and normalize(x) not in haystack]
    if missing:
        raise ValueError("PDF text coverage failed: " + repr(missing[:5]))
    return {"pages": len(reader.pages), "text_characters": len(text), "checked_item_cells": len(values), "text_coverage": "pass"}


def build_pdfs(root: Path, *, paper: str = "auto") -> dict:
    if paper not in {"auto", "A4", "A4 landscape", "A3 landscape"}:
        raise ValueError("Unsupported paper size")
    try:
        import weasyprint
        from weasyprint import HTML, CSS
        from bs4 import BeautifulSoup
        from pypdf import PdfReader  # noqa: F401
    except (ImportError, OSError) as exc:
        raise RuntimeError("Install the PDF optional dependencies and Japanese system fonts; see docs/doc/PDF出力と項目一覧.md") from exc
    root = root.resolve()
    mdroot = safe_root(root, root / "output/md")
    htmlroot = safe_root(root, root / "output/html")
    destination = safe_root(root, root / "output/PDF")
    markdown = sorted(mdroot.rglob("*.md"))
    if not markdown:
        raise ValueError("No Markdown documents in output/md")
    documents = {safe_root(htmlroot, htmlroot / p.relative_to(mdroot).with_suffix(".html")) for p in markdown}
    for document in documents:
        if not document.is_file():
            raise ValueError("HTML is missing; run contextbase build first: " + str(document))
    work = root / ".contextbase-work"
    if work.is_symlink():
        raise ValueError("Refusing a symlink workspace")
    work.mkdir(exist_ok=True)
    lock = work / "pdf.lock"
    try:
        with lock.open("x", encoding="utf-8") as stream:
            stream.write(str(os.getpid()))
    except FileExistsError as exc:
        raise ValueError("Another PDF publication is running") from exc
    stage = Path(tempfile.mkdtemp(prefix="pdf-", dir=work))
    report = {"version": VERSION, "status": "running", "documents": [], "errors": [], "engine": "WeasyPrint " + weasyprint.__version__}
    try:
        previous_path = destination / "_manifest.json"
        previous = json.loads(previous_path.read_text(encoding="utf-8")) if previous_path.exists() else {"documents": []}
        owned = {x["pdf"]: x for x in previous.get("documents", [])}
        if destination.exists():
            for p in destination.rglob("*"):
                if p.is_symlink():
                    raise ValueError("Refusing a PDF output symlink")
                if p.is_file() and p.name != "_manifest.json":
                    relative = p.relative_to(destination).as_posix()
                    if relative not in owned or sha(p.read_bytes()) != owned[relative]["pdf_sha256"]:
                        raise ValueError("Edited or unmanaged PDF must not be overwritten: " + relative)
        asset_hashes = {p.relative_to(htmlroot).as_posix(): sha(safe_root(htmlroot, p).read_bytes())
                        for p in sorted(htmlroot.rglob("*")) if p.is_file() and p.suffix.lower() != ".html"}
        logger = logging.getLogger("weasyprint")
        for md in markdown:
            safe_root(mdroot, md)
            relative = md.relative_to(mdroot)
            source = htmlroot / relative.with_suffix(".html")
            raw = source.read_text(encoding="utf-8")
            meta = BeautifulSoup(raw, "html.parser").find("meta", attrs={"name": "docsite-source-sha256"})
            md_hash = sha(md.read_text(encoding="utf-8").encode("utf-8"))
            if not meta or meta.get("content") != md_hash:
                raise ValueError("HTML does not match the current Markdown: " + str(relative))
            signature = sha(json.dumps({"html": sha(raw.encode("utf-8")), "md": md_hash, "css": PRINT_CSS,
                                       "assets": asset_hashes, "engine": report["engine"], "paper": paper,
                                       "version": VERSION}, sort_keys=True).encode("utf-8"))
            key = relative.with_suffix(".pdf").as_posix()
            target = stage / key
            target.parent.mkdir(parents=True, exist_ok=True)
            prepared, selected, values, title = prepare_html(raw, source, htmlroot, documents, paper)
            if key in owned and owned[key].get("signature") == signature and (destination / key).is_file():
                data = (destination / key).read_bytes()
                reused = True
            else:
                fetcher, capture = OfflineFetcher(htmlroot), CaptureErrors()
                logger.addHandler(capture)
                try:
                    data = HTML(string=prepared, base_url=source.as_uri(), url_fetcher=fetcher).write_pdf(
                        stylesheets=[CSS(string=PRINT_CSS.replace("PAPER", selected))])
                finally:
                    logger.removeHandler(capture)
                if fetcher.errors or capture.errors:
                    raise ValueError("PDF asset/font/render errors: " + repr(fetcher.errors + capture.errors))
                data = portable_links(data, source, documents)
                reused = False
            checks = validate_pdf(data, values, title)
            target.write_bytes(data)
            report["documents"].append({"markdown": relative.as_posix(), "pdf": key,
                "markdown_sha256": md_hash, "html_sha256": sha(raw.encode("utf-8")),
                "signature": signature, "pdf_sha256": sha(data), "paper": selected,
                "reused": reused, **checks})
        report.update(status="verified", count=len(report["documents"]),
                      total_pages=sum(x["pages"] for x in report["documents"]))
        json_write(stage / "_manifest.json", report)
        backup = work / ("previous-" + stage.name)
        moved = False
        destination.parent.mkdir(parents=True, exist_ok=True)
        try:
            if destination.exists():
                destination.rename(backup)
                moved = True
            stage.rename(destination)
        except Exception:
            if moved and not destination.exists():
                backup.rename(destination)
            raise
        if backup.exists():
            shutil.rmtree(backup)
        json_write(root / "report/pdf/validation.json", report)
        return report
    except Exception as exc:
        report.update(status="failed", errors=[str(exc)], published=False)
        json_write(root / "report/pdf/validation.json", report)
        raise
    finally:
        if stage.exists():
            shutil.rmtree(stage)
        lock.unlink(missing_ok=True)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="検証済みHTMLから日本語PDFを生成")
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--paper", choices=["auto", "A4", "A4 landscape", "A3 landscape"], default="auto")
    args = parser.parse_args(argv)
    try:
        result = build_pdfs(args.root, paper=args.paper)
    except (OSError, ValueError, RuntimeError) as exc:
        parser.exit(1, "pdf: " + str(exc) + "\n")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

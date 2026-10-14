"""Offline derived views of immutable AI Markdown, with isolated trusted Mermaid.

Structure, safe display and semantic approval are separate outcomes. Sanitizing
a derived view never repairs or rewrites the AI document.
"""
from __future__ import annotations

import base64
from contextlib import contextmanager
import hashlib
import html
import io
import json
import math
import os
from pathlib import Path
import re
import threading
from urllib.parse import unquote, urlsplit
import xml.etree.ElementTree as ET

from bs4 import BeautifulSoup
from markdown_it import MarkdownIt
from PIL import Image
import tinycss2

from .validation import validate_document, _inert_header_metadata
from .edge_label_projection import (project_flowchart_edges, reverse_projection,
    validate_semantic_signature, validate_svg_label_rows)


SECURE_KEYS = ["secure", "securityLevel", "startOnLoad", "maxTextSize", "suppressErrorRendering", "maxEdges",
               "htmlLabels", "themeCSS", "fontFamily", "flowchart", "deterministicIds", "deterministicIDSeed"]
STATIC_CSP = "default-src 'none'; script-src 'none'; style-src 'unsafe-inline'; img-src data:; font-src 'none'; connect-src 'none'; frame-src 'none'; form-action 'none'; base-uri 'none'"
BASE_STYLE = 'body{margin:16px;font-family:system-ui,sans-serif}pre{white-space:pre-wrap}table[data-renderer-markdown]{border-collapse:collapse;width:100%;table-layout:fixed;margin:12px 0}table[data-renderer-markdown] th,table[data-renderer-markdown] td{border:1px solid #aaa;padding:6px;vertical-align:top;overflow-wrap:anywhere}table[data-renderer-markdown] th{background:#f0f3f7}img[data-renderer-diagram]{max-width:100%;height:auto}table[data-renderer-markdown]:not([data-renderer-columns="1"]):not([data-renderer-columns="2"]){table-layout:auto}table[data-renderer-markdown]:not([data-renderer-columns="1"]):not([data-renderer-columns="2"]) col{width:auto!important}table[data-renderer-markdown]:not([data-renderer-columns="1"]):not([data-renderer-columns="2"]) th,table[data-renderer-markdown]:not([data-renderer-columns="1"]):not([data-renderer-columns="2"]) td{overflow-wrap:normal;word-break:normal;white-space:normal}table[data-renderer-markdown]:not([data-renderer-columns="1"]):not([data-renderer-columns="2"]) code{white-space:nowrap}'
MERMAID_LABEL_STYLE = ".edgeLabel rect{opacity:1!important;fill:#ffffff!important}.edgeLabel .labelBkg{background-color:#ffffff!important}"
MERMAID_LABEL_WIDTH = 320
_RUNTIME_LOCK = threading.RLock()


@contextmanager
def _playwright_runtime(runtime):
    """Keep the driver's automatic artifact/temp folders in caller publication."""
    from playwright.sync_api import sync_playwright
    temporary = runtime / "tmp"
    temporary.mkdir(parents=True, exist_ok=True)
    with _RUNTIME_LOCK:
        previous = {key: os.environ.get(key) for key in ("TEMP", "TMP", "TMPDIR")}
        try:
            os.environ.update({key: str(temporary) for key in previous})
            with sync_playwright() as playwright:
                yield playwright
        finally:
            for key, value in previous.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value


def _sha(data):
    return hashlib.sha256(data if isinstance(data, bytes) else data.encode("utf-8")).hexdigest()


def _path(path):
    value = Path(os.path.abspath(os.fspath(path)))
    if any(part.casefold() == "spec-eval" for part in value.parts):
        raise ValueError("Evaluation paths are forbidden")
    for ancestor in (value, *value.parents):
        junction = getattr(ancestor, "is_junction", None)
        if ancestor.is_symlink() or (junction and junction()):
            raise ValueError("Linked publication paths are forbidden")
        try:
            # Python 3.11 has no Path.is_junction; reject Windows reparse points too.
            if getattr(ancestor.lstat(), "st_file_attributes", 0) & 0x400:
                raise ValueError("Reparse publication paths are forbidden")
        except FileNotFoundError:
            pass
    return value.resolve()


def _write(path, value):
    with path.open("xb") as stream:
        stream.write(value if isinstance(value, bytes) else value.encode("utf-8"))


def _image_data(uri, base, asset_root):
    parsed = urlsplit(html.unescape(uri).strip())
    mime = None
    if parsed.scheme == "data":
        match = re.fullmatch(r"data:(image/(?:png|jpeg|gif|webp));base64,([A-Za-z0-9+/=\s]+)", uri)
        if not match:
            raise ValueError("Only verified raster data images are allowed")
        mime = match[1]
        data = base64.b64decode(re.sub(r"\s", "", match[2]), validate=True)
    elif parsed.scheme or parsed.netloc or not parsed.path or "\\" in parsed.path:
        raise ValueError("External or noncanonical image reference")
    else:
        asset = _path(base / unquote(parsed.path))
        if not asset.is_relative_to(asset_root) or "spec-eval" in asset.parts or not asset.is_file():
            raise ValueError("Image outside the supplied asset root")
        if asset.stat().st_size > 20_000_000:
            raise ValueError("Image exceeds bounded input size")
        data = asset.read_bytes()
    if len(data) > 20_000_000:
        raise ValueError("Image exceeds bounded input size")
    with Image.open(io.BytesIO(data)) as picture:
        if picture.width * picture.height > 40_000_000:
            raise ValueError("Image exceeds bounded dimensions")
        kind = picture.format
        picture.verify()
    formats = {"PNG": "image/png", "JPEG": "image/jpeg", "GIF": "image/gif", "WEBP": "image/webp"}
    if kind not in formats or (mime is not None and mime != formats[kind]):
        raise ValueError("Unsupported image content")
    return "data:" + formats[kind] + ";base64," + base64.b64encode(data).decode("ascii")


def _css_url(token):
    if token.type == "url":
        return token.value
    if token.type == "function" and token.lower_name == "url":
        args = [arg for arg in token.arguments if arg.type not in {"whitespace", "comment"}]
        return args[0].value if len(args) == 1 and args[0].type == "string" else ""
    return None


def _safe_css(css, base, asset_root, removed):
    def walk(tokens):
        result = []
        skip_import = False
        for token in tokens:
            if token.type == "at-keyword" and token.lower_value == "import":
                removed.append({"kind": "css", "name": "import"})
                skip_import = True
            if skip_import:
                if token.type == "literal" and token.value == ";":
                    skip_import = False
                continue
            value = _css_url(token)
            if value is not None:
                if value.startswith("#"):
                    result.append(token)
                    continue
                try:
                    safe = _image_data(value, base, asset_root)
                    result.extend(tinycss2.parse_component_value_list("url(" + json.dumps(safe) + ")"))
                except Exception as exc:
                    # No remote access and no substitution of a different image.
                    removed.append({"kind": "css-resource", "name": "url", "reason": type(exc).__name__})
                    result.extend(tinycss2.parse_component_value_list("none"))
                continue
            if token.type == "function" and token.lower_name in {"expression", "-moz-binding"}:
                removed.append({"kind": "css", "name": token.lower_name})
                continue
            if token.type == "function":
                if token.lower_name in {"image-set", "-webkit-image-set"}:
                    # Direct string alternatives are URLs; nested type("image/png") is metadata.
                    for index, argument in enumerate(token.arguments):
                        if argument.type == "string":
                            token.arguments[index] = tinycss2.parse_component_value_list(
                                "url(" + json.dumps(argument.value) + ")")[0]
                token.arguments = walk(token.arguments)
            elif hasattr(token, "content"):
                token.content = walk(token.content)
            result.append(token)
        return result

    return tinycss2.serialize(walk(tinycss2.parse_component_value_list(css)))


def _sanitize(fragment, base, asset_root):
    soup = BeautifulSoup(fragment, "html.parser")
    removed = []
    for tag in list(soup.find_all(["script", "iframe", "object", "embed", "base", "link", "meta",
                                  "animate", "animatemotion", "animatetransform", "set"])):
        if tag.name == "meta" and _inert_header_metadata(tag.attrs):
            continue
        removed.append({"kind": "element", "name": tag.name})
        tag.decompose()
    for tag in soup.find_all(True):
        for attr in list(tag.attrs):
            if attr.lower().startswith("on") or attr.lower() in {"srcdoc", "action", "formaction", "srcset", "ping"}:
                removed.append({"kind": "attribute", "name": attr})
                del tag[attr]
        for attr in ("href", "xlink:href", "src"):
            if not tag.has_attr(attr):
                continue
            value = str(tag[attr])
            if tag.name == "img" and attr == "src":
                try:
                    tag[attr] = _image_data(value, base, asset_root)
                    continue
                except Exception as exc:
                    removed.append({"kind": "image", "name": "src", "reason": type(exc).__name__})
            elif value.startswith("#"):
                continue
            elif tag.name == "a" and attr == "href" and urlsplit(value).scheme.lower() in {"http", "https", "mailto"}:
                # An inert citation is not an automatic external dependency.
                continue
            elif tag.name == 'a' and attr == 'href' and _local_document_citation(value, base, asset_root):
                # Preserve related-document citations just like external ones.
                # No linked file is read, fetched, or declared already published.
                continue
            else:
                removed.append({"kind": "resource", "name": attr})
            del tag[attr]
        if tag.name == "style":
            tag.string = _safe_css(tag.get_text(), base, asset_root, removed)
        if tag.has_attr("style"):
            tag["style"] = _safe_css(str(tag["style"]), base, asset_root, removed)
        if tag.find_parent("svg") or tag.name == "svg":
            for attr in ("fill", "stroke", "filter", "clip-path", "mask", "marker", "marker-start", "marker-mid", "marker-end", "cursor"):
                if tag.has_attr(attr):
                    tag[attr] = _safe_css(str(tag[attr]), base, asset_root, removed)
    return str(soup), removed


def _local_document_citation(value, base, asset_root):
    parsed = urlsplit(value)
    if parsed.scheme or parsed.netloc:
        return False
    relative = unquote(parsed.path)
    if not relative or relative.startswith(('/', '\\')) or '\\' in relative or ':' in relative:
        return False
    if Path(relative).suffix.lower() not in {'.md', '.html', '.pdf', '.xlsx'}:
        return False
    try:
        target = _path(Path(base) / relative)
        permitted_root = _path(Path(asset_root))
    except (OSError, ValueError):
        return False
    return permitted_root in target.parents


def _svg_css_check(css):
    def walk(tokens):
        for token in tokens:
            value = _css_url(token)
            if value is not None and not value.startswith("#"):
                raise ValueError("Unexpected external SVG CSS")
            if token.type == "at-keyword" and token.lower_value == "import":
                raise ValueError("Unexpected imported SVG CSS")
            if token.type == "function":
                if token.lower_name in {"expression", "-moz-binding"}:
                    raise ValueError("Unexpected active SVG CSS")
                walk(token.arguments)
            elif hasattr(token, "content"):
                walk(token.content)
    walk(tinycss2.parse_component_value_list(css))


def _svg_safe(svg):
    if re.search(r"<!DOCTYPE|<!ENTITY", svg, re.I):
        raise ValueError("SVG declarations are forbidden")
    root = ET.fromstring(svg)
    if root.tag.rsplit("}", 1)[-1] != "svg":
        raise ValueError("Mermaid did not produce SVG")
    ET.register_namespace("", "http://www.w3.org/2000/svg")
    ET.register_namespace("xlink", "http://www.w3.org/1999/xlink")
    for parent in root.iter():
        for child in list(parent):
            if child.tag.rsplit("}", 1)[-1].lower() in {"script", "foreignobject", "iframe", "object", "embed",
                                                      "animate", "animatemotion", "animatetransform", "set"}:
                raise ValueError("Unexpected active SVG element")
        for attr, value in parent.attrib.items():
            short = attr.rsplit("}", 1)[-1].lower()
            if short.startswith("on") or (short in {"href", "src"} and not value.startswith("#")):
                raise ValueError("Unexpected active SVG attribute")
            # Includes presentation attributes such as fill/filter/clip-path.
            _svg_css_check(value)
        if parent.tag.rsplit("}", 1)[-1].lower() == "style":
            _svg_css_check(parent.text or "")
    return ET.tostring(root, encoding="unicode")


def _html(body, styles="", scripts=False):
    csp = STATIC_CSP if not scripts else STATIC_CSP.replace("script-src 'none'", "script-src 'unsafe-inline' 'unsafe-eval'")
    return '<!doctype html><html lang="ja"><head><meta charset="utf-8"><meta http-equiv="Content-Security-Policy" content="' + html.escape(csp, quote=True) + '"><style>' + BASE_STYLE + "</style>" + styles + "</head><body>" + body + "</body></html>"


def _png_info(data):
    with Image.open(io.BytesIO(data)) as picture:
        width, height = picture.size
        nonblank = any(low != high for low, high in picture.convert("RGB").getextrema())
    with Image.open(io.BytesIO(data)) as picture:
        picture.verify()
    return {"width": width, "height": height, "decoded": True, "nonblank": nonblank, "sha256": _sha(data)}


def _capture(page, locator=None):
    if locator is not None:
        dimensions = locator.bounding_box()
        if dimensions is None:
            raise ValueError("No visible artifact bounds")
        width, height = dimensions["width"], dimensions["height"]
    else:
        width, height = page.evaluate("[document.documentElement.scrollWidth,document.documentElement.scrollHeight]")
    if width <= 0 or height <= 0 or width > 16000 or height > 16000 or width * height > 40_000_000:
        raise ValueError("Artifact exceeds bounded capture dimensions; it is not cropped or declared passed")
    return locator.screenshot(animations="disabled") if locator is not None else page.screenshot(full_page=True, animations="disabled")


def _protect_cluster_labels(page):
    """Paint an opaque title background above crossing paths at its existing position."""
    return page.evaluate("""() => {
        const svg = document.querySelector('svg');
        for (const label of [...svg.querySelectorAll('g.cluster-label')]) {
            const box = label.getBBox();
            const matrix = svg.getCTM().inverse().multiply(label.getCTM());
            if (![box.x,box.y,box.width,box.height,matrix.a,matrix.b,matrix.c,matrix.d,matrix.e,matrix.f].every(Number.isFinite)) {
                throw new Error('Invalid cluster label geometry');
            }
            const layer = document.createElementNS('http://www.w3.org/2000/svg','g');
            layer.setAttribute('class','trusted-cluster-label-overlay');
            layer.setAttribute('transform',`matrix(${matrix.a},${matrix.b},${matrix.c},${matrix.d},${matrix.e},${matrix.f})`);
            const background = document.createElementNS('http://www.w3.org/2000/svg','rect');
            for (const [key,value] of Object.entries({x:box.x-3,y:box.y-2,width:box.width+6,height:box.height+4})) {
                background.setAttribute(key,String(value));
            }
            background.setAttribute('data-trusted-label-background','true');
            background.setAttribute('style','fill:#ffffff!important;stroke:none!important;opacity:1!important');
            const copy = label.cloneNode(true);
            copy.removeAttribute('transform');
            layer.append(background,copy);
            label.remove();
            svg.append(layer);
        }
        return svg.outerHTML;
    }""")


def _flowchart_svg_signature(svg):
    """Compare meaning-bearing graph structure while allowing geometry changes."""
    soup = BeautifulSoup(svg, "xml")
    normalize = lambda value: ''.join(value.split())
    node_key = lambda value: re.sub(r'^.*?flowchart-', '', value)
    shapes = lambda node: sorted((child.name, tuple(sorted(child.get('class', '').split())))
        for child in node.find_all(['rect', 'polygon', 'circle', 'ellipse', 'path'], recursive=False))
    nodes = [{'id': node_key(node.get('id', '')), 'text': normalize(node.get_text()),
              'shapes': shapes(node)} for node in soup.select('g.node')]
    edges = [{'id': edge.get('data-id', edge.get('id', '')),
              'endpoints': sorted(c for c in edge.get('class', '').split() if c.startswith(('LS-', 'LE-'))),
              'connectionClasses': sorted(c for c in edge.get('class', '').split()
                  if c.startswith(('edge-pattern-', 'edge-thickness-'))),
              'markerStart': edge.get('marker-start'), 'markerEnd': edge.get('marker-end')}
             for edge in soup.select('path.flowchart-link')]
    labels = [{'id': label['data-id'], 'text': normalize(label.get_text())}
              for label in soup.select('g.edgeLabel g.label[data-id]')]
    clusters = [{'id': group.get('id', ''), 'shapes': shapes(group),
                 'text': normalize(label.get_text()) if (label := group.select_one('g.cluster-label')) else ''}
                for group in soup.select('g.cluster')]
    return {'nodes': nodes, 'edges': edges, 'edgeLabels': labels, 'clusters': clusters}


def _edge_label_rows(page):
    """Read actual visible SVG rows from the inert static browser context."""
    return page.locator('g.edgeLabel g.label[data-id]').evaluate_all("""nodes => {
        const svg = document.querySelector('svg').getBoundingClientRect();
        function visible(row) {
            const box = row.getBoundingClientRect();
            if (!(box.width > 0 && box.height > 0) || box.left < svg.left-1 ||
                box.right > svg.right+1 || box.top < svg.top-1 || box.bottom > svg.bottom+1) return false;
            for (let parent = row; parent instanceof Element; parent = parent.parentElement) {
                const style = getComputedStyle(parent);
                if (style.display === 'none' || style.visibility === 'hidden' ||
                    style.visibility === 'collapse' || Number(style.opacity) === 0) return false;
            }
            const fill = getComputedStyle(row).fill;
            return fill !== 'none' && fill !== 'transparent' && !/rgba\\([^)]*,\\s*0\\s*\\)$/.test(fill);
        }
        return nodes.map(node => ({id:node.dataset.id,text:node.textContent,
            rows:[...node.querySelectorAll('tspan.text-outer-tspan')].filter(visible).map(row=>row.textContent)}));
    }""")


def _capture_document(page, destination, display):
    """Keep bounded PNGs while recording the full extent of long documents."""
    width, height = [math.ceil(value) for value in page.evaluate(
        "[document.documentElement.scrollWidth,document.documentElement.scrollHeight]")]
    if width <= 0 or height <= 0 or width > 16000 or height > 500000 or width * height > 250_000_000:
        raise ValueError("Document exceeds complete tiled capture bounds")
    if height <= 16000 and width * height <= 40_000_000:
        data = _capture(page)
        display['documentPng'] = _png_info(data)
        _write(destination / 'document.png', data)
        if not display['documentPng']['nonblank']:
            raise ValueError('Blank document capture')
        return
    tile_height = min(4000, 40_000_000 // width)
    pages = []
    # A page may contain blank spacing; the complete document must contain text
    # or image variation. Every strip is preserved and included in coverage.
    for y in range(0, height, tile_height):
        clip = {'x': 0, 'y': y, 'width': width, 'height': min(tile_height, height-y)}
        data = page.screenshot(clip=clip, full_page=True, animations='disabled')
        info = _png_info(data)
        if (info['width'], info['height']) != (clip['width'], clip['height']):
            raise ValueError('Document strip does not cover its recorded rectangle')
        name = f'document-{len(pages)+1:03d}.png'
        _write(destination / name, data)
        pages.append({'path': name, 'sourceRectangle': clip, 'png': info})
    display['documentCapture'] = {'mode': 'complete-vertical-tiles', 'width': width,
        'height': height, 'complete': True, 'pages': pages}
    if not any(record['png']['nonblank'] for record in pages):
        raise ValueError('Blank document capture')


def _markdown_table_open(tokens, index, options, env, renderer):
    """Style parser-owned Markdown tables without changing embedded source-screen tables."""
    count = 0
    for token in tokens[index + 1:]:
        if token.type == "thead_close":
            break
        if token.type == "th_open":
            count += 1
    if count < 1:
        raise ValueError("Markdown table header required")
    tokens[index].attrSet("data-renderer-markdown", "")
    tokens[index].attrSet("data-renderer-columns", str(count))
    widths = ([100] if count == 1 else [24, 76] if count == 2 else
              [4] + [56 / (count - 2)] * (count - 2) + [40])
    columns = ''.join(f'<col style="width:{width:g}%">' for width in widths)
    return renderer.renderToken(tokens, index, options, env) + '<colgroup>' + columns + '</colgroup>\n'


def render_document(source: Path, destination: Path, *, mermaid_package: Path | None = None,
                    chromium_executable: Path | None = None, document_path: str | None = None,
                    asset_root: Path | None = None) -> dict:
    source, destination = _path(source), _path(destination)
    if not source.is_file():
        raise ValueError("Immutable Markdown source required")
    if destination == source.parent or destination in source.parents:
        raise ValueError("Publication must not contain the original source")
    destination.mkdir(parents=True, exist_ok=False)
    raw = source.read_bytes()
    content = raw.decode("utf-8-sig")
    asset_root = _path(asset_root or source.parent)
    result = {"source": str(source), "sourceSha256": _sha(raw), "originalModified": False,
              "structure": {"findings": validate_document(content, document_path or source.name)},
              "display": {"status": "NOT_RUN", "errors": [], "blockedRequests": []},
              "safety": {"status": "UNMODIFIED_DERIVATION", "removed": [], "inputJavaScriptEnabled": False},
              "diagrams": [], "layouts": [], "artifacts": [], "semanticApproval": "NOT_ASSESSED"}
    result["structure"]["status"] = "ERROR" if result["structure"]["findings"] else "PASS"
    parser = MarkdownIt("commonmark", {"html": True}).enable("table")
    parser.renderer.rules['table_open'] = lambda tokens, index, options, env: _markdown_table_open(
        tokens, index, options, env, parser.renderer)
    diagrams, layout_blocks = [], []
    original_fence = parser.renderer.rules["fence"]

    def fence(tokens, index, options, env):
        token = tokens[index]
        if token.info.strip() != "mermaid":
            return original_fence(tokens, index, options, env)
        number = len(diagrams) + 1
        diagrams.append({"id": f"diagram-{number:03}", "source": token.content, "lines": [token.map[0] + 1, token.map[1]]})
        return f'<figure data-renderer-diagram="{number}"><pre><code class="language-mermaid">' + html.escape(token.content) + "</code></pre></figure>"

    parser.renderer.rules["fence"] = fence
    tokens = parser.parse(content)
    for token in tokens:
        if token.type == "html_block" and BeautifulSoup(token.content, "html.parser").find(["form", "input", "select", "textarea", "table"]):
            layout_blocks.append({"html": token.content, "lines": [token.map[0] + 1, token.map[1]]})
    body, removed = _sanitize(parser.renderer.render(tokens, parser.options, {}), source.parent, asset_root)
    result["safety"]["removed"].extend(removed)
    styles = "".join(str(tag) for tag in BeautifulSoup(body, "html.parser").find_all("style"))
    for index, block in enumerate(layout_blocks, 1):
        markup, removed = _sanitize(block["html"], source.parent, asset_root)
        result["safety"]["removed"].extend(removed)
        block.update(id=f"layout-{index:03}", html=_html(markup, styles))
        _write(destination / (block["id"] + ".html"), block["html"])
        result["layouts"].append({"id": block["id"], "sourceLines": block["lines"], "status": "NOT_RUN"})
    for diagram in diagrams:
        _write(destination / (diagram["id"] + ".mmd"), diagram["source"])
        result["diagrams"].append({"id": diagram["id"], "sourceLines": diagram["lines"], "sourceSha256": _sha(diagram["source"]), "status": "NOT_RENDERED"})
    executable = chromium_executable or os.environ.get("CONTEXTBASE_CHROMIUM_EXE")
    if executable and not _path(Path(executable)).is_file():
        executable = None
        result["display"]["errors"].append("Chromium executable unavailable")
    package = _path(mermaid_package) if mermaid_package is not None else None
    bundle = package / "dist/mermaid.min.js" if package else None
    if bundle and bundle.is_file():
        package_info = json.loads((package / "package.json").read_text(encoding="utf-8"))
        result["mermaid"] = {"version": package_info["version"], "bundleSha256": _sha(bundle.read_bytes()), "securityLevel": "strict", "secure": SECURE_KEYS}
    else:
        bundle = None
    try:
        if not executable:
            raise RuntimeError("Supply an existing Chromium executable; no browser download is performed")
        runtime = destination / ".runtime"
        with _playwright_runtime(runtime) as playwright:
            static = playwright.chromium.launch_persistent_context(str(runtime / "static"), executable_path=str(executable), headless=True,
                        java_script_enabled=False, viewport={"width": 1440, "height": 1000}, locale="ja-JP", service_workers="block",
                        downloads_path=str(runtime / "downloads"), traces_dir=str(runtime / "traces"))
            def block(route):
                result["display"]["blockedRequests"].append(route.request.url)
                route.abort()
            static.route("**/*", block)
            try:
                if bundle and diagrams:
                    diagram_context = playwright.chromium.launch_persistent_context(str(runtime / "mermaid"), executable_path=str(executable), headless=True,
                                          viewport={"width": 1440, "height": 1000}, locale="ja-JP", service_workers="block",
                                          downloads_path=str(runtime / "mermaid-downloads"), traces_dir=str(runtime / "mermaid-traces"))
                    diagram_context.route("**/*", block)
                    try:
                        for diagram, record in zip(diagrams, result["diagrams"]):
                            page = diagram_context.new_page()
                            projection_receipt = None
                            try:
                                projection = project_flowchart_edges(diagram["source"])
                                if reverse_projection(projection) != diagram["source"]:
                                    raise ValueError("Edge layout projection does not recover the canonical source")
                                repeated = project_flowchart_edges(projection.text)
                                if repeated.text != projection.text or repeated.insertions:
                                    raise ValueError("Edge layout projection is not idempotent")
                                projection_receipt = {"schema": "mermaid-edge-layout-projection/1", **projection.receipt(),
                                    "canonicalMmd": diagram["id"] + ".mmd", "viewMmd": diagram["id"] + ".view.mmd",
                                    "applied": bool(projection.insertions), "status": "NOT_RUN",
                                    "originalSvg": diagram["id"] + ".source.svg", "viewSvg": diagram["id"] + ".view.svg",
                                    "semanticSignatureCompared": False, "wholeVisibleTokensVerified": False}
                                _write(destination / projection_receipt["viewMmd"], projection.text)
                                record['layoutProjection'] = projection_receipt
                                page.set_content(_html("", scripts=True))
                                page.add_script_tag(path=str(bundle))
                                config = {"startOnLoad": False, "securityLevel": "strict", "secure": SECURE_KEYS, "htmlLabels": False,
                                          "themeCSS": MERMAID_LABEL_STYLE, "fontFamily": "sans-serif", "maxTextSize": 500000, "maxEdges": 10000,
                                          "suppressErrorRendering": True, "deterministicIds": True, "deterministicIDSeed": result["sourceSha256"],
                                          "flowchart": {"htmlLabels": False, "useMaxWidth": False,
                                                        "wrappingWidth": MERMAID_LABEL_WIDTH}}
                                rendered = page.evaluate("""async ({id,text,config}) => {
                                    mermaid.initialize(config);
                                    const {svg}=await mermaid.render(id,text);
                                    return {svg,securityLevel:mermaid.mermaidAPI.getConfig().securityLevel};
                                }""", {"id": diagram["id"], "text": diagram["source"], "config": config})
                                if rendered["securityLevel"] != "strict":
                                    raise ValueError("Mermaid security level changed")
                                original_svg = _svg_safe(rendered["svg"])
                                _write(destination / projection_receipt["originalSvg"], original_svg)
                                svg = original_svg
                                if projection.insertions:
                                    rendered = page.evaluate("""async ({id,text,config}) => {
                                        mermaid.initialize(config);
                                        const {svg}=await mermaid.render(id,text);
                                        return {svg,securityLevel:mermaid.mermaidAPI.getConfig().securityLevel};
                                    }""", {"id": diagram["id"], "text": projection.text, "config": config})
                                    if rendered["securityLevel"] != "strict":
                                        raise ValueError("Mermaid security level changed during layout projection")
                                    svg = _svg_safe(rendered["svg"])
                                _write(destination / projection_receipt["viewSvg"], svg)
                                projection_receipt.update(originalSvgSha256=_sha(original_svg), viewSvgSha256=_sha(svg))
                                if projection.supportedDiagram:
                                    signature = _flowchart_svg_signature(original_svg)
                                    validate_semantic_signature(signature, _flowchart_svg_signature(svg))
                                    projection_receipt.update(semanticSignatureCompared=True, semanticSignatureEqual=True,
                                        semanticSignatureSha256=_sha(json.dumps(signature, sort_keys=True, ensure_ascii=False)))
                                capture = static.new_page()
                                try:
                                    capture.set_content(_html(svg), wait_until="load")
                                    svg = _svg_safe(_protect_cluster_labels(capture))
                                    capture.set_content(_html(svg), wait_until="load")
                                    checks = validate_svg_label_rows(diagram["source"], projection, _edge_label_rows(capture))
                                    projection_receipt.update(visibleLabelChecks=checks,
                                        wholeVisibleTokensVerified=projection.supportedDiagram,
                                        excludedMarkdownBaselineLabels=sum(label.markdown for label in projection.labels),
                                        status="PASS" if projection.supportedDiagram else "UNMODIFIED_NON_FLOW_DISPLAY")
                                    _write(destination / (diagram["id"] + ".svg"), svg)
                                    data = _capture(capture, capture.locator("svg"))
                                finally:
                                    capture.close()
                                info = _png_info(data)
                                if not info["nonblank"]:
                                    raise ValueError("Blank diagram capture")
                                _write(destination / (diagram["id"] + ".png"), data)
                                record.update(status="PASS", png=info, securityLevel=rendered["securityLevel"])
                                image = 'data:image/png;base64,' + base64.b64encode(data).decode("ascii")
                                dom = BeautifulSoup(body, "html.parser")
                                figure = dom.find("figure", attrs={"data-renderer-diagram": str(int(diagram["id"].split("-")[1]))})
                                picture = dom.new_tag("img", src=image, attrs={"data-renderer-diagram": diagram["id"], "alt": diagram["id"]})
                                figure.insert(0, picture)
                                body = str(dom)
                            except Exception as exc:
                                record.update(status="ERROR", error=str(exc)[:1000])
                                if projection_receipt is not None:
                                    projection_receipt.update(status="ERROR", error=str(exc)[:1000], authorRevisionRequired=True)
                            finally:
                                if projection_receipt is not None:
                                    receipt_name = diagram["id"] + ".projection.json"
                                    receipt_raw = json.dumps(projection_receipt, ensure_ascii=False, indent=2) + "\n"
                                    _write(destination / receipt_name, receipt_raw)
                                    record['projectionReceipt'] = {'path': receipt_name, 'sha256': _sha(receipt_raw)}
                                page.close()
                    finally:
                        diagram_context.close()
                viewer = _html(body)
                _write(destination / "document.html", viewer)
                for block_info, record in zip(layout_blocks, result["layouts"]):
                    page = static.new_page()
                    try:
                        page.set_content(block_info["html"], wait_until="load")
                        data = _capture(page)
                        info = _png_info(data)
                        if not info["nonblank"]:
                            raise ValueError("Blank layout capture")
                        _write(destination / (block_info["id"] + ".png"), data)
                        record.update(status="PASS", png=info)
                    except Exception as exc:
                        record.update(status="ERROR", error=str(exc)[:1000])
                    finally:
                        page.close()
                page = static.new_page()
                try:
                    page.set_content(viewer, wait_until="load")
                    _capture_document(page, destination, result['display'])
                    result["display"]["browserUserAgent"] = page.evaluate("navigator.userAgent")
                    session = static.new_cdp_session(page)
                    try:
                        result["display"]["browserVersion"] = session.send("Browser.getVersion")["product"]
                    finally:
                        session.detach()
                finally:
                    page.close()
                result["display"]["status"] = "PASS"
            finally:
                static.close()
    except Exception as exc:
        result["display"]["errors"].append(str(exc)[:1000])
        result["display"]["status"] = "ERROR"
    if not (destination / "document.html").exists():
        _write(destination / "document.html", _html(body))
    if any(record["status"] != "PASS" for record in result["diagrams"] + result["layouts"]):
        result["display"]["status"] = "ERROR" if any(record["status"] == "ERROR" for record in result["diagrams"] + result["layouts"]) else "NOT_RENDERED"
    if result["display"]["blockedRequests"]:
        result["display"]["status"] = "ERROR"
    if result["safety"]["removed"]:
        result["safety"]["status"] = "SANITIZED_ORIGINAL_REQUIRES_REVISION"
        if result["display"]["status"] == "PASS":
            result["display"]["status"] = "SANITIZED"
    result["originalModified"] = source.read_bytes() != raw
    if result["originalModified"]:
        result["display"]["status"] = "SOURCE_CHANGED"
    for artifact in sorted(destination.iterdir()):
        if artifact.is_file():
            result["artifacts"].append({"path": artifact.name, "sha256": _sha(artifact.read_bytes()), "bytes": artifact.stat().st_size})
    result["scope"] = "Static derived display and image decoding only; no original application, source JavaScript, business execution, pixel oracle or semantic approval"
    _write(destination / "manifest.json", json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    return result

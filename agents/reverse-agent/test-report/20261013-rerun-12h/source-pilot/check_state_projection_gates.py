"""Exercise helper gates in isolation, without launching AI or reading manuscripts."""
from __future__ import annotations

import ast
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

source = Path(__file__).with_name("prepare_state_projection.py")
raw = source.read_bytes()
tree = ast.parse(raw.decode("utf-8"), filename=str(source))
definitions = ast.Module(body=[node for node in tree.body if isinstance(node, (ast.Import, ast.ImportFrom, ast.FunctionDef, ast.ClassDef))], type_ignores=[])
space = {"__name__": "projection_gate_check"}
exec(compile(definitions, str(source), "exec"), space)
tests = []


def expect_rejection(name, callback):
    try:
        callback()
    except ValueError:
        tests.append({"name": name, "status": "PASS_REJECTED"})
    else:
        raise AssertionError(f"unsafe gate input accepted: {name}")


def html(value):
    parser = space["InertHtml"]()
    parser.feed(value)
    parser.close()


html('<!doctype html><html><head><style>body{color:#222}@media(max-width:100px){body{display:block}}</style></head><body><form inert><input type="text"><button type="button">x</button></form></body></html>')
tests.append({"name": "self-contained inert-form HTML and embedded CSS", "status": "PASS_ACCEPTED"})
for name, value in (
    ("escaped CSS import", '<style>@im\\70ort "https://invalid.example/x.css";</style>'),
    ("escaped CSS URL function", '<style>body{background:u\\72l("https://invalid.example/x")}</style>'),
    ("unquoted URL token", '<div style="background:url(https://invalid.example/x)"></div>'),
    ("style attribute escaped URL", '<div style="background:u\\72l(https://invalid.example/x)"></div>'),
    ("image-set string external URL", '<style>body{background:image-set("https://invalid.example/x" 1x)}</style>'),
    ("webkit image-set string external URL", '<style>body{background:-webkit-image-set("https://invalid.example/x" 1x)}</style>'),
    ("escaped image-set string external URL", '<style>body{background:im\\61ge-set("https://invalid.example/x" 1x)}</style>'),
    ("image string external URL", '<style>body{background:image("https://invalid.example/x")}</style>'),
    ("src string external URL", '<style>body{background:src("https://invalid.example/x")}</style>'),
    ("SVG external reference", '<svg><use xlink:href="https://invalid.example/x"/></svg>'),
    ("poster URL", '<video poster="https://invalid.example/x"></video>'),
    ("srcset URL", '<img srcset="https://invalid.example/x 2x">'),
    ("blank event attribute", '<div onclick=""></div>'),
    ("form default submit", '<form><button type="button">x</button></form>'),
    ("input default submit", '<form inert><input type="submit"></form>'),
    ("button default submit", '<form inert><button>x</button></form>'),
    ("meta refresh", '<meta http-equiv="refresh" content="0;url=https://invalid.example/x">'),
    ("duplicate meta refresh attribute", '<meta http-equiv="refresh" http-equiv="x" content="0;url=https://invalid.example/x">'),
    ("duplicate button type attribute", '<form inert><button type="submit" type="button">x</button></form>'),
    ("unclosed style block", '<style>body{color:red}'),
):
    expect_rejection(name, lambda value=value: html(value))
content = "# One\ntext\n## Two\nvalue\n# Three\nend\n"
drafts = [{"sha256": "a" * 64, "headingRanges": space["heading_ranges"](content)}]
location = {"documentSha256": "a" * 64, "heading": "Two", "headingLine": 3, "startLine": 3, "endLine": 4}
space["validate_canonical_location"](location, drafts)
tests.append({"name": "exact SHA heading and section range", "status": "PASS_ACCEPTED"})
expect_rejection("wrong canonical SHA", lambda: space["validate_canonical_location"]({**location, "documentSha256": "b" * 64}, drafts))
expect_rejection("missing canonical heading", lambda: space["validate_canonical_location"]({**location, "heading": "Missing"}, drafts))
expect_rejection("canonical range crosses following section", lambda: space["validate_canonical_location"]({**location, "endLine": 6}, drafts))
expect_rejection("negative canonical line", lambda: space["validate_canonical_location"]({**location, "startLine": -1}, drafts))
report = Path(__file__).resolve().parent
repo = report.parents[4]
approved = repo / "test-project1/spec-analysis/CSharp_ASPNET/20261013-rerun-12h/source-only/drafts"
expect_rejection("outside approved draft root", lambda: space["canonical_path"](source, approved))
expect_rejection("noncanonical md path", lambda: space["canonical_path"](approved / "arbitrary.md", approved))
value = {"createdAt": datetime.now(timezone.utc).isoformat(), "helperFile": str(source),
         "helperSha256": hashlib.sha256(raw).hexdigest(), "tests": tests, "count": len(tests),
         "AIProviderLaunched": False, "applicationExecuted": False, "manuscriptReadOrModified": False,
         "strictRendererSanitizerStillRequired": True, "independentProjectionMeaningReviewStillRequired": True}
output = Path(sys.argv[1])
with output.open("x", encoding="utf-8", newline="\n") as stream:
    json.dump(value, stream, ensure_ascii=False, indent=2)
    stream.write("\n")
print(json.dumps({"status": "PASS", "count": len(tests), "helperSha256": value["helperSha256"], "report": str(output)}, ensure_ascii=False))

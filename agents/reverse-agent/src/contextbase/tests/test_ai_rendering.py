"""Synthetic real-browser rendering; no business programs or model calls."""
import base64
import hashlib
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
import xml.etree.ElementTree as ET

from PIL import Image

from contextbase.ai.rendering import render_document, _sanitize, _svg_safe, _png_info, _path


def fixture(body="", *, path="fixture.md"):
    meta = {"schema": "spec-md/1.0", "documentId": "SYNTHETIC", "version": "1.0", "path": path,
            "sheets": [{"heading": "自由な章", "kind": "GRID", "sheet": "自由な章"}]}
    return "<!-- spec-meta: " + json.dumps(meta, ensure_ascii=False) + " -->\n# 人工fixture\n\n## 自由な章\n\n" + body


class SafetyTests(unittest.TestCase):
    def setUp(self):
        root = Path(__file__).resolve().parents[3] / ".tmp/publication"
        root.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(prefix="render-unit-", dir=root)
        self.root = Path(self.temp.name)
        self.addCleanup(self.temp.cleanup)

    def test_arbitrary_classes_css_and_control_values_are_retained(self):
        raw = '<section class="arbitrary"><style>.arbitrary{display:grid;width:520px}.field{color:#123456}</style><form><input class="field" value="架空入力" readonly><table><tr><td>例</td></tr></table></form></section>'
        safe, removed = _sanitize(raw, self.root, self.root)
        self.assertFalse(removed)
        self.assertIn('class="arbitrary"', safe)
        self.assertIn("520px", safe)
        self.assertIn("架空入力", safe)
        self.assertIn("readonly", safe)

    def test_script_inline_events_and_embedded_frames_are_removed(self):
        safe, removed = _sanitize('<script>window.pwned=1</script><form action="https://example.invalid"><input onclick="run()"><iframe srcdoc="x"></iframe></form>', self.root, self.root)
        self.assertNotIn("<script", safe)
        self.assertNotIn("onclick", safe)
        self.assertNotIn("iframe", safe)
        self.assertNotIn("action=", safe)
        self.assertTrue(removed)

    def test_inert_encoding_and_viewport_metadata_are_retained(self):
        safe, removed = _sanitize('<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">', self.root, self.root)
        self.assertFalse(removed)
        self.assertIn('charset="utf-8"', safe.lower())
        self.assertIn('name="viewport"', safe)

    def test_refresh_and_mixed_metadata_remain_removed(self):
        safe, removed = _sanitize('<meta http-equiv="refresh" content="0;url=https://example.invalid"><meta charset="utf-8" http-equiv="refresh" content="0;url=https://example.invalid">', self.root, self.root)
        self.assertNotIn("<meta", safe)
        self.assertEqual(2, len(removed))

    def test_external_css_is_removed_but_inert_strings_are_preserved(self):
        raw = '<style>@import "https://example.invalid/a.css";.a{background:url(https://example.invalid/a.png);content:"url(https://example.invalid)"}</style>'
        safe, removed = _sanitize(raw, self.root, self.root)
        self.assertNotIn("@import", safe)
        self.assertIn("background:none", safe)
        self.assertIn('content:"url(https://example.invalid)"', safe)
        self.assertEqual(2, len(removed))

    def test_outside_image_is_not_read(self):
        safe, removed = _sanitize('<img src="../../secret.png">', self.root, self.root)
        self.assertNotIn("src=", safe)
        self.assertTrue(removed)

    def test_relative_related_document_citation_is_preserved_without_reading_it(self):
        detail = self.root/'detail'; detail.mkdir()
        value = '../共通/契約.md#入口'
        safe, removed = _sanitize('<a href="'+value+'">関連契約</a>',detail,self.root)
        self.assertFalse(removed)
        self.assertIn(value,safe)
        self.assertFalse((self.root/'共通/契約.md').exists())

    def test_local_citation_cannot_escape_the_publication_root(self):
        for target in ('../../secret.md','%2e%2e/%2e%2e/secret.md',
                       'file:///C:/secret.md','//example.invalid/secret.md',
                       'javascript:run()','../program.exe'):
            with self.subTest(target=target):
                safe, removed = _sanitize('<a href="'+target+'">参照</a>',self.root,self.root)
                self.assertNotIn('href=',safe)
                self.assertTrue(removed)

    def test_local_raster_is_verified_and_embedded(self):
        image = self.root / "picture.png"
        Image.new("RGB", (12, 12), "blue").save(image)
        safe, removed = _sanitize('<img src="picture.png">', self.root, self.root)
        self.assertFalse(removed)
        self.assertIn("data:image/png;base64,", safe)

    def test_external_svg_script_and_attribute_are_rejected(self):
        for fragment in ('<svg xmlns="http://www.w3.org/2000/svg"><script>run()</script></svg>', '<svg xmlns="http://www.w3.org/2000/svg" onload="run()"></svg>', '<svg xmlns="http://www.w3.org/2000/svg"><image href="https://example.invalid/a.png"/></svg>'):
            with self.subTest(fragment=fragment), self.assertRaises(ValueError):
                _svg_safe(fragment)

    def test_svg_viewbox_case_is_preserved(self):
        value = _svg_safe('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 50"><text x="2" y="20">人工</text></svg>')
        self.assertEqual("0 0 100 50", ET.fromstring(value).attrib["viewBox"])

    def test_svg_quoted_internal_resource_is_preserved(self):
        value = _svg_safe('<svg xmlns="http://www.w3.org/2000/svg"><path style=\'fill:url("#marker")\'/></svg>')
        self.assertIn('url("#marker")', ET.fromstring(value)[0].attrib["style"])

    def test_svg_external_presentation_resource_is_rejected(self):
        for attribute in ("fill", "filter", "clip-path"):
            with self.subTest(attribute=attribute), self.assertRaises(ValueError):
                _svg_safe('<svg xmlns="http://www.w3.org/2000/svg"><path ' + attribute + '="url(https://example.invalid/a.svg#marker)"/></svg>')

    def test_declarative_svg_animation_is_not_static_content(self):
        safe, removed = _sanitize('<svg><set attributeName="href" to="https://example.invalid/a.svg"/><animate attributeName="x" values="0;100"/></svg>', self.root, self.root)
        self.assertNotIn("<set", safe)
        self.assertNotIn("<animate", safe)
        self.assertEqual(2, len(removed))

    def test_css_internal_svg_filter_is_preserved(self):
        safe, removed = _sanitize('<svg><filter id="shadow"></filter><rect style=\'filter:url("#shadow")\'/></svg>', self.root, self.root)
        self.assertFalse(removed)
        self.assertIn("#shadow", safe)

    def test_html_svg_presentation_external_resource_is_sanitized(self):
        safe, removed = _sanitize('<svg><rect filter="url(https://example.invalid/filter.svg#x)"/></svg>', self.root, self.root)
        self.assertNotIn("https://example.invalid", safe)
        self.assertEqual(1, len(removed))

    def test_evaluation_path_is_rejected_before_any_file_read(self):
        for name in ("spec-eval", "SPEC-EVAL"):
            with self.subTest(name=name), self.assertRaises(ValueError):
                _path(self.root / name / "not-read.md")

    def test_png_decoding_is_real(self):
        buffer = io.BytesIO()
        image = Image.new("RGB", (20, 10), "white")
        image.putpixel((0, 0), (0, 0, 0))
        image.save(buffer, format="PNG")
        info = _png_info(buffer.getvalue())
        self.assertTrue(info["decoded"])
        self.assertTrue(info["nonblank"])
        self.assertEqual((20, 10), (info["width"], info["height"]))

    def test_invalid_png_is_not_success(self):
        with self.assertRaises(Exception):
            _png_info(b"not-an-image")


class RealRenderingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.agent = Path(__file__).resolve().parents[3]
        cls.chromium = Path(os.environ["CONTEXTBASE_CHROMIUM_EXE"])
        cls.mermaid = Path(os.environ["CONTEXTBASE_MERMAID_PACKAGE"])
        cls.run_root = Path(os.environ["CONTEXTBASE_RENDER_TEST_RUN"])
        cls.run_root.mkdir(parents=True, exist_ok=False)
        text = fixture('''<section class="random-container"><style>.random-container{width:620px;background:#f1f5ff;padding:12px}.random-container input{width:180px}</style><form><label>架空項目<input value="TEST-RENDER-0001" readonly></label><table><tr><th>架空列</th></tr><tr><td>表示のみ</td></tr></table></form></section>

```mermaid
flowchart LR
 A[開始] --> B{判定}
 B -->|成立| C[表示]
```

```mermaid
sequenceDiagram
 participant A as 呼出側
 participant B as 保持領域
 A->>B: 架空要求
 B-->>A: 架空応答
```

```mermaid
erDiagram
 ENTITY_A ||--o{ ENTITY_B : relates
 ENTITY_A { int id PK }
 ENTITY_B { int id PK }
```
''')
        cls.source = cls.run_root / "fixture.md"
        cls.source.write_bytes(text.encode("utf-8"))
        cls.before = cls.source.read_bytes()
        cls.result = render_document(cls.source, cls.run_root / "positive", mermaid_package=cls.mermaid,
                                     chromium_executable=cls.chromium)

    def test_real_display_and_structure_are_separate_passes(self):
        self.assertEqual("PASS", self.result["structure"]["status"])
        self.assertEqual("PASS", self.result["display"]["status"])
        self.assertEqual("NOT_ASSESSED", self.result["semanticApproval"])

    def test_original_ai_markdown_remains_byte_identical(self):
        self.assertEqual(self.before, self.source.read_bytes())
        self.assertFalse(self.result["originalModified"])

    def test_relative_document_citation_is_inert_in_real_browser(self):
        detail = self.run_root/'detail'; detail.mkdir()
        source = detail/'citation.md'
        source.write_text(fixture('<a href="../共通/契約.md#入口">関連契約</a>',path='citation.md'),encoding='utf-8')
        result = render_document(source,self.run_root/'relative-citation',
                  chromium_executable=self.chromium,asset_root=self.run_root)
        self.assertEqual('PASS',result['display']['status'],result['display'])
        self.assertEqual([],result['display']['blockedRequests'])
        self.assertEqual([],result['safety']['removed'])
        self.assertIn('../共通/契約.md#入口',(self.run_root/'relative-citation/document.html').read_text(encoding='utf-8'))

    def test_long_document_captures_every_strip_with_bounded_images(self):
        source = self.run_root / 'long.md'
        source.write_text(fixture(''.join('<p>人工文書の行 %d</p>\n' % i for i in range(700)),
                                  path='long.md'), encoding='utf-8')
        before = source.read_bytes()
        result = render_document(source, self.run_root/'long', chromium_executable=self.chromium)
        self.assertEqual('PASS', result['display']['status'], result['display'])
        capture = result['display']['documentCapture']
        self.assertTrue(capture['complete'])
        self.assertGreater(capture['height'], 16000)
        next_y = 0
        for record in capture['pages']:
            bounds = record['sourceRectangle']
            self.assertEqual(next_y, bounds['y'])
            self.assertEqual(capture['width'], bounds['width'])
            self.assertLessEqual(record['png']['height'], 4000)
            self.assertTrue(record['png']['decoded'])
            image_file = self.run_root/'long'/record['path']
            self.assertEqual(record['png']['sha256'], hashlib.sha256(image_file.read_bytes()).hexdigest())
            next_y += bounds['height']
        self.assertEqual(capture['height'], next_y)
        self.assertEqual(before, source.read_bytes())

    def test_flow_sequence_and_er_are_rendered_with_original_sources(self):
        self.assertEqual(3, len(self.result["diagrams"]))
        for diagram in self.result["diagrams"]:
            self.assertEqual("PASS", diagram["status"], diagram)
            self.assertEqual("strict", diagram["securityLevel"])
            self.assertTrue((self.run_root / "positive" / (diagram["id"] + ".svg")).is_file())
            self.assertEqual(diagram["sourceSha256"], hashlib.sha256((self.run_root / "positive" / (diagram["id"] + ".mmd")).read_bytes()).hexdigest())

    def test_generic_layout_is_captured_without_required_classes(self):
        self.assertEqual(1, len(self.result["layouts"]))
        self.assertEqual("PASS", self.result["layouts"][0]["status"])
        self.assertTrue(self.result["layouts"][0]["png"]["nonblank"])
        self.assertIn("random-container", (self.run_root / "positive/layout-001.html").read_text(encoding="utf-8"))

    def test_no_external_request_occurs(self):
        self.assertEqual([], self.result["display"]["blockedRequests"])
        self.assertEqual([], self.result["safety"]["removed"])

    def test_every_artifact_hash_matches(self):
        for artifact in self.result["artifacts"]:
            raw = (self.run_root / "positive" / artifact["path"]).read_bytes()
            self.assertEqual(artifact["sha256"], hashlib.sha256(raw).hexdigest())

    def test_sanitized_input_is_not_called_faithful_pass(self):
        source = self.run_root / "unsafe.md"
        raw = fixture('<section class="x"><script>window.originalScriptRan=1;fetch("https://example.invalid/leak")</script><style>.x{background:url(https://example.invalid/remote.png)}</style><input onclick="window.originalScriptRan=2" value="架空"></section>', path="unsafe.md")
        source.write_bytes(raw.encode("utf-8"))
        result = render_document(source, self.run_root / "sanitized", chromium_executable=self.chromium)
        self.assertEqual("SANITIZED", result["display"]["status"])
        self.assertTrue(result["safety"]["removed"])
        self.assertEqual([], result["display"]["blockedRequests"])
        self.assertEqual(raw.encode("utf-8"), source.read_bytes())

    def test_bad_mermaid_does_not_become_display_pass(self):
        source = self.run_root / "bad.md"
        source.write_text(fixture("```mermaid\nnot-a-real-diagram !!!\n```\n", path="bad.md"), encoding="utf-8")
        result = render_document(source, self.run_root / "bad", mermaid_package=self.mermaid, chromium_executable=self.chromium)
        self.assertEqual("ERROR", result["diagrams"][0]["status"])
        self.assertNotEqual("PASS", result["display"]["status"])
        self.assertTrue((self.run_root / "bad/diagram-001.mmd").is_file())

    def test_missing_mermaid_dependency_is_not_rendered(self):
        source = self.run_root / "missing.md"
        source.write_text(fixture("```mermaid\ngraph LR\n A --> B\n```\n", path="missing.md"), encoding="utf-8")
        result = render_document(source, self.run_root / "missing", chromium_executable=self.chromium)
        self.assertEqual("NOT_RENDERED", result["diagrams"][0]["status"])
        self.assertNotEqual("PASS", result["display"]["status"])

    def test_standalone_header_metadata_is_display_pass_without_source_rewrite(self):
        source = self.run_root / "metadata.md"
        raw = fixture('<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head><body><form data-source-action="/original"><input value="fixture"><button type="button">操作</button></form><a href="#local" data-source-route="/original">遷移</a></body></html>', path="metadata.md")
        source.write_bytes(raw.encode('utf-8'))
        result = render_document(source, self.run_root / "metadata", chromium_executable=self.chromium)
        self.assertEqual("PASS", result['structure']['status'])
        self.assertEqual("PASS", result['display']['status'])
        self.assertEqual([], result['safety']['removed'])
        self.assertEqual([], result['display']['blockedRequests'])
        self.assertEqual(raw.encode('utf-8'), source.read_bytes())
        self.assertFalse(result['safety']['inputJavaScriptEnabled'])

    def test_grid_pipe_overflow_is_reported_and_escaped_form_keeps_result(self):
        header='| Trigger | Condition | Outcome |\n| --- | --- | --- |\n'
        rows={'grid-overflow':'| T | `alpha || beta` | Result sentinel |\n',
              'grid-escaped':r'| T | `alpha \|\| beta` | Result sentinel |'+'\n'}
        for name,row in rows.items():
            with self.subTest(name=name):
                source=self.run_root/(name+'.md')
                raw=fixture(header+row,path=name+'.md').encode('utf-8')
                source.write_bytes(raw)
                result=render_document(source,self.run_root/name,chromium_executable=self.chromium)
                self.assertEqual('PASS',result['display']['status'])
                rendered=(self.run_root/name/'document.html').read_text(encoding='utf-8')
                if name=='grid-overflow':
                    self.assertEqual('ERROR',result['structure']['status'])
                    self.assertIn('TABLE_CELL_OVERFLOW',{item['code'] for item in result['structure']['findings']})
                    self.assertNotIn('Result sentinel',rendered)
                else:
                    self.assertEqual('PASS',result['structure']['status'])
                    self.assertIn('<code>alpha || beta</code>',rendered)
                    self.assertIn('<td>Result sentinel</td>',rendered)
                self.assertEqual(raw,source.read_bytes())

    def test_destination_reuse_is_rejected(self):
        with self.assertRaises(FileExistsError):
            render_document(self.source, self.run_root / "positive", chromium_executable=self.chromium)

    def test_mermaid_directive_cannot_lower_strict_security(self):
        source = self.run_root / "directive.md"
        raw = fixture('''```mermaid
%%{init: {"securityLevel":"loose","secure":[],"htmlLabels":true}}%%
flowchart LR
 A["<img src=x onerror=window.pwned=1>"] --> B[表示]
 click A callback
```
''', path="directive.md")
        source.write_bytes(raw.encode("utf-8"))
        result = render_document(source, self.run_root / "directive", mermaid_package=self.mermaid, chromium_executable=self.chromium)
        self.assertEqual("strict", result["diagrams"][0].get("securityLevel"), result["diagrams"])
        self.assertEqual("PASS", result["diagrams"][0]["status"])
        self.assertEqual([], result["display"]["blockedRequests"])
        svg = ET.fromstring((self.run_root / "directive/diagram-001.svg").read_text(encoding="utf-8"))
        self.assertFalse(any(key.lower().startswith("on") for element in svg.iter() for key in element.attrib))

    def test_structural_failure_is_not_repaired_by_rendering(self):
        source = self.run_root / "unstructured.md"
        raw = b"# Synthetic unstructured title\n\nplain text\n"
        source.write_bytes(raw)
        result = render_document(source, self.run_root / "unstructured", chromium_executable=self.chromium)
        self.assertEqual("ERROR", result["structure"]["status"])
        self.assertEqual("PASS", result["display"]["status"])
        self.assertEqual(raw, source.read_bytes())

    def test_missing_browser_is_not_display_success(self):
        source = self.run_root / "no-browser.md"
        source.write_bytes(fixture("本文", path="no-browser.md").encode("utf-8"))
        result = render_document(source, self.run_root / "no-browser", chromium_executable=self.run_root / "missing.exe")
        self.assertEqual("ERROR", result["display"]["status"])
        self.assertTrue((self.run_root / "no-browser/document.html").is_file())

    def test_browser_profiles_are_inside_publication(self):
        self.assertTrue((self.run_root / "positive/.runtime/static").is_dir())
        self.assertTrue((self.run_root / "positive/.runtime/mermaid").is_dir())
        self.assertTrue((self.run_root / "positive/.runtime/tmp").is_dir())

    def test_blank_document_capture_is_not_display_success(self):
        source = self.run_root / "blank.md"
        source.write_bytes(fixture('<style>body{color:white;background:white}</style>', path="blank.md").encode("utf-8"))
        result = render_document(source, self.run_root / "blank", chromium_executable=self.chromium)
        self.assertEqual("ERROR", result["display"]["status"])
        self.assertFalse(result["display"]["documentPng"]["nonblank"])
        self.assertTrue((self.run_root / "blank/document.png").is_file())


if __name__ == "__main__":
    unittest.main()

"""Synthetic real-browser rendering; no business programs or model calls."""
import base64
import hashlib
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET

from PIL import Image

from contextbase.ai.rendering import (render_document, _sanitize, _svg_safe, _png_info, _path,
    _markdown_table_open, _flowchart_svg_signature)


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

    def test_css_image_set_string_resources_use_the_same_no_network_gate(self):
        raw = '<style>.a{background:image-set("https://example.invalid/a.png" 1x,url("https://example.invalid/b.png") 2x);content:"https://example.invalid/plain"}</style>'
        safe, removed = _sanitize(raw, self.root, self.root)
        self.assertNotIn('a.png', safe)
        self.assertNotIn('b.png', safe)
        self.assertIn('content:"https://example.invalid/plain"', safe)
        self.assertEqual(2, len(removed))

    def test_local_image_set_string_is_embedded_without_reinterpreting_type_metadata(self):
        picture = self.root / 'local.png'
        Image.new('RGB', (12, 12), 'blue').save(picture)
        raw = '<style>.a{background:-webkit-image-set("local.png" type("image/png") 1x)}</style>'
        safe, removed = _sanitize(raw, self.root, self.root)
        self.assertFalse(removed)
        self.assertIn('data:image/png;base64,', safe)
        self.assertIn('type("image/png")', safe)

    def test_markdown_table_widths_and_borders_do_not_rewrite_screen_html(self):
        from markdown_it import MarkdownIt
        from bs4 import BeautifulSoup
        parser = MarkdownIt('commonmark', {'html': True}).enable('table')
        parser.renderer.rules['table_open'] = lambda tokens, index, options, env: _markdown_table_open(tokens, index, options, env, parser.renderer)
        raw = '| 属性 | 説明 |\n| --- | --- |\n| 値 | 十分な説明 |\n\n<table class="source"><tr><td>画面値</td></tr></table>\n'
        soup = BeautifulSoup(parser.render(raw), 'html.parser')
        tables = soup.find_all('table')
        self.assertEqual('2', tables[0]['data-renderer-columns'])
        self.assertEqual(['width:24%', 'width:76%'], [col['style'] for col in tables[0].find_all('col')])
        self.assertEqual(['属性', '説明', '値', '十分な説明'], [cell.text for cell in tables[0].find_all(['th', 'td'])])
        self.assertNotIn('data-renderer-markdown', tables[1].attrs)
        self.assertIsNone(tables[1].find('colgroup'))
        self.assertEqual('画面値', tables[1].td.text)

    def test_many_column_markdown_table_keeps_column_order_and_readable_label_space(self):
        from markdown_it import MarkdownIt
        from bs4 import BeautifulSoup
        parser = MarkdownIt('commonmark').enable('table')
        parser.renderer.rules['table_open'] = lambda tokens, index, options, env: _markdown_table_open(tokens, index, options, env, parser.renderer)
        raw = '| No | 名称 | 型 | 説明 |\n| --- | --- | --- | --- |\n| 01 | 値 | string | 原文の説明 |\n'
        table = BeautifulSoup(parser.render(raw), 'html.parser').table
        self.assertEqual('4', table['data-renderer-columns'])
        self.assertEqual(['width:4%', 'width:28%', 'width:28%', 'width:40%'], [col['style'] for col in table.find_all('col')])
        self.assertEqual(['01', '値', 'string', '原文の説明'], [cell.text for cell in table.find_all('td')])

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

    def test_svg_semantics_include_endpoints_markers_shapes_and_clusters(self):
        from contextbase.ai.edge_label_projection import validate_semantic_signature, ProjectionError
        svg = '''<svg xmlns="http://www.w3.org/2000/svg"><g class="node" id="flowchart-A-0"><rect width="100"/><text>A</text></g>
<path class="flowchart-link LS-A LE-B edge-pattern-solid edge-thickness-normal" data-id="L_A_B_0" marker-end="url(#arrow)" d="M0,0L1,1"/>
<g class="edgeLabel"><g class="label" data-id="L_A_B_0"><text>condition</text></g></g>
<g class="cluster" id="SG"><rect width="200"/><g class="cluster-label"><text>Scope</text></g></g></svg>'''
        baseline = _flowchart_svg_signature(svg)
        moved = svg.replace('width="100"', 'width="300"').replace('M0,0L1,1', 'M5,5L20,20')
        self.assertTrue(validate_semantic_signature(baseline, _flowchart_svg_signature(moved)))
        for old, new in [('LE-B', 'LE-C'), ('url(#arrow)', 'url(#circle)'),
                         ('edge-pattern-solid', 'edge-pattern-dotted'), ('<rect width="100"/>', '<circle r="50"/>'),
                         ('<text>condition</text>', '<text>changed</text>'), ('<text>Scope</text>', '<text>Other</text>')]:
            with self.subTest(change=old), self.assertRaises(ProjectionError):
                validate_semantic_signature(baseline, _flowchart_svg_signature(svg.replace(old, new)))


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

    def test_opaque_edge_labels_preserve_every_diagram_coordinate_and_label(self):
        source = self.run_root / 'opaque-labels.md'
        raw = fixture('```mermaid\nflowchart LR\n A[Start] -->|branch alpha| B[Continue]\n A -->|branch beta| C[Stop]\n C --> B\n```\n', path=source.name).encode('utf-8')
        source.write_bytes(raw)
        with patch('contextbase.ai.rendering.MERMAID_LABEL_STYLE', ''):
            baseline = render_document(source, self.run_root/'opaque-baseline', mermaid_package=self.mermaid, chromium_executable=self.chromium)
        fixed = render_document(source, self.run_root/'opaque-fixed', mermaid_package=self.mermaid, chromium_executable=self.chromium)
        for result in (baseline, fixed):
            self.assertEqual('PASS', result['display']['status'], result['display'])
            self.assertEqual([], result['display']['blockedRequests'])
        def signature(path):
            root = ET.fromstring(path.read_text(encoding='utf-8'))
            return [(element.tag, tuple(sorted(element.attrib.items())), element.text or '')
                    for element in root.iter() if element.tag.rsplit('}', 1)[-1] != 'style']
        self.assertEqual(signature(self.run_root/'opaque-baseline/diagram-001.svg'),
                         signature(self.run_root/'opaque-fixed/diagram-001.svg'))
        self.assertEqual(baseline['diagrams'][0]['sourceSha256'], fixed['diagrams'][0]['sourceSha256'])
        self.assertEqual(baseline['diagrams'][0]['png']['width'], fixed['diagrams'][0]['png']['width'])
        self.assertEqual(baseline['diagrams'][0]['png']['height'], fixed['diagrams'][0]['png']['height'])
        self.assertEqual(raw, source.read_bytes())

    def test_author_directive_cannot_make_edge_label_background_transparent(self):
        source = self.run_root / 'label-directive.md'
        raw = fixture('''```mermaid
%%{init: {"themeCSS":".edgeLabel rect{opacity:0!important}","secure":[]}}%%
flowchart LR
 A[Start] -->|condition| B[End]
```
''', path=source.name).encode('utf-8')
        source.write_bytes(raw)
        result = render_document(source, self.run_root/'label-directive', mermaid_package=self.mermaid, chromium_executable=self.chromium)
        self.assertEqual('PASS', result['display']['status'], result['display'])
        from contextbase.ai.rendering import _playwright_runtime, _html
        with _playwright_runtime(self.run_root/'label-style-probe') as playwright:
            browser = playwright.chromium.launch(executable_path=str(self.chromium), headless=True)
            try:
                context = browser.new_context(java_script_enabled=False, service_workers='block')
                context.route('**/*', lambda route: route.abort())
                page = context.new_page()
                page.set_content(_html((self.run_root/'label-directive/diagram-001.svg').read_text(encoding='utf-8')))
                styles = page.locator('.edgeLabel rect').evaluate_all('(elements)=>elements.map(e=>({opacity:getComputedStyle(e).opacity,fill:getComputedStyle(e).fill}))')
                self.assertTrue(styles)
                self.assertTrue(all(style == {'opacity': '1', 'fill': 'rgb(255, 255, 255)'} for style in styles), styles)
            finally:
                browser.close()
        self.assertEqual(raw, source.read_bytes())

    def test_visible_long_identifiers_and_numbers_are_not_split_into_fragments(self):
        source = self.run_root / 'atomic-labels.md'
        labels = ['SyntheticIdentifierWithLongName', '900000000000000123', 'OperationCanceledException']
        body = '```mermaid\nflowchart TD\n A["'+labels[0]+'"] -->|accepted| B["'+labels[1]+'"]\n B --> C["'+labels[2]+'"]\n```\n'
        raw = fixture(body, path=source.name).encode('utf-8')
        source.write_bytes(raw)
        result = render_document(source, self.run_root/'atomic-labels', mermaid_package=self.mermaid, chromium_executable=self.chromium)
        self.assertEqual('PASS', result['display']['status'], result['display'])
        self.assertEqual([], result['display']['blockedRequests'])
        root = ET.fromstring((self.run_root/'atomic-labels/diagram-001.svg').read_text(encoding='utf-8'))
        rows = [''.join(element.itertext()) for element in root.iter()
                if 'text-outer-tspan' in element.get('class', '').split()]
        for label in labels:
            self.assertIn(label, rows, rows)
        self.assertEqual(raw, source.read_bytes())

    def test_cluster_title_overlay_keeps_label_node_and_edge_geometry(self):
        source = self.run_root/'cluster-title.md'
        raw = fixture('''```mermaid
flowchart TD
 A[Entry] --> B
 subgraph G[Long synthetic group title]
 B[Work] --> C[Complete]
 end
 C --> D[Exit]
```
''', path=source.name).encode('utf-8')
        source.write_bytes(raw)
        with patch('contextbase.ai.rendering._protect_cluster_labels',
                   lambda page: page.locator('svg').evaluate('(svg)=>svg.outerHTML')):
            baseline = render_document(source, self.run_root/'cluster-title-baseline',mermaid_package=self.mermaid,chromium_executable=self.chromium)
        fixed = render_document(source,self.run_root/'cluster-title-fixed',mermaid_package=self.mermaid,chromium_executable=self.chromium)
        from contextbase.ai.rendering import _playwright_runtime, _html
        observed = []
        with _playwright_runtime(self.run_root/'cluster-title-probe') as playwright:
            browser = playwright.chromium.launch(executable_path=str(self.chromium),headless=True)
            try:
                for name, result in [('cluster-title-baseline',baseline),('cluster-title-fixed',fixed)]:
                    self.assertEqual('PASS',result['display']['status'],result['display'])
                    self.assertEqual([],result['display']['blockedRequests'])
                    context = browser.new_context(java_script_enabled=False,service_workers='block')
                    context.route('**/*',lambda route:route.abort())
                    page = context.new_page()
                    page.set_content(_html((self.run_root/name/'diagram-001.svg').read_text(encoding='utf-8')))
                    observed.append(page.locator('g.node,path.flowchart-link,g.cluster-label').evaluate_all('''elements => elements.map(e=>({
                        kind:e.getAttribute('class'),text:e.textContent,box:e.getBoundingClientRect().toJSON()
                    })).sort((a,b)=>(a.kind+a.text).localeCompare(b.kind+b.text))'''))
                    if name.endswith('fixed'):
                        self.assertEqual(1,page.locator('g.trusted-cluster-label-overlay').count())
                        paint = page.locator('[data-trusted-label-background]').evaluate('(e)=>({fill:getComputedStyle(e).fill,opacity:getComputedStyle(e).opacity,stroke:getComputedStyle(e).stroke})')
                        self.assertEqual({'fill':'rgb(255, 255, 255)','opacity':'1','stroke':'none'},paint)
                    context.close()
            finally:
                browser.close()
        self.assertEqual(len(observed[0]),len(observed[1]))
        for before,after in zip(*observed):
            self.assertEqual((before['kind'],before['text']),(after['kind'],after['text']))
            for key in ('x','y','width','height'):
                self.assertAlmostEqual(before['box'][key],after['box'][key],places=3)
        self.assertEqual(raw,source.read_bytes())

    def test_author_width_override_cannot_fragment_the_trusted_label_layout(self):
        graph = 'flowchart LR\n A["SyntheticIdentifierWithLongName"] -->|branch| B["900000000000000123"]\n'
        directive = '%%{init: {"flowchart":{"wrappingWidth":8,"minNodeWidth":8,"htmlLabels":true},"htmlLabels":true,"secure":[]}}%%\n'
        signatures = []
        for name, prefix in [('width-baseline', ''), ('width-hostile', directive)]:
            source = self.run_root/(name+'.md')
            raw = fixture('```mermaid\n'+prefix+graph+'```\n', path=source.name).encode('utf-8')
            source.write_bytes(raw)
            result = render_document(source, self.run_root/name, mermaid_package=self.mermaid, chromium_executable=self.chromium)
            self.assertEqual('PASS', result['display']['status'], result['display'])
            self.assertEqual('strict', result['diagrams'][0]['securityLevel'])
            root = ET.fromstring((self.run_root/name/'diagram-001.svg').read_text(encoding='utf-8'))
            self.assertFalse(any(element.tag.rsplit('}',1)[-1] == 'foreignObject' for element in root.iter()))
            nodes = [element for element in root.iter() if 'node' in element.get('class','').split()]
            signatures.append([(node.get('transform'), ''.join(node.itertext()),
                [(child.tag, tuple(sorted(child.attrib.items()))) for child in node
                 if child.tag.rsplit('}',1)[-1] in ('rect','polygon','path')]) for node in nodes])
            self.assertEqual(raw, source.read_bytes())
        self.assertEqual(signatures[0], signatures[1])

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

    def _render_edge_fixture(self, name, graph):
        source = self.run_root / (name + '.md')
        raw = fixture('```mermaid\n' + graph + '\n```\n', path=source.name).encode('utf-8')
        source.write_bytes(raw)
        destination = self.run_root / name
        result = render_document(source, destination, mermaid_package=self.mermaid,
            chromium_executable=self.chromium)
        self.assertEqual(raw, source.read_bytes())
        self.assertEqual(graph + '\n', (destination / 'diagram-001.mmd').read_text(encoding='utf-8'))
        return destination, result

    def test_edge_projection_native_whole_tokens_and_provenance(self):
        graph = ('flowchart TD\n subgraph SG[架空の領域]\n'
                 ' A[入力] -->|条件InputValidationException又はArgumentException発生| B{判定}\n'
                 ' B -- 値10001件または1.0の場合 --> C[完了]\n end')
        destination, result = self._render_edge_fixture('edge-whole-token', graph)
        self.assertEqual('PASS', result['display']['status'], result['diagrams'])
        diagram = result['diagrams'][0]
        receipt = json.loads((destination / 'diagram-001.projection.json').read_text(encoding='utf-8'))
        self.assertTrue(receipt['applied'])
        self.assertTrue(receipt['semanticSignatureEqual'])
        self.assertTrue(receipt['wholeVisibleTokensVerified'])
        self.assertEqual('PASS', receipt['status'])
        self.assertNotEqual(receipt['sourceSha256'], receipt['projectedSha256'])
        from contextbase.ai.edge_label_projection import project_flowchart_edges, reverse_projection
        projection = project_flowchart_edges(graph + '\n')
        self.assertEqual(graph + '\n', reverse_projection(projection))
        self.assertEqual(projection.text, (destination / 'diagram-001.view.mmd').read_text(encoding='utf-8'))
        self.assertEqual(receipt['projectedSha256'], hashlib.sha256(projection.text.encode('utf-8')).hexdigest())
        self.assertEqual(diagram['projectionReceipt']['sha256'],
            hashlib.sha256((destination / 'diagram-001.projection.json').read_bytes()).hexdigest())
        tokens = [token for check in receipt['visibleLabelChecks'] for token in check.get('tokens', [])]
        for token in ['InputValidationException', 'ArgumentException', '10001', '1.0']:
            self.assertIn(token, tokens)
        self.assertEqual([], result['display']['blockedRequests'])
        self.assertFalse(result['safety']['inputJavaScriptEnabled'])

    def test_edge_projection_oversized_identifier_requires_author_revision(self):
        token = 'VeryLongIndivisibleIdentifier' * 4
        destination, result = self._render_edge_fixture('edge-oversized',
            'flowchart TD\n A -->|条件' + token + '発生| B')
        self.assertEqual('ERROR', result['display']['status'])
        self.assertEqual('ERROR', result['diagrams'][0]['status'])
        receipt = json.loads((destination / 'diagram-001.projection.json').read_text(encoding='utf-8'))
        self.assertTrue(receipt['authorRevisionRequired'])
        self.assertIn('Indivisible label token', receipt['error'])
        self.assertTrue(receipt['semanticSignatureEqual'])
        self.assertFalse(receipt['wholeVisibleTokensVerified'])
        self.assertFalse((destination / 'diagram-001.png').exists())

    def test_node_literals_are_bound_to_visible_whole_tokens_and_original_source(self):
        graph = 'flowchart TD\n A["Alpha Beta<br/>日本語400・422とModelState"] --> B["終端"]'
        destination, result = self._render_edge_fixture('node-token-positive', graph)
        self.assertEqual('PASS', result['display']['status'], result['diagrams'])
        self.assertEqual(graph+'\n', (destination/'diagram-001.mmd').read_text(encoding='utf-8'))
        receipt = json.loads((destination/'diagram-001.projection.json').read_text(encoding='utf-8'))
        self.assertTrue(receipt['wholeVisibleNodeTokensVerified'])
        self.assertEqual('PASS_VISIBLE_WHOLE_NODE_TOKENS', receipt['nodeLabelProof']['status'])
        tokens = [t['token'] for n in receipt['nodeLabelProof']['nodes'] for t in n['tokens']]
        self.assertEqual(['Alpha','Beta','400','422','ModelState'], tokens)
        self.assertEqual(receipt['canonicalNodeLiteralsSha256'], hashlib.sha256(json.dumps(
            receipt['canonicalNodeLiterals'],sort_keys=True,ensure_ascii=False).encode('utf-8')).hexdigest())
        self.assertTrue((destination/'diagram-001.png').exists())

    def test_indivisible_oversized_node_token_is_rejected_before_final_png(self):
        destination, result = self._render_edge_fixture('node-token-oversized',
            'flowchart LR\n A["'+'A'*180+'"] --> B["終端"]')
        self.assertEqual('ERROR', result['display']['status'])
        receipt = json.loads((destination/'diagram-001.projection.json').read_text(encoding='utf-8'))
        self.assertTrue(receipt['authorRevisionRequired'])
        self.assertFalse(receipt['wholeVisibleNodeTokensVerified'])
        self.assertIn('Indivisible node token', receipt['error'])
        self.assertFalse((destination/'diagram-001.png').exists())

    def test_unproven_node_effective_visibility_is_rejected_before_final_png(self):
        from contextbase.ai import rendering
        original = rendering._node_label_rows
        def hidden_measurement(page):
            measured = original(page)
            measured['nodes'][0]['rows'][0]['effectiveVisible'] = False
            return measured
        with patch.object(rendering, '_node_label_rows', side_effect=hidden_measurement):
            destination, result = self._render_edge_fixture('node-token-hidden',
                'flowchart TD\n A["Alpha"] --> B["Beta"]')
        self.assertEqual('ERROR', result['display']['status'])
        receipt = json.loads((destination/'diagram-001.projection.json').read_text(encoding='utf-8'))
        self.assertTrue(receipt['authorRevisionRequired'])
        self.assertIn('effective ancestor/fill visibility', receipt['error'])
        self.assertFalse((destination/'diagram-001.png').exists())

    def test_actual_svg_transparent_fill_is_rejected_but_partial_alpha_is_visible(self):
        from contextbase.ai.rendering import _node_label_rows, _playwright_runtime
        from contextbase.ai.node_label_row_gate import prove_node_rows, NodeLabelProofError
        destination = self.run_root/'node-effective-fill-regression'
        destination.mkdir(exist_ok=False)
        blocked = []
        results = []
        with _playwright_runtime(destination/'.runtime') as playwright:
            context = playwright.chromium.launch_persistent_context(
                str(destination/'.runtime/static'), executable_path=str(self.chromium), headless=True,
                java_script_enabled=False, viewport={'width':640,'height':240},
                service_workers='block')
            context.route('**/*', lambda route: (blocked.append(route.request.url), route.abort())[1])
            try:
                page = context.new_page()
                for fill, visible in [('transparent',False),('rgba(17,34,51,0)',False),
                                      ('rgba(17,34,51,0.4)',True)]:
                    document = ('<svg xmlns="http://www.w3.org/2000/svg" width="600" height="200">'
                        '<g class="node" id="synthetic-A"><rect x="20" y="20" width="400" height="100" '
                        'fill="white"/><text x="40" y="70" font-size="24" fill="'+fill+'">'
                        '<tspan class="text-outer-tspan">Alpha422</tspan></text></g></svg>')
                    page.set_content(document, wait_until='load')
                    measured = _node_label_rows(page)
                    self.assertEqual(visible, measured['nodes'][0]['rows'][0]['effectiveVisible'])
                    vertex = {'id':'A','domId':'synthetic-A','labelType':'text','text':'Alpha422'}
                    if visible:
                        proof = prove_node_rows([vertex],measured['nodes'],measured['canvas'])
                        self.assertEqual('PASS_VISIBLE_WHOLE_NODE_TOKENS',proof['status'])
                    else:
                        with self.assertRaisesRegex(NodeLabelProofError,'effective ancestor/fill visibility'):
                            prove_node_rows([vertex],measured['nodes'],measured['canvas'])
                    results.append({'fill':fill,'expectedVisible':visible,'measurement':measured})
            finally:
                context.close()
        self.assertEqual([],blocked)
        (destination/'measurements.json').write_text(json.dumps(results,indent=2),encoding='utf-8')

    def test_edge_projection_semantic_difference_is_rejected(self):
        destination, result = self._render_edge_fixture('edge-semantic-reject',
            'flowchart TD\n A -->|"条件ArgumentException text --> literal"| B')
        self.assertEqual('ERROR', result['display']['status'])
        receipt = json.loads((destination / 'diagram-001.projection.json').read_text(encoding='utf-8'))
        self.assertTrue(receipt['authorRevisionRequired'])
        self.assertIn('changes visible SVG', receipt['error'])
        self.assertFalse(receipt['wholeVisibleTokensVerified'])
        self.assertFalse((destination / 'diagram-001.png').exists())

    def test_edge_projection_unknown_plain_label_mapping_is_rejected(self):
        destination, result = self._render_edge_fixture('edge-unknown-label',
            'flowchart TD\n A ~~~|unknown| B')
        self.assertEqual('ERROR', result['display']['status'])
        receipt = json.loads((destination / 'diagram-001.projection.json').read_text(encoding='utf-8'))
        self.assertTrue(receipt['authorRevisionRequired'])
        self.assertIn('unparsed plain edge label', receipt['error'])
        self.assertFalse((destination / 'diagram-001.png').exists())

    def test_edge_projection_markdown_and_nonflow_baseline_unchanged(self):
        destination, result = self._render_edge_fixture('edge-markdown-baseline',
            'flowchart TD\n A -->|"`**Markdown** label`"| B')
        self.assertEqual('PASS', result['display']['status'], result['diagrams'])
        receipt = json.loads((destination / 'diagram-001.projection.json').read_text(encoding='utf-8'))
        self.assertFalse(receipt['applied'])
        self.assertEqual(1, receipt['excludedMarkdownBaselineLabels'])
        self.assertEqual(receipt['sourceSha256'], receipt['projectedSha256'])
        self.assertIn('MARKDOWN_BASELINE_DISPLAY_UNMODIFIED',
            [check['status'] for check in receipt['visibleLabelChecks']])
        self.assertEqual((destination / 'diagram-001.mmd').read_bytes(),
            (destination / 'diagram-001.view.mmd').read_bytes())
        for diagram in self.result['diagrams'][1:]:
            self.assertEqual('UNMODIFIED_NON_FLOW_DISPLAY', diagram['layoutProjection']['status'])
            self.assertFalse(diagram['layoutProjection']['applied'])

    def test_markdown_plain_collision_cannot_allow_unknown_native_label(self):
        destination, result = self._render_edge_fixture('edge-markdown-collision-reject',
            'flowchart TD\n A -->|"`Same text`"| B\n B -->|Same text| C\n C ~~~|unknown| D')
        self.assertEqual('ERROR', result['display']['status'])
        receipt = json.loads((destination / 'diagram-001.projection.json').read_text(encoding='utf-8'))
        self.assertTrue(receipt['authorRevisionRequired'])
        self.assertIn('unparsed plain edge label', receipt['error'])
        self.assertFalse((destination / 'diagram-001.png').exists())

    def test_dotted_thick_bidirectional_native_long_labels_keep_meaning(self):
        graph = ('flowchart LR\n'
                 ' A[入力] -. 条件ArgumentException発生 .-> B[判定]\n'
                 ' B == 条件InputValidationException発生 ==> C[結果]\n'
                 ' C <-- 値10001件 --> D[終了]\n'
                 ' D <== 条件ErrorCode発生 ==> E[参照]\n'
                 ' E <-. "値1.0の場合" .-> F[完了]')
        destination, result = self._render_edge_fixture('edge-dotted-thick-bidir', graph)
        self.assertEqual('PASS', result['display']['status'], result['diagrams'])
        receipt = json.loads((destination / 'diagram-001.projection.json').read_text(encoding='utf-8'))
        self.assertTrue(receipt['semanticSignatureEqual'])
        self.assertTrue(receipt['wholeVisibleTokensVerified'])
        forms = {label['form'] for label in receipt['labels']}
        self.assertTrue({'long-dotted', 'long-thick', 'long-solid'}.issubset(forms))
        tokens = [token for item in receipt['visibleLabelChecks'] for token in item.get('tokens', [])]
        for token in ['ArgumentException', 'InputValidationException', '10001', '1.0', 'ErrorCode']:
            self.assertIn(token, tokens)
        self.assertEqual([], result['display']['blockedRequests'])

    def test_dotted_ambiguous_quote_is_never_rendered_as_pass(self):
        destination, result = self._render_edge_fixture('edge-dotted-ambiguous',
            'flowchart TD\n A -. 条件"ArgumentException" .-> B')
        self.assertEqual('ERROR', result['display']['status'])
        self.assertIn('Mixed quoted', result['diagrams'][0]['error'])
        self.assertFalse((destination / 'diagram-001.png').exists())

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
        self.assertEqual("ERROR", result["diagrams"][0]["status"])
        self.assertEqual([], result["display"]["blockedRequests"])
        receipt = json.loads((self.run_root / "directive/diagram-001.projection.json").read_text(encoding="utf-8"))
        self.assertTrue(receipt['authorRevisionRequired'])
        self.assertIn('Unsupported node-label markup', receipt['error'])
        self.assertFalse((self.run_root / "directive/diagram-001.png").exists())
        svg = ET.fromstring((self.run_root / "directive/diagram-001.source.svg").read_text(encoding="utf-8"))
        self.assertFalse(any(key.lower().startswith("on") for element in svg.iter() for key in element.attrib))
        self.assertEqual(raw.encode('utf-8'), source.read_bytes())

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

    def _measure_markdown_table_css(self, name, markdown, atomic=(), *, baseline=False):
        """Trusted geometry queries in an inert browser; no application JavaScript."""
        from markdown_it import MarkdownIt
        from contextbase.ai.rendering import (_html, _playwright_runtime, _capture_document,
                                              MARKDOWN_TABLE_READABILITY_STYLE)
        destination = self.run_root/name
        destination.mkdir(exist_ok=False)
        source = destination/'fixture.md'
        source.write_bytes(markdown.encode('utf-8'))
        before = source.read_bytes()
        parser = MarkdownIt('commonmark', {'html': True}).enable('table')
        parser.renderer.rules['table_open'] = lambda tokens,index,options,env: _markdown_table_open(
            tokens,index,options,env,parser.renderer)
        document = _html(parser.render(markdown))
        if baseline:
            self.assertEqual(1, document.count(MARKDOWN_TABLE_READABILITY_STYLE))
            document = document.replace(MARKDOWN_TABLE_READABILITY_STYLE, '')
        (destination/'fixture.html').write_text(document, encoding='utf-8')
        blocked = []
        with _playwright_runtime(destination/'.runtime') as playwright:
            context = playwright.chromium.launch_persistent_context(
                str(destination/'.runtime/static'), executable_path=str(self.chromium), headless=True,
                java_script_enabled=False, viewport={'width':1440,'height':1000}, locale='ja-JP',
                service_workers='block')
            context.route('**/*', lambda route: (blocked.append(route.request.url), route.abort())[1])
            try:
                page = context.new_page()
                page.set_content(document, wait_until='load')
                state = page.evaluate(r'''({atomic}) => {
                    const box = r => ({x:r.x,y:r.y,width:r.width,height:r.height,right:r.right,bottom:r.bottom});
                    const tables = [...document.querySelectorAll('table')].map(table => {
                        const bounds = table.getBoundingClientRect();
                        return {html:table.outerHTML, columns:table.getAttribute('data-renderer-columns'),
                            layout:getComputedStyle(table).tableLayout, width:bounds.width,height:bounds.height,
                            cells:[...table.querySelectorAll('th,td')].map(cell => {
                                const rect = cell.getBoundingClientRect(), style = getComputedStyle(cell);
                                return {html:cell.innerHTML,text:cell.textContent,rowSpan:cell.rowSpan,colSpan:cell.colSpan,
                                    x:rect.x-bounds.x,y:rect.y-bounds.y,width:rect.width,height:rect.height,
                                    overflowWrap:style.overflowWrap,wordBreak:style.wordBreak,whiteSpace:style.whiteSpace};
                            })};
                    });
                    const tokens=[],overflows=[];
                    for (const cell of document.querySelectorAll('table[data-renderer-markdown] th,table[data-renderer-markdown] td')) {
                        const cb=cell.getBoundingClientRect(), walker=document.createTreeWalker(cell,NodeFilter.SHOW_TEXT);
                        let node;
                        while(node=walker.nextNode()) {
                            if(!node.textContent.trim())continue;
                            const range=document.createRange();range.selectNodeContents(node);
                            for(const rect of range.getClientRects()) if(rect.width>0 &&
                                (rect.x<cb.x-1 || rect.right>cb.right+1 || rect.y<cb.y-1 || rect.bottom>cb.bottom+1))
                                overflows.push({text:node.textContent,rect:box(rect),cell:box(cb)});
                            for(const token of atomic) {
                                let from=0,pos;
                                while((pos=node.textContent.indexOf(token,from))>=0) {
                                    const span=document.createRange();span.setStart(node,pos);span.setEnd(node,pos+token.length);
                                    const rects=[...span.getClientRects()].filter(rect=>rect.width>0);
                                    tokens.push({token,rows:[...new Set(rects.map(rect=>Math.round(rect.y*10)/10))],
                                        withinCell:rects.every(rect=>rect.x>=cb.x-1 && rect.right<=cb.right+1 &&
                                            rect.y>=cb.y-1 && rect.bottom<=cb.bottom+1)});
                                    from=pos+token.length;
                                }
                            }
                        }
                    }
                    return {tables,tokens,overflows,width:document.documentElement.scrollWidth,
                        height:document.documentElement.scrollHeight,
                        inlineCodeWhitespace:[...document.querySelectorAll('table[data-renderer-markdown] code')]
                            .map(code=>getComputedStyle(code).whiteSpace)};
                }''', {'atomic':list(atomic)})
                display = {}
                _capture_document(page, destination, display)
                state['capture'] = display
                state['blockedRequests'] = blocked
                (destination/'measurement.json').write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding='utf-8')
            finally:
                context.close()
        self.assertEqual(before, source.read_bytes())
        self.assertEqual([], blocked)
        return destination,state

    def test_table_css_keeps_nine_non_no_three_and_long_six_column_tokens_whole(self):
        def table(headers, rows):
            return '| '+' | '.join(headers)+' |\n|'+'|'.join(['---']*len(headers))+'|\n'+''.join(
                '| '+' | '.join(row)+' |\n' for row in rows)+'\n'
        atomic = ['sample_atomic_identifier_abcdefghijklmno', 'unique_synthetic_datatype',
                  'SYNTHETIC_CATEGORY_WITH_LONG_NAME', 'sample_parameter_identifier_abcdefghijklmnopqrstuvwxyz',
                  '123456789012345678901234567890123456789012345678901234567890', 'PLAIN-LEGAL-WRAP-TOKEN']
        text = table(['No','physical_id','logical','kind','size','required','default','source','description'],
            [['1','`'+atomic[0]+'`','合成項目',atomic[1],'1234567890','Y','NULL','FixtureOnly:1','日本語説明。'*20],
             ['2','`'+atomic[5]+'`','空欄例','text','','N','','FixtureOnly:2','明示改行<br>次の説明']])
        text += table(['分類ID','パラメータ','説明'], [[atomic[2],atomic[3],'自然な日本語の説明。'*20]])
        text += table(['分類ID','列A','列B','列C','列D','説明'],
                      [[atomic[2],atomic[0],atomic[1],atomic[4],'VALUE','長い日本語説明。'*20]])
        old_root,old = self._measure_markdown_table_css('table-css-baseline',text,atomic,baseline=True)
        root,state = self._measure_markdown_table_css('table-css-readable',text,atomic)
        self.assertEqual([t['html'] for t in old['tables']], [t['html'] for t in state['tables']])
        self.assertEqual(['9','3','6'], [t['columns'] for t in state['tables']])
        self.assertTrue(all(t['layout']=='auto' for t in state['tables']))
        self.assertEqual(set(atomic), {token['token'] for token in state['tokens']})
        self.assertTrue(all(len(token['rows'])==1 and token['withinCell'] for token in state['tokens']), state['tokens'])
        self.assertEqual([],state['overflows'])
        self.assertTrue(all(style=='nowrap' for style in state['inlineCodeWhitespace']))
        self.assertIn('明示改行<br>次の説明',state['tables'][0]['html'])
        self.assertTrue(any(len(token['rows'])>1 for token in old['tokens']), 'fixture must reproduce fixed-column wrapping')
        with Image.open(root/'document.png') as image:
            self.assertEqual((state['width'],state['height']),image.size)

    def test_table_css_one_two_column_and_embedded_geometry_and_pixels_are_unchanged(self):
        text = ('| 単独欄 |\n| --- |\n| `OneColumnStableIdentifier` |\n\n'
                '| 識別子 | 説明 |\n| --- | --- |\n| `TwoColumnStableIdentifier` | 二列の説明。 |\n\n'
                '<style>#embedded{width:480px;border:2px solid #345;padding:8px;font-size:15px}'
                '#embedded table{width:450px;border-collapse:collapse}#embedded td{border:1px solid #789;padding:4px}</style>'
                '<div id="embedded"><table><tr><td>固定欄</td><td>EmbeddedIdentifier</td><td>埋込み三列</td></tr></table>'
                '<input disabled value="fixture"></div>')
        old_root,old = self._measure_markdown_table_css('table-css-protected-baseline',text,baseline=True)
        root,state = self._measure_markdown_table_css('table-css-protected',text)
        self.assertEqual(['1','2',None],[t['columns'] for t in state['tables']])
        self.assertEqual(old['tables'],state['tables'])
        self.assertEqual(old['width'],state['width'])
        self.assertEqual(old['height'],state['height'])
        with Image.open(old_root/'document.png') as baseline, Image.open(root/'document.png') as current:
            self.assertEqual(baseline.convert('RGBA').tobytes(),current.convert('RGBA').tobytes())

    def test_table_css_preserves_authored_identifier_break_without_content_repair(self):
        text = '| 分類 | 値 | 説明 |\n| --- | --- | --- |\n| AuthoredAtomic<br>Token | 1 | 合成説明 |\n'
        _,state = self._measure_markdown_table_css('table-css-authored-break',text,['AuthoredAtomic','Token'])
        self.assertIn('AuthoredAtomic<br>Token',state['tables'][0]['html'])
        self.assertEqual(2,len({token['rows'][0] for token in state['tokens']}))
        self.assertNotIn('<span',state['tables'][0]['html'])

    def test_table_css_excessive_atomic_width_is_display_error_with_no_partial_png(self):
        source = self.run_root/'table-css-excessive.md'
        raw = fixture('| 分類 | 値 | 説明 |\n| --- | --- | --- |\n| '+('W'*2500)+' | Synthetic | 超長幅負例 |\n',
                      path=source.name).encode('utf-8')
        source.write_bytes(raw)
        destination = self.run_root/'table-css-excessive'
        result = render_document(source,destination,chromium_executable=self.chromium)
        self.assertEqual('PASS',result['structure']['status'])
        self.assertEqual('ERROR',result['display']['status'])
        self.assertTrue(any('capture bounds' in error for error in result['display']['errors']))
        self.assertEqual([],list(destination.glob('*.png')))
        self.assertEqual(raw,source.read_bytes())



if __name__ == "__main__":
    unittest.main()

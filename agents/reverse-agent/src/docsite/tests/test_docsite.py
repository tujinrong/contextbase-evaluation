from __future__ import annotations
import json, tempfile, unittest
from pathlib import Path
from bs4 import BeautifulSoup
from docsite.common import (embed_layout, scoped_css, insert_layout, fences, rewrite_links, check_html, write)
from docsite.publish import migrate, build, check, classify, prepare_markdown

LAYOUT='''<!doctype html><html><head><style>body{color:#123}main{padding:10px}input,select{width:100%}@media print{main{margin:0}}</style></head><body><main><h1>画面</h1><div data-item="customer" data-role="input"><label for="customer">顧客名</label><input id="customer"></div><div data-component="viewer">帳票表示領域</div></main></body></html>'''
MD='''# 機能の仕様書

## 1. システム概要

### 1.2 レイアウト

[HTML画面レイアウトを開く](画面レイアウトF-001_登録.html)

## 2. 項目一覧

|項目|役割|
|---|---|
|顧客名|入力|

## 3. イベント仕様

```mermaid
flowchart LR
  A[入力] --> B[登録]
```

```json
{"table": "customers", "url": "[例](original.md)"}
```

## 4. 補足説明

[共通](概要仕様書COM-001_共通仕様.md#共通仕様)
'''

class FragmentTests(unittest.TestCase):
    def test_embed_is_raw_html_and_not_full_document(self):
        block,keys=embed_layout(LAYOUT)
        self.assertEqual(keys,['customer']);self.assertIn('<div class="screen-layout"',block)
        self.assertNotIn('<html',block);self.assertNotIn('```html',block)
    def test_ids_and_labels_are_namespaced(self):
        block,_=embed_layout(LAYOUT)
        self.assertIn('id="screen-control-customer"',block);self.assertIn('for="screen-control-customer"',block)
    def test_css_scopes_media_and_document_selectors(self):
        css=scoped_css('body{color:red}@media print{main,input{margin:0}}')
        self.assertIn('.screen-layout{',css)
        self.assertIn('.screen-layout .layout-root,.screen-layout input',css)
        check_html('<style>'+css+'</style>')
    def test_global_css_rejected(self):
        with self.assertRaises(ValueError):check_html('<style>body{display:none}</style>')
    def test_script_rejected(self):
        with self.assertRaises(ValueError):check_html('<script>alert(1)</script>')
    def test_event_handler_rejected(self):
        with self.assertRaises(ValueError):check_html('<input onfocus="alert(1)">')
    def test_external_css_rejected(self):
        with self.assertRaises(ValueError):scoped_css('body{background:url(https://example.com/x)}')
    def test_json_and_diagram_definitions_unchanged(self):
        block,_=embed_layout(LAYOUT)
        self.assertEqual(fences(MD),fences(insert_layout(MD,block)))
    def test_embedded_layout_renders_as_controls(self):
        block,_=embed_layout(LAYOUT);text=insert_layout(MD,block)
        content,_=prepare_markdown(text);soup=BeautifulSoup(content,'html.parser')
        self.assertEqual(len(soup.select('.screen-layout input')),1)
        self.assertEqual(len(soup.find_all('table')),1);self.assertEqual(len(soup.select('svg.flowchart-svg')),1)
    def test_missing_layout_section_not_silently_appended(self):
        with self.assertRaises(ValueError):insert_layout('# Missing\n','<div>test</div>')
    def test_language_independent_categories(self):
        self.assertEqual(str(classify('概要仕様書JAVA-009_注文.md')), '基本設計書/概要仕様書JAVA-009_注文.md')
        self.assertEqual(str(classify('開発規約.md')), '共通/開発規約.md')
    def test_unsafe_url_rejected(self):
        with self.assertRaises(ValueError):check_html('<a href="javascript:alert(1)">危険</a>')
    def test_mermaid_html_escaped(self):
        content,_=prepare_markdown('```mermaid\nflowchart LR\nA["</pre><script>alert(1)</script>"]\n```\n')
        self.assertIsNone(BeautifulSoup(content,'html.parser').find('script'))
    def test_reference_links_and_inline_code(self):
        a=Path('/repo/output/a.md');b=Path('/repo/output/md/基本設計書/a.md');target=Path('/repo/output/md/共通/b.md')
        src='[共通][c]\n\n[c]: b.md\n\n`[例](b.md)`\n\n```text\n[例](b.md)\n```\n'
        out=rewrite_links(src,a,b,{Path('/repo/output/b.md'):(target,'')})
        self.assertIn('[c]: ../%E5%85%B1%E9%80%9A/b.md',out)
        self.assertIn('`[例](b.md)`',out);self.assertEqual(fences(src),fences(out))

class PublicationTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name);out=self.root/'output';out.mkdir()
        (out/'概要仕様書F-001_登録.md').write_text(MD,encoding='utf-8')
        (out/'概要仕様書COM-001_共通仕様.md').write_text('# 共通仕様\n\n共通の規則。\n',encoding='utf-8')
        (out/'画面レイアウトF-001_登録.html').write_text(LAYOUT,encoding='utf-8')
        (out/'機能一覧.md').write_text('# 機能一覧\n\n[仕様](概要仕様書F-001_登録.md)\n',encoding='utf-8')
    def test_md_is_the_only_build_input_after_migration(self):
        r=migrate(self.root,True);self.assertEqual(r['pruned'],4)
        self.assertFalse((self.root/'output/画面レイアウトF-001_登録.html').exists())
        result=build(self.root);self.assertEqual(result['html_documents'],3)
        self.assertEqual(check(self.root)['errors'],[])
    def test_common_links_become_html_and_keep_anchors(self):
        migrate(self.root);build(self.root)
        text=(self.root/'output/html/基本設計書/概要仕様書F-001_登録.html').read_text()
        self.assertIn('.html#%E5%85%B1%E9%80%9A%E4%BB%95%E6%A7%98',text)
        self.assertEqual(check(self.root)['errors'],[])
    def test_unchanged_build_preserves_mtime(self):
        migrate(self.root);build(self.root)
        paths=list((self.root/'output/html').rglob('*.html'));before={p:p.stat().st_mtime_ns for p in paths}
        result=build(self.root)
        self.assertEqual(result['written'],0);self.assertEqual(before,{p:p.stat().st_mtime_ns for p in paths})
    def test_user_md_edit_survives_unchanged_upstream(self):
        migrate(self.root);p=self.root/'output/md/基本設計書/概要仕様書F-001_登録.md'
        p.write_text(p.read_text()+'\n顧客が確認した内容。\n');migrate(self.root)
        self.assertIn('顧客が確認した内容',p.read_text())
    def test_conflicting_upstream_and_md_edit_are_protected(self):
        migrate(self.root)
        p=self.root/'output/md/基本設計書/概要仕様書F-001_登録.md';p.write_text(p.read_text()+'手修正')
        s=self.root/'output/概要仕様書F-001_登録.md';s.write_text(s.read_text()+'原本変更')
        with self.assertRaises(ValueError):migrate(self.root,True)
        self.assertTrue(s.exists());self.assertIn('手修正',p.read_text())
    def test_user_html_edit_is_not_overwritten(self):
        migrate(self.root);build(self.root)
        p=self.root/'output/html/基本設計書/概要仕様書F-001_登録.html';p.write_text('手修正')
        with self.assertRaises(ValueError):build(self.root)
        self.assertEqual(p.read_text(),'手修正')
    def test_missing_common_doc_is_detected(self):
        migrate(self.root);build(self.root)
        (self.root/'output/html/共通/概要仕様書COM-001_共通仕様.html').unlink()
        self.assertTrue(check(self.root)['errors'])
    def test_deleted_layout_item_is_detected(self):
        migrate(self.root);build(self.root)
        p=self.root/'output/html/基本設計書/概要仕様書F-001_登録.html'
        p.write_text(p.read_text().replace('data-item="customer"','data-broken="customer"'))
        self.assertIn('embedded_component_loss',{e['rule'] for e in check(self.root)['errors']})
    def test_removed_md_prunes_only_managed_html(self):
        migrate(self.root);build(self.root)
        p=self.root/'output/md/共通/概要仕様書COM-001_共通仕様.md';p.unlink()
        custom=self.root/'output/html/manual.txt';custom.write_text('手作業');build(self.root)
        self.assertFalse((self.root/'output/html/共通/概要仕様書COM-001_共通仕様.html').exists());self.assertTrue(custom.exists())
    def test_symlink_refused(self):
        migrate(self.root);p=self.root/'output/md/危険.md'
        try:p.symlink_to(self.root/'output/機能一覧.md')
        except OSError:self.skipTest('Symlink privilege unavailable')
        with self.assertRaises(ValueError):build(self.root)

if __name__=='__main__':unittest.main()

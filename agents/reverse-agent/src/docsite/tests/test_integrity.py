"""Regressions for publication continuity and visible-content loss."""
from pathlib import Path
import tempfile
import unittest
from bs4 import BeautifulSoup
from docsite.publish import migrate, build, check

class IntegrityTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        out=self.root/'output';out.mkdir();self.upstream=out/'共通.md'
        self.upstream.write_text('# 共通\n\n重要な業務説明。\n\n| 項目 | 値 |\n| --- | --- |\n| 保存 | 必須 |\n\n```json\n{"key":"value"}\n```\n',encoding='utf-8')
    def publish(self):
        migrate(self.root);build(self.root);return self.root/'output/html/共通/共通.html'
    def test_edit_survives_multiple_imports_then_conflicts(self):
        migrate(self.root)
        md=self.root/'output/md/共通/共通.md';md.write_text(md.read_text()+'\n承認した手修正。')
        migrate(self.root);migrate(self.root)
        self.upstream.write_text(self.upstream.read_text()+'\nソース側の新しい説明。')
        with self.assertRaises(ValueError):migrate(self.root,True)
        self.assertIn('手修正',md.read_text());self.assertTrue(self.upstream.exists())
    def test_machine_baseline_is_distinct_from_current_md(self):
        import json
        migrate(self.root);md=self.root/'output/md/共通/共通.md';md.write_text(md.read_text()+'手修正');migrate(self.root)
        row=json.loads((self.root/'.specgen-state/docsite/migration.json').read_text())['files']['共通.md']
        self.assertNotEqual(row['md_sha256'],row['generated_md_sha256'])
    def test_no_html_is_not_passed(self):
        migrate(self.root);self.assertNotEqual(check(self.root)['status'],'pass')
    def test_no_inputs_is_not_passed(self):
        self.assertIn('no_markdown_sources',{e['rule'] for e in check(self.root)['errors']})
    def test_missing_unlinked_page_is_detected(self):
        p=self.publish();p.unlink()
        self.assertIn('missing_html_page',{e['rule'] for e in check(self.root)['errors']})
    def test_missing_hash_meta_is_reported(self):
        p=self.publish();s=BeautifulSoup(p.read_text(),'html.parser');s.find('meta',attrs={'name':'docsite-source-sha256'}).decompose();p.write_text(str(s))
        self.assertIn('source_hash',{e['rule'] for e in check(self.root)['errors']})
    def test_missing_article_is_reported(self):
        p=self.publish();s=BeautifulSoup(p.read_text(),'html.parser');s.select_one('article.doc-body').decompose();p.write_text(str(s))
        self.assertIn('missing_article',{e['rule'] for e in check(self.root)['errors']})
    def test_visible_cell_edit_is_detected_with_same_counts(self):
        p=self.publish();p.write_text(p.read_text().replace('必須','不要'))
        self.assertIn('table_cell_changed',{e['rule'] for e in check(self.root)['errors']})
    def test_paragraph_loss_is_detected(self):
        p=self.publish();p.write_text(p.read_text().replace('重要な業務説明。',''))
        self.assertIn('visible_content_changed',{e['rule'] for e in check(self.root)['errors']})
    def test_code_edit_is_detected(self):
        p=self.publish();s=BeautifulSoup(p.read_text(),'html.parser');s.select_one('code.language-json').string='{"key":"changed"}\n';p.write_text(str(s))
        self.assertIn('code_example_changed',{e['rule'] for e in check(self.root)['errors']})
    def test_scripts_disabled_in_published_csp(self):
        p=self.publish();s=BeautifulSoup(p.read_text(),'html.parser')
        self.assertIn("script-src 'none'",s.find('meta',attrs={'http-equiv':'Content-Security-Policy'})['content'])

class BrowserReportTests(unittest.TestCase):
    def test_empty_report_cannot_pass(self):
        from docsite.ci import validate_browser_report
        with tempfile.TemporaryDirectory() as t:
            with self.assertRaises(ValueError):validate_browser_report(Path(t),{'status':'pass','results':[],'pages':0})
    def test_missing_page_cannot_pass(self):
        from docsite.ci import validate_browser_report
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);(root/'output/html').mkdir(parents=True);(root/'output/html/a.html').write_text('a')
            with self.assertRaises(ValueError):validate_browser_report(root,{'status':'pass','results':[],'pages':0})
    def test_stale_page_cannot_pass(self):
        from docsite.ci import validate_browser_report
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);(root/'output/html').mkdir(parents=True);(root/'output/html/a.html').write_text('a')
            with self.assertRaises(ValueError):validate_browser_report(root,{'status':'pass','results':[{'file':'output/html/a.html','html_sha256':'stale'}],'pages':1})

if __name__=='__main__':unittest.main()

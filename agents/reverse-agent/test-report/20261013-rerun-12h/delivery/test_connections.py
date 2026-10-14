"""Boundary/retention tests. No PDF/XLSX authoring or original files."""
import json
import tempfile
import unittest
from pathlib import Path
from delivery_model import canonical, sha, load_bound, parse_markdown, document_model, cell_height

def markdown(metadata,body):
    return '<!-- spec-meta: '+json.dumps(metadata,ensure_ascii=False)+' -->\n# 素材\n\n'+body

class ExtractionTests(unittest.TestCase):
    def test_table_single_sheet_and_literals(self):
        columns=['No','論理名','物理名','PK','NOT NULL','タイプ','長さ','初期値','説明']
        meta={'schema':'spec-md/1.1','documentId':'SYNTHETIC','path':'table.md','layout':'TABLE',
              'sheets':[{'sheet':'sample'}],'sections':[{'heading':'テーブルヘッダー','kind':'HEADER'},{'heading':'項目詳細','kind':'LIST'}],'columns':columns}
        text=markdown(meta,'## テーブルヘッダー\n\n| 属性 | 値 |\n| --- | --- |\n| 確認 | 001 |\n\n## 項目詳細\n\n| '+' | '.join(columns)+' |\n| '+' | '.join(['---']*9)+' |\n| 1 | 値 | sample | | | text | 3.10 | =A1 | 零<br>保持&#124;区切り |\n')
        entry={'documentId':'SYNTHETIC','canonicalDocumentPath':'table.md','rawMarkdown':text,'images':[],
               'markdown':'unused.md','markdownSha256':sha(text.encode()),'renderDirectory':'unused','renderPinsSha256':'0'*64,'renderManifestSha256':'0'*64}
        model=document_model(entry)
        self.assertEqual(len(model['sheets']),1)
        values=[op['value'] for op in model['sheets'][0]['operations']]
        for value in ['001','3.10','=A1','零\n保持|区切り']: self.assertIn(value,values)
        self.assertNotIn('‐',values)

    def test_explicit_grid_and_list_names_and_order(self):
        meta={'schema':'spec-md/1.0','documentId':'SYNTHETIC','path':'basic.md','sheets':[
            {'heading':'概要','kind':'GRID','sheet':'01_概要'},{'heading':'候補','kind':'LIST','sheet':'02_候補'}]}
        text=markdown(meta,'## 概要\n\n本文\n\n## 候補\n\n| ID | 値 |\n| --- | --- |\n| 001 | =literal |\n')
        entry={'documentId':'SYNTHETIC','canonicalDocumentPath':'basic.md','rawMarkdown':text,'images':[],
               'markdown':'unused.md','markdownSha256':sha(text.encode()),'renderDirectory':'unused','renderPinsSha256':'0'*64,'renderManifestSha256':'0'*64}
        model=document_model(entry)
        self.assertEqual([s['name'] for s in model['sheets']],['表紙','01_概要','02_候補'])
        self.assertEqual(model['sheets'][1]['columns'],120)
        self.assertEqual(model['sheets'][2]['operations'][0]['range'],'A1:A1')

    def test_table_preamble_is_preserved_before_header_on_same_sheet(self):
        columns=['No','論理名','物理名','PK','NOT NULL','タイプ','長さ','初期値','説明']
        meta={'schema':'spec-md/1.1','documentId':'SYNTHETIC','path':'table.md','layout':'TABLE',
              'sheets':[{'sheet':'sample'}],'sections':[{'heading':'テーブルヘッダー','kind':'HEADER'},{'heading':'項目詳細','kind':'LIST'}],'columns':columns}
        text=markdown(meta,'文書ID：SYNTHETIC  \n版：1.0\n\n## テーブルヘッダー\n\n| 属性 | 値 |\n| --- | --- |\n| 確認 | 001 |\n\n## 項目詳細\n\n| '+' | '.join(columns)+' |\n| '+' | '.join(['---']*9)+' |\n| 1 | 値 | sample | | | text | 3.10 | =A1 | 本文 |\n')
        entry={'documentId':'SYNTHETIC','canonicalDocumentPath':'table.md','rawMarkdown':text,'images':[],
               'markdown':'unused.md','markdownSha256':sha(text.encode()),'renderDirectory':'unused','renderPinsSha256':'0'*64,'renderManifestSha256':'0'*64}
        model=document_model(entry)
        self.assertEqual(len(model['sheets']),1)
        sheet=model['sheets'][0]
        self.assertEqual((sheet['name'],sheet['columns']),('sample',9))
        values=[op['value'] for op in sheet['operations']]
        self.assertEqual(values[1],'文書ID：SYNTHETIC\n版：1.0')
        self.assertLess(values.index('文書ID：SYNTHETIC\n版：1.0'),values.index('属性'))
        self.assertLess(values.index('属性'),values.index('No'))
        self.assertIn('001',values);self.assertIn('=A1',values)
        self.assertLess(values.index('テーブルヘッダー'),values.index('属性'))
        self.assertLess(values.index('項目詳細'),values.index('No'))

    def test_unpinned_mermaid_refused(self):
        meta={'schema':'spec-md/1.0','documentId':'S','sheets':[]}
        with self.assertRaisesRegex(ValueError,'same-line'):
            parse_markdown(markdown(meta,'## 概要\n\n```mermaid\nflowchart LR\nA-->B\n```\n'),[])

    def test_numbered_step_order_retained(self):
        meta={'schema':'spec-md/1.0','documentId':'S','sheets':[]}
        _,_,_,sections=parse_markdown(markdown(meta,'## 概要\n\n7. first\n8. second\n'),[])
        self.assertEqual([b['text'] for b in sections[0]['blocks']],['7. first','8. second'])

    def test_long_cell_readability_refused(self):
        with self.assertRaises(ValueError):cell_height('字'*4000,10)

    def test_path_traversal_refused(self):
        for value in ['../source.md','C:/source.md','a\\b.md','/root.md']:
            with self.subTest(value=value), self.assertRaises(ValueError): canonical(value)

class BindingTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(dir=Path(__file__).parent)
        self.root=Path(self.temp.name);mdroot=self.root/'md';renderroot=self.root/'render';mdroot.mkdir();renderroot.mkdir()
        md=mdroot/'sample.md';md.write_text('synthetic immutable bytes',encoding='utf-8')
        html=b'<!doctype html><html><body>synthetic</body></html>'
        (renderroot/'document.html').write_bytes(html);(renderroot/'sample.html').write_bytes(html)
        state={'sourceSha256':sha(md.read_bytes()),'structure':{'status':'PASS','findings':[]},
               'display':{'status':'PASS','blockedRequests':[],'errors':[]},'safety':{'removed':[],'inputJavaScriptEnabled':False},
               'layouts':[],'diagrams':[],'artifacts':[{'path':'document.html','sha256':sha(html),'bytes':len(html)}]}
        (renderroot/'manifest.json').write_text(json.dumps(state),encoding='utf-8')
        pins={**state,'documentId':'SYNTHETIC','canonicalDocumentPath':'sample.md','canonicalHtmlFilename':'sample.html',
              'canonicalHtmlSha256':sha(html),'sourceSnapshotManifestSha256':'1'*64}
        (renderroot/'render-pins.json').write_text(json.dumps(pins),encoding='utf-8')
        self.entry={'documentId':'SYNTHETIC','canonicalDocumentPath':'sample.md','markdown':str(md),'markdownSha256':sha(md.read_bytes()),
                    'renderDirectory':str(renderroot),'renderManifestSha256':sha((renderroot/'manifest.json').read_bytes()),'renderPinsSha256':sha((renderroot/'render-pins.json').read_bytes())}
        self.binding=self.root/'binding.json';self.write_binding([self.entry])
    def tearDown(self): self.temp.cleanup()
    def write_binding(self,rows):
        self.binding.write_text(json.dumps({'schema':'reverse-agent-delivery-binding/1','permittedMarkdownRoot':str(self.root/'md'),
            'permittedRenderRoot':str(self.root/'render'),'sourceSnapshotManifestSha256':'1'*64,'documents':rows}),encoding='utf-8')
    def test_valid_seal_read(self): self.assertEqual(len(load_bound(self.binding)[1]),1)
    def test_changed_markdown_rejected(self):
        Path(self.entry['markdown']).write_text('changed',encoding='utf-8')
        with self.assertRaisesRegex(ValueError,'Changed Markdown'):load_bound(self.binding)
    def test_changed_render_rejected(self):
        (self.root/'render'/'document.html').write_text('changed',encoding='utf-8')
        with self.assertRaisesRegex(ValueError,'artifact'):load_bound(self.binding)
    def test_duplicate_ids_rejected(self):
        self.write_binding([self.entry,self.entry])
        with self.assertRaisesRegex(ValueError,'Duplicate'):load_bound(self.binding)
    def test_wrong_source_snapshot_rejected(self):
        record=json.loads(self.binding.read_text());record['sourceSnapshotManifestSha256']='2'*64;self.binding.write_text(json.dumps(record))
        with self.assertRaisesRegex(ValueError,'snapshot'):load_bound(self.binding)

if __name__=='__main__':unittest.main()

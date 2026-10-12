import io
import json
from pathlib import Path
import tempfile
import unittest
import zipfile
from xml.etree import ElementTree as ET
from docsite.excel import build_excels, convert, safe
from docsite.excel_model import HEADERS, markdown_model, expected_values
from docsite.excel_package import package, verify, S


class ExcelTests(unittest.TestCase):
    def test_chapter_sheets_and_table(self):
        md='# 職員番号入力\n\n## 1. システム概要\n本文です。\n## 2. 項目一覧\n| '+' | '.join(HEADERS)+' |\n| '+' | '.join(['---']*10)+' |\n| 1 | 入力 | 番号 | TextBox | I | データ | ‐ | 必須 | 8桁 | 先頭ゼロを保持 |\n## 3. イベント仕様\nクリックする。'
        model=markdown_model(md,'基本設計書/F-0123.md')
        self.assertEqual(['表紙','概要','項目一覧','イベント仕様'],[s['name'] for s in model['sheets']])
        self.assertEqual(HEADERS,model['sheets'][2]['rows'][3]['values'])
        self.assertEqual('A3',model['sheets'][2]['paper'])
        result=verify(package(model),model)
        self.assertEqual('verified',result['status'])

    def test_literals_not_formulas(self):
        model=markdown_model('# test\n\n| 値 | 説明 |\n|---|---|\n|00123|=HYPERLINK("x")|\n|+123|@SUM(1)|\n|-11|日本語|','t.md')
        data=package(model);self.assertEqual(0,verify(data,model)['formulas'])
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            text=z.read('xl/worksheets/sheet2.xml').decode()
            self.assertIn('00123',text);self.assertIn('=HYPERLINK',text);self.assertNotIn('<f>',text)

    def test_escaped_pipe_br_code_and_lists(self):
        md='# test\n\n| 項目 | 内容 |\n|---|---|\n|A\\|B|x<br>y|\n\n```python\nx = 1\n```\n\n- abc\n- def'
        model=markdown_model(md,'t.md');values=' '.join(v for s in model['sheets'] for v in expected_values(s).values())
        self.assertIn('A|B',values);self.assertIn('x\ny',values);self.assertIn('x = 1',values);self.assertIn('・abc',values)

    def test_no_script_execution(self):
        m=markdown_model('# X\n\n<script>alert("secret")</script>\n\n<div>visible</div>','a.md')
        values=str(m);self.assertNotIn('secret',values);self.assertIn('visible',values)

    def test_unique_valid_sheet_names(self):
        md='# X\n' + ''.join('\n## '+name+'\ntext\n' for name in ['x'*80,'x'*80,'a/b:c*d?e[f]','概要','概要'])
        names=[s['name'] for s in markdown_model(md,'x.md')['sheets']]
        self.assertEqual(len(names),len(set(names)))
        self.assertTrue(all(len(n)<=31 for n in names));self.assertNotIn('/',names[3])

    def test_long_cell_continues_without_loss(self):
        value='あいうえお'*10000
        m=markdown_model('# X\n\n| Name | Text |\n|---|---|\n|A|'+value+'|','a.md')
        chunks=[v for s in m['sheets'] for v in expected_values(s).values() if 'あいう' in v]
        self.assertEqual(value,''.join(chunks).replace('\n',''))
        self.assertTrue(all(len(v)<=32767 for v in chunks));self.assertTrue(m['warnings'])
        self.assertEqual('verified',verify(package(m),m)['status'])

    def test_print_headers_filter_freeze(self):
        m=markdown_model('# X\n\n## 項目一覧\n|No|項目|\n|---|---|\n|1|abc|','x.md')
        with zipfile.ZipFile(io.BytesIO(package(m))) as z:
            wb=z.read('xl/workbook.xml').decode();sheet=z.read('xl/worksheets/sheet2.xml').decode()
            self.assertIn('_xlnm.Print_Titles',wb);self.assertIn('autoFilter',sheet)
            self.assertIn('state="frozen"',sheet);self.assertIn('fitToWidth="1"',sheet)

    def test_missing_image_preserves_reference_and_reports(self):
        m=markdown_model('# X\n\n![画面](assets/a.png)','x.md')
        self.assertTrue(m['warnings']);self.assertIn('assets/a.png',str(m['sheets']))

    def test_mermaid_preserved(self):
        m=markdown_model('# X\n\n```mermaid\nflowchart LR\nA-->B\n```','x.md')
        self.assertIn('A-->B',str(m['sheets']));self.assertTrue(m['warnings'])

    def test_tamper_detected(self):
        m=markdown_model('# X\ntext','x.md');data=package(m)
        m['sheets'][0]['rows'][0]['values'][0]='changed'
        with self.assertRaises(ValueError):verify(data,m)

    def test_deterministic_bytes(self):
        m=markdown_model('# X\n日本語','x.md');self.assertEqual(package(m),package(m))
        with zipfile.ZipFile(io.BytesIO(package(m))) as z:
            self.assertIn(b'<Types xmlns=',z.read('[Content_Types].xml'))
            self.assertIn(b'<Relationships xmlns=',z.read('_rels/.rels'))

    def test_build_and_reuse(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);p=root/'output/md/基本設計書/a.md';p.parent.mkdir(parents=True);p.write_text('# X\n\n## 項目一覧\nText')
            first=build_excels(root);second=build_excels(root)
            self.assertEqual(1,first['count']);self.assertTrue(second['documents'][0]['reused'])
            self.assertTrue((root/'output/Excel/基本設計書/a.xlsx').is_file())
            self.assertFalse((root/'output/Excel/manifest.json').exists())

    def test_failure_retains_existing_output(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);p=root/'output/md/a.md';p.parent.mkdir(parents=True);p.write_text('# Good')
            build_excels(root);out=root/'output/Excel/a.xlsx';original=out.read_bytes()
            p.write_text('# Changed');(root/'output/md/z.md').write_bytes(b'\xff')
            with self.assertRaises(ValueError):build_excels(root)
            self.assertEqual(original,out.read_bytes())
            self.assertFalse((root/'.contextbase-work/excel.lock').exists())

    def test_manual_excel_protected(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);p=root/'output/md/a.md';p.parent.mkdir(parents=True);p.write_text('# Good')
            out=root/'output/Excel';out.mkdir();(out/'manual.xlsx').write_bytes(b'manual')
            with self.assertRaises(ValueError):build_excels(root)
            self.assertEqual(b'manual',(out/'manual.xlsx').read_bytes())

    def test_path_escape(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            with self.assertRaises(ValueError):safe(root,root/'../other')
            (root/'link').symlink_to(root,target_is_directory=True)
            with self.assertRaises(ValueError):safe(root,root/'link/file')

    def test_single_conversion_cannot_replace_markdown(self):
        with tempfile.TemporaryDirectory() as d:
            md=Path(d)/'a.md';md.write_text('# Keep')
            with self.assertRaises(ValueError):convert(md,md)
            self.assertEqual('# Keep',md.read_text())

    def test_bom_and_single_conversion(self):
        with tempfile.TemporaryDirectory() as d:
            md=Path(d)/'a.md';out=Path(d)/'a.xlsx';md.write_text('# 日本語',encoding='utf-8-sig')
            self.assertEqual('verified',convert(md,out)['status']);self.assertTrue(out.read_bytes().startswith(b'PK'))

if __name__=='__main__':unittest.main()

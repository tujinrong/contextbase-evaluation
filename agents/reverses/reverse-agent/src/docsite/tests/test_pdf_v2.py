import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from docsite.pdf import OfflineFetcher, build_pdfs, safe_root


def create_document(root, name='確認', extra=''):
    md=root/'output/md'/f'{name}.md'
    page=root/'output/html'/f'{name}.html'
    md.parent.mkdir(parents=True,exist_ok=True)
    page.parent.mkdir(parents=True,exist_ok=True)
    md.write_text('# '+name+'\n',encoding='utf-8')
    digest=hashlib.sha256(md.read_bytes()).hexdigest()
    page.write_text('<html lang="ja"><head><meta charset="utf-8"><meta name="docsite-source-sha256" content="'+digest+'"></head><body><h1>'+name+'</h1><p>日本語表示とページ番号の確認。</p>'+extra+'</body></html>',encoding='utf-8')
    return md,page


@unittest.skipUnless(all(importlib.util.find_spec(name) for name in ("weasyprint", "bs4", "pypdf")), "Optional PDF dependencies are not installed")
class PDFTests(unittest.TestCase):
    def test_pdf_and_reuse(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);create_document(root)
            first=build_pdfs(root)
            self.assertEqual('verified',first['status'])
            self.assertEqual(1,first['count'])
            self.assertFalse(first['documents'][0]['reused'])
            second=build_pdfs(root)
            self.assertTrue(second['documents'][0]['reused'])
            self.assertEqual(first['documents'][0]['pdf_sha256'],second['documents'][0]['pdf_sha256'])

    def test_failure_does_not_replace_published_pdf(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);_,html=create_document(root)
            build_pdfs(root)
            before=(root/'output/PDF/確認.pdf').read_bytes()
            html.write_text(html.read_text()+'<img src="missing.png">',encoding='utf-8')
            with self.assertRaises(ValueError):build_pdfs(root)
            self.assertEqual(before,(root/'output/PDF/確認.pdf').read_bytes())
            self.assertEqual('failed',json.loads((root/'report/pdf/validation.json').read_text())['status'])

    def test_stale_html_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);md,_=create_document(root)
            md.write_text('# 変更後\n',encoding='utf-8')
            with self.assertRaisesRegex(ValueError,'does not match'):build_pdfs(root)
            self.assertFalse((root/'output/PDF').exists())

    def test_unmanaged_pdf_is_protected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);create_document(root)
            out=root/'output/PDF';out.mkdir()
            (out/'manual.pdf').write_bytes(b'Keep me')
            with self.assertRaisesRegex(ValueError,'unmanaged'):build_pdfs(root)
            self.assertEqual(b'Keep me',(out/'manual.pdf').read_bytes())

    def test_edited_generated_pdf_is_protected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);create_document(root);build_pdfs(root)
            p=root/'output/PDF/確認.pdf';p.write_bytes(b'edited')
            with self.assertRaisesRegex(ValueError,'unmanaged'):build_pdfs(root)
            self.assertEqual(b'edited',p.read_bytes())

    def test_network_is_not_requested(self):
        with tempfile.TemporaryDirectory() as tmp:
            fetcher=OfflineFetcher(Path(tmp))
            with patch('weasyprint.default_url_fetcher') as remote:
                with self.assertRaises(ValueError):fetcher('https://example.com/private')
                remote.assert_not_called()
            self.assertTrue(fetcher.errors)

    def test_escape_and_symlink_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            with self.assertRaises(ValueError):safe_root(root,root/'../secret')
            target=root/'target';target.mkdir()
            (root/'link').symlink_to(target,target_is_directory=True)
            with self.assertRaises(ValueError):safe_root(root,root/'link/asset.css')

    def test_missing_html_fails_without_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);_,page=create_document(root);page.unlink()
            with self.assertRaisesRegex(ValueError,'HTML is missing'):build_pdfs(root)

    def test_ten_column_table_landscape_and_text_coverage(self):
        headers=['No','グループ','項目名','種類','入出力','DB連携項目','候補取得元','必須','形式・桁','説明']
        values=['1','入力項目','職員番号','TextBox','I／O','未確認','‐','必須','最大8文字','職員番号を入力して確認する。']
        table='<table><thead><tr>'+''.join('<th>'+x+'</th>' for x in headers)+'</tr></thead><tbody><tr>'+''.join('<td>'+x+'</td>' for x in values)+'</tr></tbody></table>'
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);create_document(root,extra=table)
            result=build_pdfs(root)
            self.assertEqual('A4 landscape',result['documents'][0]['paper'])
            self.assertEqual(10,result['documents'][0]['checked_item_cells'])


    def test_cross_document_pdf_link_is_portable(self):
        from pypdf import PdfReader
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            create_document(root,name='一覧',extra='<a href="確認.html">対象を開く</a>')
            create_document(root,name='確認')
            build_pdfs(root)
            reader=PdfReader(root/'output/PDF/一覧.pdf')
            actions=[a.get_object().get('/A') for page in reader.pages for a in page.get('/Annots',[])]
            links=[a for a in actions if a and a.get('/S')=='/GoToR']
            self.assertEqual(1,len(links))
            self.assertEqual('確認.pdf',links[0]['/F'])
            self.assertNotIn(tmp,str(links))

    def test_multi_page_table_keeps_all_values(self):
        headers=['No','グループ','項目名','種類','入出力','DB連携項目','候補取得元','必須','形式・桁','説明']
        rows=[]
        for number in range(1,71):
            values=[str(number),'検証','項目番号'+str(number),'TextBox','I','未確認','‐','必須','8文字','検証値'+str(number)+'を照合する。']
            rows.append('<tr>'+''.join('<td>'+v+'</td>' for v in values)+'</tr>')
        table='<table><thead><tr>'+''.join('<th>'+h+'</th>' for h in headers)+'</tr></thead><tbody>'+''.join(rows)+'</tbody></table>'
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);create_document(root,extra=table)
            result=build_pdfs(root)
            doc=result['documents'][0]
            self.assertGreater(doc['pages'],1)
            self.assertEqual(700,doc['checked_item_cells'])


if __name__=='__main__':unittest.main()

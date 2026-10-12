import base64
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
import io
import zipfile
from docsite.v2.render_document_xlsx import markdown_model, fill_cover, parse_blocks, proportional_spans
from docsite.excel_package import package, verify
from docsite.excel_model import HEADERS, expected_values
from contextbase.pilot import load_pilot

ROOT=Path(__file__).resolve().parents[3]

class V2RendererTests(unittest.TestCase):
    def test_reference_cover_anchors(self):
        fixture=json.loads((ROOT/'src/docsite/v2/reference_format.json').read_text())
        m=markdown_model('# test\n\n## 表紙\n|項目|内容|\n|---|---|\n|画面名|test|\n## 概要\nhello','test.md')
        self.assertEqual(set(fixture['sheets']['表紙']['merges']),set(m['sheets'][0]['merges']))
        self.assertEqual('O6:AU36',m['sheets'][0]['print_area'])

    def test_print_area_is_absolute(self):
        m=markdown_model('# X\n\n## 概要\nhello','x.md')
        with zipfile.ZipFile(io.BytesIO(package(m))) as z:
            text=z.read('xl/workbook.xml').decode()
            self.assertIn("'表紙'!$O$6:$AU$36",text)

    def test_grid_header_anchors_and_five_sheet_order(self):
        text='# test\n'+''.join('\n## '+s+'\n本文\n' for s in ['概要','項目一覧','イベント仕様','補足説明'])
        m=markdown_model(text,'test.md')
        self.assertEqual(['表紙','概要','項目一覧','イベント仕様','補足説明'],[s['name'] for s in m['sheets']])
        self.assertIn('A1:J1',m['sheets'][1]['merges'])
        self.assertEqual(62,len(m['sheets'][1]['widths']))

    def test_generic_preface_does_not_duplicate_overview(self):
        m=markdown_model('# test\n\n前文\n\n## 1. システム概要\n説明','test.md')
        self.assertEqual(['表紙','概要'],[s['name'] for s in m['sheets']])
        self.assertIn('前文',str(m['sheets']))

    def test_sheet_names_case_insensitive(self):
        m=markdown_model('# X\n\n## Alpha\nA\n## alpha\nB','x.md')
        self.assertEqual(['表紙','Alpha','alpha_2'],[s['name'] for s in m['sheets']])

    def test_layout_math_conserves_columns(self):
        self.assertEqual([14,24,22],proportional_spans(60,[14,24,22]))
        self.assertEqual(60,sum(proportional_spans(60,[1,2,5,7,3,3])))

    def test_images_embedded_not_replaced_with_link(self):
        from PIL import Image
        with tempfile.TemporaryDirectory() as t:
            path=Path(t);Image.new('RGB',(20,10),'white').save(path/'screen.png')
            m=markdown_model('# X\n\n## 概要\n![画面](screen.png)','x.md',markdown_path=path/'x.md')
            result=verify(package(m),m)
            self.assertEqual(1,result['embedded_images'])
            damaged=copy.deepcopy(m);damaged['sheets'][1]['images'][0]['sha256']='wrong'
            with self.assertRaises(ValueError):verify(package(m),damaged)

    def test_image_missing_fails_instead_of_silent_omission(self):
        with tempfile.TemporaryDirectory() as t:
            with self.assertRaises(ValueError):markdown_model('# X\n\n![画面](no.png)','x.md',markdown_path=Path(t)/'x.md')

    def test_item_title_and_note_have_room(self):
        md='# X\n\n## 項目一覧\n| '+' | '.join(HEADERS)+' |\n| '+' | '.join(['---']*10)+' |\n| 1 | 入力 | 番号 | TextBox | I | ‐ | ‐ | 必須 | 8桁 | 説明 |\n\n項目定義数は1項目。'
        m=markdown_model(md,'x.md');s=m['sheets'][1]
        self.assertEqual(10,len(s['widths']));self.assertIn('A1:J1',s['merges'])
        self.assertEqual(HEADERS,s['rows'][1]['values']);self.assertEqual('A4',s['paper'])

    def test_literal_leading_equal_is_not_formula(self):
        m=markdown_model('# X\n\n## 概要\n=SUM(1)\n\n|No|値|\n|---|---|\n|1|00123|','x.md')
        self.assertEqual(0,verify(package(m),m)['formulas'])


class StaffPilotTests(unittest.TestCase):
    def test_source_change_prevents_stale_prose(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);d=root/'src-dynamic/jsbrms-pilot';d.mkdir(parents=True)
            source=root/'input/app/Staff.cshtml';source.parent.mkdir(parents=True);source.write_text('changed')
            (d/'pilot.json').write_text(json.dumps({'base':'app','source':'app/Staff.cshtml','checksums':{'Staff.cshtml':'wrong'}}))
            cfg,changed=load_pilot(root,'input');self.assertIsNone(cfg);self.assertEqual(['Staff.cshtml'],changed)

    def test_pilot_contract_covers_clear_errors_and_data(self):
        p=ROOT/'src-dynamic/jsbrms-pilot/職員番号入力.md'
        self.assertTrue(p.exists());text=p.read_text()
        for phrase in ['HTTP 204','職員番号・職員名・店番','既存のセッション職員情報は更新・削除しない','8時間','最大8文字','メニュー画面へ遷移する処理ではない','物理DBテーブルを参照・更新しない']:
            self.assertIn(phrase,text)
        self.assertIn('Q-PILOT-STYLE',text)
        self.assertNotIn('「ログアウトボタン」',text)

    def test_actual_pilot_sources_match_seal(self):
        if not (ROOT/'input/JSBRMS.Web/Pages/Staff.cshtml').exists():self.skipTest('Pilot input not in this checkout')
        cfg,changed=load_pilot(ROOT,'input')
        self.assertFalse(changed);self.assertEqual('100008',cfg['id'])
        self.assertEqual(11,len(cfg['checksums']))

    def test_source_branches_are_present_in_reviewed_input(self):
        p=ROOT/'input/JSBRMS.Web/Pages/Staff.cshtml.cs'
        if not p.exists():self.skipTest('Pilot input not in this checkout')
        source=p.read_text();clear=source.split('public IActionResult OnPostClear()')[1]
        self.assertIn('ModelState.Clear()',clear);self.assertIn('StaffNo = null',clear)
        self.assertIn('new NoContentResult()',clear);self.assertNotIn('RedirectToPage',clear)
        service=(ROOT/'input/JSBRMS.Web/Services/SampleStaffVerificationService.cs').read_text()
        self.assertIn('SampleStaffData.Staff',service);self.assertNotIn('SELECT ',service)

if __name__=='__main__':unittest.main()

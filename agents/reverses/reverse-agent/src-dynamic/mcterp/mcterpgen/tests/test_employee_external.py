from __future__ import annotations
import copy,tempfile,unittest
from pathlib import Path
from bs4 import BeautifulSoup
from contextbase.external_spec import layout_node,render,validate_contract
from mcterpgen.employee_layout import screens,condition,Adapter,PREFIX
from mcterpgen.employee_contract import fields,contract
from mcterpgen.employee_external import validate,generate

ROOT=Path(__file__).resolve().parents[4]
class EmployeeExternalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.screens,cls.trace,cls.columns=screens(ROOT,fields());cls.spec=contract(cls.screens,cls.columns);cls.text=render(cls.spec)
    def test_external_contract_complete(self):self.assertEqual(validate(ROOT,self.text,self.spec)['errors'],[])
    def test_modal_width_source(self):self.assertTrue(all(s['width']==1500 for s in self.screens[1:]))
    def test_six_groups_in_basic(self):
        h=BeautifulSoup(self.text,'html.parser').select_one('[data-screen="employee-edit-1"]')
        self.assertEqual([x.get_text() for x in h.select('h4')],['基本情報','連絡方法','教育、経験','対応フェーズ','管理情報','役割'])
    def test_fixed_table_order(self):
        self.assertEqual(len(self.columns),16);self.assertEqual([c['label'] for c in self.columns][:3],['社員番号','氏名','カタカナ'])
    def test_fixed_table_width(self):self.assertEqual([c['width'] for c in self.columns][:4],[100,150,200,200])
    def test_read_mode_buttons(self):
        h=BeautifulSoup(self.text,'html.parser').select_one('[data-screen="employee-view-3"]')
        self.assertEqual([b.get_text() for b in h.select('.ext-footer button')],['閉じる'])
    def test_new_mode_no_delete_reset(self):
        h=BeautifulSoup(self.text,'html.parser').select_one('[data-screen="employee-new-2"]')
        self.assertNotIn('削除',h.get_text());self.assertNotIn('パスワード初期化',h.get_text())
    def test_retirement_conditional(self):
        h=BeautifulSoup(self.text,'html.parser')
        self.assertFalse(h.select_one('[data-screen="employee-edit-1"] [data-field=quit_dt]'))
        self.assertIsNotNone(h.select_one('[data-screen="employee-edit-retired-4"] [data-field=quit_dt]'))
    def test_read_mode_basic_no_text_inputs(self):
        h=BeautifulSoup(self.text,'html.parser').select_one('[data-screen="employee-view-3"]')
        self.assertFalse(h.select('input:not([type=checkbox]),select'))
    def test_internal_item_row_mutation(self):
        bad=self.text.replace('| F1 | 社員番号 |','| F1 | 内部名 |')
        self.assertTrue(validate(ROOT,bad,self.spec)['errors'])
    def test_missing_event_output(self):
        bad=copy.deepcopy(self.spec);bad['events'][0]['output']=''
        with self.assertRaises(ValueError):render(bad)
    def test_implementation_detail_rejected(self):
        bad=copy.deepcopy(self.spec);bad['events'][0]['steps'][0]='SELECTで抽出する'
        with self.assertRaises(ValueError):render(bad)
    def test_width_mutation(self):
        bad=self.text.replace('data-width="1500"','data-width="800"',1)
        self.assertTrue(validate(ROOT,bad,self.spec)['errors'])
    def test_unknown_condition_stops(self):
        with self.assertRaises(ValueError):condition('external.run()',{'mode':'edit'})
    def test_other_project_layout_uses_same_renderer(self):
        node={'kind':'row','children':[{'kind':'col','span':12,'children':[{'kind':'field','id':'product','label':'商品名'}]},{'kind':'col','span':12,'children':[{'kind':'field','id':'stock','label':'在庫数','type':'number'}]}]}
        h=layout_node(node);self.assertIn('50.00000000%',h);self.assertNotIn('社員',h)
    def test_source_change_blocks_stale_contract(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):generate(Path(tmp))
    def test_embedded_layout_no_scripts(self):
        soup=BeautifulSoup(self.text,'html.parser');self.assertFalse(soup.find(['script','iframe','form']))
    def test_no_inactive_form(self):self.assertNotIn('noRight',self.text)
    def test_input_length_not_business_length(self):
        self.assertIn('入力上限6文字・有効値5桁数字',self.text);self.assertIn('入力上限13文字・有効値10～11桁数字',self.text)
    def test_clear_does_not_search(self):self.assertIn('その場では再検索しない',self.text)
    def test_csv_all_pages(self):self.assertIn('現在ページだけに限定しない',self.text)

if __name__=='__main__':unittest.main()

from __future__ import annotations
import tempfile,unittest,shutil,json
from pathlib import Path
from qualitygen.catalog import walk,quarantine_nested_keys
from qualitygen.pilot import generate_only
from qualitygen.profile import PILOT_CONTRACT,DB_CONTRACT
from qualitygen.__main__ import independent_review

class QualityTests(unittest.TestCase):
    def test_cycle_and_shortest_chain(self):
        self.assertEqual(walk({'A':['B','C'],'B':['C'],'C':['A','D']},'A')['D'],['A','C','D'])
    def test_unreachable_stays_absent(self):
        self.assertNotIn('C',walk({'A':['B'],'C':['B']},'A'))
    def test_subquery_keys_quarantined_not_discarded(self):
        mp={'object':'outer_table','column':'customer_id','direction':'key','path':'a.vb','method':'Save'}
        item={'key':'customer','binding':'CustomerId','db':[mp]}
        d={'methods':{'x':{'path':'a.vb','name':'Save','sql_fragments':[{'sql':'UPDATE outer_table SET x=1 WHERE EXISTS(SELECT * FROM inner_table WHERE customer_id=:p)'}]}},'features':[{'id':'A','items':[item]}]}
        result=quarantine_nested_keys(d)
        self.assertEqual(item['db'],[]);self.assertEqual(len(item['db_candidates']),1);self.assertEqual(len(result),1)
    def specs(self,path):
        payloads={'概要仕様書TKL-011_特別出版注文入力.md':PILOT_CONTRACT,'DB定義書.md':DB_CONTRACT,'概要仕様書COM-001_共通仕様.md':{'money':PILOT_CONTRACT['money'],'price_lookup':PILOT_CONTRACT['price_lookup']},'概要仕様書COM-002_共通関数仕様.md':{'functions':['discount','unit_price','price_lookup','transaction_contract'],'failure_state':'unchanged'},'開発規約.md':{'language':'VB.NET','option_strict':True,'database_access':'evaluation_mock_only'}}
        for name,data in payloads.items():(path/name).write_text('```json\n'+json.dumps(data)+'\n```',encoding='utf-8')
    def test_spec_only_generation_without_application_source(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);self.specs(root)
            m=generate_only(root,root/'generated',Path(__file__).parents[1]/'templates')
            self.assertEqual(m['source_access'],'none');self.assertEqual(len(m['inputs']),5)
            self.assertNotIn('@ORDER_TABLE@',(root/'generated/Rebuilt.vb').read_text())
    def test_common_individual_conflict_blocks_generation(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);self.specs(root);p=root/'概要仕様書COM-001_共通仕様.md'
            p.write_text(p.read_text().replace('to_even','away_from_zero'))
            with self.assertRaises(ValueError):generate_only(root,root/'generated',Path(__file__).parents[1]/'templates')
    def test_missing_standard_blocks_generation(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);self.specs(root);(root/'開発規約.md').unlink()
            with self.assertRaises(FileNotFoundError):generate_only(root,root/'generated',Path(__file__).parents[1]/'templates')
    def test_changed_bound_changes_generated_code(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);self.specs(root);p=root/'概要仕様書TKL-011_特別出版注文入力.md'
            p.write_text(p.read_text().replace('999','998'))
            generate_only(root,root/'generated',Path(__file__).parents[1]/'templates')
            self.assertIn('high = 998',(root/'generated/Rebuilt.vb').read_text())
    def review_fixture(self,root):
        (root/'input').mkdir();(root/'output').mkdir()
        (root/'input/a.xaml').write_text('<Window xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml"><Button x:Name="go"/><TextBox x:Name="text" IsReadOnly="True"/></Window>')
        s='\n'.join('## '+x for x in ['1. システム概要','2. 項目一覧','3. イベント仕様','4. 補足説明'])+'\n合計：2項目\n<!-- item:go order:1 role:operation -->\n<!-- item:text order:2 role:display -->'
        (root/'output/a.md').write_text(s);(root/'output/a.html').write_text('<div data-item="go"></div><div data-item="text"></div>')
        data={'features':[{'id':'A','name':'見本','source':'input/a.xaml','filename':'a.md','events':[],'db':[]}]}
        return data,[{'html':'a.html'}],{'objects':{},'scope':{}}
    def test_independent_item_role_mutation(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);args=self.review_fixture(root);p=root/'output/a.md';p.write_text(p.read_text().replace('role:operation','role:input'))
            self.assertIn('ITEM_ROLE',{x['rule'] for x in independent_review(root,*args)['automatic_errors']})
    def test_independent_html_item_mutation(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);args=self.review_fixture(root);(root/'output/a.html').write_text('<div data-item="go"></div>')
            self.assertIn('HTML_ITEMS',{x['rule'] for x in independent_review(root,*args)['automatic_errors']})
    def test_independent_total_mutation(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);args=self.review_fixture(root);p=root/'output/a.md';p.write_text(p.read_text().replace('合計：2','合計：3'))
            self.assertIn('ITEM_TOTAL',{x['rule'] for x in independent_review(root,*args)['automatic_errors']})
    def test_native_absence_cannot_pass(self):
        from qualitygen.pilot import finalize
        with tempfile.TemporaryDirectory() as t:
            with self.assertRaises(ValueError):finalize(Path(t))

if __name__=='__main__':unittest.main()

from __future__ import annotations
import copy
import tempfile
import unittest
from pathlib import Path
from overviewgen.adapters import clean_vb,logical_lines,sql_info,vb,xaml
from overviewgen.core import collect,fields,resolve_style
from overviewgen.publish import publish
from overviewgen.review import inspect_feature

XAML='''<Window xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation" xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml" x:Class="ExampleWindow" Title="見本検索"><Grid><TextBox x:Name="txtId" Text="{Binding Id}" MaxLength="6"/><TextBox x:Name="txtName" Text="{Binding Name}" IsReadOnly="True"/><Button x:Name="btnSearch" Content="検索"/></Grid></Window>'''
VB='''Public Class ExampleWindow
Private Sub btnSearch_Click(sender As Object, e As EventArgs) Handles btnSearch.Click
Dim sbSql = New StringBuilder()
sbSql.AppendLine("SELECT name FROM m101_customer WHERE id = :id")
End Sub
End Class
'''

class AdapterTests(unittest.TestCase):
    def test_comment_in_string(self):self.assertEqual(clean_vb('x = "it\'s" \' comment'),'x = "it\'s" ')
    def test_multiline_signature(self):
        out=vb('Public Class X\nPrivate Sub f(a As Integer,\n b As Integer) Handles Me.Loaded\nEnd Sub\nEnd Class','x.vb')
        self.assertIn('Me.Loaded',out['methods'][0]['handles'])
    def test_sql_read_and_write(self):
        out=sql_info('INSERT INTO sales(id) VALUES(1); SELECT id FROM sales; UPDATE sales SET id=2; DELETE FROM sales;',[(0,1)])
        self.assertEqual({x['operation'] for x in out['db']},{'C','R','U','D'})
        self.assertIn('id',{x['column'] for x in out['columns']})
    def test_truncate_and_copy_not_lost(self):
        out=sql_info("TRUNCATE TABLE m900_postal_all; COPY m900_postal_all FROM '/tmp/file.csv' WITH CSV;",[(0,1)])
        self.assertTrue({'TRUNCATE','COPY'} <= {x['operation'] for x in out['db']})
    def test_sql_literals_do_not_make_tables(self):
        out=sql_info("SELECT 'FROM fake' FROM real_table",[(0,1)])
        self.assertEqual({x['object'] for x in out['db']},{'real_table'})
    def test_dtd_rejected(self):
        with self.assertRaises(ValueError):xaml('<!DOCTYPE test><Window/>','x.xaml')
    def test_role_and_length(self):
        out=fields(xaml(XAML,'input/X.xaml'),{'methods':[]},[],{})
        by={x['key']:x for x in out}
        self.assertEqual(by['txtName']['role'],'display')
        self.assertEqual(by['txtName']['required'],'対象外')
        self.assertEqual(by['btnSearch']['role'],'operation')
        self.assertEqual(by['btnSearch']['length'],'対象外')
    def test_style_readonly(self):
        s={'ro':{'values':{'IsReadOnly':'True'},'base':'','handlers':[],'path':'styles.xaml','line':1}}
        self.assertEqual(resolve_style({'Style':'{StaticResource ro}'},s)[0]['IsReadOnly'],'True')

class PipelineTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
        p=self.root/'input/other_structure';p.mkdir(parents=True)
        (p/'Example.xaml').write_text(XAML,encoding='utf-8');(p/'Example.xaml.vb').write_text(VB,encoding='utf-8')
    def test_cold_warm_same_content(self):
        cold=collect(self.root);publish(self.root,cold)
        warm=collect(self.root);publish(self.root,warm)
        self.assertEqual(cold['stats']['parsed'],2);self.assertEqual(warm['stats']['parsed'],0);self.assertEqual(warm['stats']['cache_hits'],2)
        self.assertEqual(cold['features'],warm['features'])
    def test_stable_ids_after_new_file(self):
        first=collect(self.root)['features'][0]['id']
        (self.root/'input/a.py').write_text('def example():\n    return 1\n',encoding='utf-8')
        self.assertEqual(collect(self.root)['features'][0]['id'],first)
    def test_source_not_executed(self):
        target=self.root/'must_not_exist'
        (self.root/'input/a.py').write_text('from pathlib import Path\nPath('+repr(str(target))+').touch()\n',encoding='utf-8')
        collect(self.root);self.assertFalse(target.exists())
    def fixture(self):
        data=collect(self.root);publish(self.root,data);return data['features'][0]
    def test_mutation_missing_item_is_detected(self):
        f=self.fixture();f['items'].pop()
        self.assertIn('ITEM-COUNT',{x['rule'] for x in inspect_feature(self.root,f)})
    def test_mutation_button_input_is_detected(self):
        f=self.fixture();next(x for x in f['items'] if x['key']=='btnSearch')['role']='input'
        self.assertIn('ITEM-ROLE',{x['rule'] for x in inspect_feature(self.root,f)})
    def test_mutation_missing_db_is_detected(self):
        f=self.fixture();f['db']=[]
        self.assertIn('DB-OMISSION',{x['rule'] for x in inspect_feature(self.root,f)})
    def test_mutation_missing_event_is_detected(self):
        f=self.fixture();f['events']=[]
        self.assertIn('EVENT-OMISSION',{x['rule'] for x in inspect_feature(self.root,f)})
    def test_mutation_wrong_total_is_detected(self):
        f=self.fixture();path=self.root/'output'/f['filename'];path.write_text(path.read_text(encoding='utf-8').replace('合計：3項目','合計：99項目'),encoding='utf-8')
        self.assertIn('DOC-COUNT',{x['rule'] for x in inspect_feature(self.root,f)})
    def test_mutation_order_is_detected(self):
        f=self.fixture();f['items'][0]['order']=99
        self.assertIn('ITEM-ORDER',{x['rule'] for x in inspect_feature(self.root,f)})
    def test_unknown_schema_does_not_pass(self):
        f=self.fixture();findings=inspect_feature(self.root,f)
        self.assertIn('IMPLEMENT-SCHEMA',{x['rule'] for x in findings})

if __name__=='__main__':unittest.main()

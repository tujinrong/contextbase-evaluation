from __future__ import annotations
import json
import tempfile
import unittest
from pathlib import Path
from overviewgen.adapters import vb
from overviewgen.refine import source_calls,preflight,refine
from overviewgen.dblineage import placeholder_properties,query_bindings,enrich
from overviewgen.core import collect
from overviewgen.delivery import publish
from overviewgen.review import run_review
from overviewgen.customer import expression

class RefinementTests(unittest.TestCase):
    def test_callback_registration_is_not_execution(self):
        calls,deferred=source_calls({'statements':[{'text':'InitControlChanged(btnExec, AddressOf _UpdateData, controls)'}]})
        self.assertIn('_UpdateData',deferred);self.assertNotIn('_UpdateData',calls)
    def test_sql_text_does_not_create_application_calls(self):
        calls,_=source_calls({'statements':[{'text':'sbSql.AppendLine("SELECT func_abc() FROM data")'}]})
        self.assertNotIn('func_abc',calls)
    def test_all_parameters_in_initializer_are_mapped(self):
        m={'line':1,'statements':[{'text':'Dim ps = New List(Of NpgsqlParameter) From { MyNpg.SqlParameter("prID", _Model.Id), MyNpg.SqlParameter("prNAME", MyApp.NullToString(_Model.Name)) }'}]}
        result=placeholder_properties(m)
        self.assertEqual(result['prid'],{'Id'});self.assertEqual(result['prname'],{'Name'})
    def test_insert_nested_functions_and_keys(self):
        m={'line':1,'statements':[{'text':'MyNpg.SqlParameter("prID", _Model.Id)'},{'text':'MyNpg.SqlParameter("prNAME", _Model.Name)'}],'sql_fragments':[{'sql':'INSERT INTO customers (id,name,updated) VALUES (:prID,:prNAME,NOW()); UPDATE customers SET name=:prNAME WHERE id=:prID;'}]}
        result=query_bindings(m)
        pairs={(x['property'],x['column'],x['direction']) for x in result}
        self.assertIn(('Id','id','write'),pairs);self.assertIn(('Name','name','write'),pairs);self.assertIn(('Id','id','key'),pairs)
    def test_source_identifier_not_mistranslated(self):
        self.assertIsNone(expression('sUnknown > iLimit',{}))
        self.assertEqual(expression('Count > 0',{'Count':'件数'}),'件数 > 0')
    def test_first_run_has_real_review_target(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);p=root/'input/moved';p.mkdir(parents=True)
            (p/'Example.xaml').write_text('<Window xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation" xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml" x:Class="ExampleWindow" Title="見本"><Grid><TextBox x:Name="input"/><Button x:Name="btnSearch" Content="検索"/></Grid></Window>',encoding='utf-8')
            (p/'Example.xaml.vb').write_text('Public Class ExampleWindow\nPrivate Sub btnSearch_Click(sender As Object,e As EventArgs) Handles btnSearch.Click\nDim sbSql = New StringBuilder()\nsbSql.AppendLine("SELECT name FROM m101_customer")\nEnd Sub\nEnd Class\n',encoding='utf-8')
            preflight(root);data=collect(root);refine(root,data);enrich(data);publish(root,data)
            result=run_review(root,data)
            self.assertEqual(result['broken_links'],0)
            self.assertEqual(result['automatic_errors'],0)
            self.assertEqual(result['status'],'review_required')

if __name__=='__main__':unittest.main()

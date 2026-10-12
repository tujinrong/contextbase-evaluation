"""Independent fixture expectations for consolidated definitions and real DB binding."""
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest

from contextbase.detail.database import collect, database_documents
from contextbase.detail.bindings import BindingIndex, select_columns
from contextbase.detail.event_templates import er_model, flow_model, Narrator
from contextbase.validation.quality import consolidated_table_entries
from bs4 import BeautifulSoup
from markdown_it import MarkdownIt


def database():
    return {'tables':[{'name':'Ledger','logical_name':{'value':'台帳'},'origin':'ddl',
                       'columns':[{'name':name,'logical_name':{'value':jp},'status':'declared',
                                   'variants':[{'type':'VARCHAR(30)','nullable':'NULL','primary_key':name=='record_key'}]}
                                  for name,jp in [('record_key','記録番号'),('status_no','状態'),('full_name','氏名')]],
                       'definitions':[{'path':'schema.sql','line':1}]}], 'data_objects':[],'objects':[]}

MODEL='''public class Entry {
 public String getReference(){return null;}
 public String getCaption(){return null;}
 public void setReference(String x){}
 public void setCaption(String x){}
}'''
SOURCE='''public class Repo {
 public void save(Connection db, Entry form) throws Exception {
  PreparedStatement s = db.prepareStatement("INSERT INTO Ledger (record_key, status_no, full_name) VALUES (?, 7, ?)");
  bind(s, form);
  s.executeUpdate();
 }
 private void bind(PreparedStatement stmt, Entry dto) throws Exception {
  stmt.setString(1, dto.getReference());
  stmt.setString(2, dto.getCaption());
 }
 public Entry load(Connection db) throws Exception {
  PreparedStatement s = db.prepareStatement("SELECT L.record_key AS K, L.full_name AS NM FROM Ledger L");
  ResultSet rs = s.executeQuery();
  return map(rs);
 }
 private Entry map(ResultSet rs) throws Exception {
  Entry v = new Entry();
  v.setReference(rs.getString("K"));
  v.setCaption(rs.getString("NM"));
  return v;
 }
}'''
REQUEST='''public class Read {
 public Entry input(HttpServletRequest request){
  Entry form = new Entry();
  form.setReference(request.getParameter("ORDER_REF"));
  form.setCaption(request.getParameter("DISPLAY"));
  return form;
 }
}'''


def setup_binding(repo=SOURCE,request=REQUEST):
    sources={'Entry.java':MODEL,'Repo.java':repo,'Read.java':request,
             'screen.jsp':'<% Entry model = bean.getEntry(); %><input name="ORDER_REF" value="<%= model.getReference() %>">'}
    ops=collect(sources);index=BindingIndex(sources,ops,database())
    feature={'id':'SCR-009','source':'screen.jsp','dependencies':list(sources),'sql_operations':ops,
             'items':[{'id':'item1','number':1,'name':'記録番号','binding':'ORDER_REF','io':'I／O','db':'未確認','description':'記録番号を入力する。','facts':{}}]}
    return index,feature


class BindingTests(unittest.TestCase):
    def test_model_property_reaches_differently_named_column(self):
        index,f=setup_binding();index.apply(f)
        links=f['items'][0]['db_bindings']
        self.assertTrue(any(x['column']=='record_key' and x['direction']=='write' for x in links))
        self.assertIn('台帳・記録番号',f['items'][0]['db'])
        self.assertNotIn('Entry.reference',f['items'][0]['db'])
        self.assertIn('Entry.reference',f['items'][0]['binding_remarks'])

    def test_literal_value_does_not_shift_jdbc_positions(self):
        index,f=setup_binding()
        q=next(q for q in f['sql_operations'] if q['operation']=='C')
        self.assertEqual([('record_key',1),('full_name',2)],[(b['column'],b['position']) for b in q['parameter_bindings']])

    def test_select_alias_is_connected_through_called_mapper(self):
        index,f=setup_binding();index.apply(f)
        self.assertTrue(any(x['direction']=='read' and x['select_alias']=='K' and x['column']=='record_key' for x in f['items'][0]['db_bindings']))

    def test_unused_mapper_in_same_file_is_not_a_binding(self):
        index,f=setup_binding(SOURCE.replace('return map(rs);','return null;'));index.apply(f)
        self.assertFalse(any(x['direction']=='read' for x in f['items'][0]['db_bindings']))

    def test_name_similarity_without_source_edges_is_unresolved(self):
        index,f=setup_binding();f['items'][0]['binding']='record_key';index.apply(f)
        self.assertEqual([],f['items'][0]['db_bindings'])
        self.assertIn('確定できていない',f['items'][0]['binding_remarks'])

    def test_other_model_type_does_not_join_same_property(self):
        index,f=setup_binding(request=REQUEST.replace('Entry','Other'))
        f['source']='plain.html';index.apply(f)
        self.assertEqual([],f['items'][0]['db_bindings'])

    def test_ambiguous_parameter_assignment_not_claimed(self):
        src=SOURCE.replace('stmt.setString(1, dto.getReference());','stmt.setString(1, dto.getReference());\n  stmt.setString(1, dto.getCaption());')
        index,f=setup_binding(src);index.apply(f)
        self.assertFalse(any(x['direction']=='write' for x in f['items'][0]['db_bindings']))
        self.assertTrue(index.unresolved)

    def test_join_read_column_is_not_write_column(self):
        refs=select_columns('SELECT C.label AS STATUS, L.status_no AS CODE FROM Ledger L LEFT JOIN Codes C ON C.id=L.status_no')
        self.assertEqual('Codes',refs['STATUS'][0]['table'])
        self.assertEqual('status_no',refs['CODE'][0]['column'])

    def test_unknown_physical_column_is_not_published(self):
        index,f=setup_binding(SOURCE.replace('record_key','missing_column'));index.apply(f)
        self.assertEqual([],f['items'][0]['db_bindings'])

    def test_snapshot_write_not_listed_as_direct_input_write(self):
        src=SOURCE.replace(' public Entry load(',''' public void copyExisting(Connection db) throws Exception {
  Entry oldValue = load(db);
  if (oldValue == null) { return; }
  save(db, oldValue);
 }
 public Entry load(''')
        index,f=setup_binding(src);index.apply(f)
        self.assertTrue(any(e.get('input_role')=='database_snapshot' for e in f['items'][0]['db_bindings']))
        self.assertNotIn('保存：',f['items'][0]['db'])
        self.assertIn('画面入力の直接保存ではない',f['items'][0]['binding_remarks'])

    def test_idempotent_enrichment_preserves_description(self):
        index,f=setup_binding();index.apply(f);before=deepcopy(f['items'])
        index.apply(f);self.assertEqual(before,f['items'])


class TemplateTests(unittest.TestCase):
    def test_all_tables_one_md_with_scoped_ids(self):
        db=database();second=deepcopy(db['tables'][0]);second.update(name='Other',logical_name={'value':'その他'})
        db['tables'].append(second)
        docs=database_documents(db,[])
        self.assertEqual(1,len(docs));self.assertEqual('共通/DB仕様書/テーブル定義書.md',docs[0]['path'])
        self.assertEqual(2,len(docs[0]['db_tables']))
        self.assertEqual(3,len(docs[0]['model']['sections']))

    def test_false_nullable_is_not_treated_as_missing(self):
        db=database();db['tables'][0]['columns'][0]['variants'][0]['nullable']=False
        d=database_documents(db,[])[0]
        self.assertIn('NULL不可',str(d))

    def test_empty_database_does_not_invent_tables(self):
        db=database();db['tables']=[]
        d=database_documents(db,[])[0]
        self.assertEqual([],d['db_tables']);self.assertIn('検出していない',str(d))

    def test_er_does_not_invent_fk_or_multiplicity(self):
        ops=collect({'Repo.java':SOURCE})
        er=er_model(ops,database())
        self.assertEqual(1,len(er['entities']));self.assertEqual([],er['relationships'])
        self.assertEqual('Ledger',er['entities'][0]['table'])

    def test_join_is_annotated_as_query_not_declared_fk(self):
        db=database();db['tables'].append({'name':'Codes','logical_name':{'value':'状態区分'},'columns':[
            {'name':'id','logical_name':{'value':'区分番号'},'variants':[]},{'name':'label','logical_name':{'value':'区分名'},'variants':[]}]})
        q={'id':'SQL-1','operation':'R','table':'Ledger','columns':[], 'sql':'SELECT C.label AS STATUS FROM Ledger L JOIN Codes C ON C.id=L.status_no'}
        er=er_model([q],db);self.assertEqual(1,len(er['relationships']))
        self.assertEqual('sql_join',er['relationships'][0]['kind']);self.assertEqual('未確定',er['relationships'][0]['cardinality'])

    def test_flow_early_return_has_end_not_next_write(self):
        event={'id':'EV1','name':'登録','methods':[{'steps':[], 'flow':[
            {'kind':'if','condition':'error != null','line':1,'body':[{'kind':'return','value':'null','line':2}],'else':[]},
            {'kind':'call','expression':'repo.save(model)','line':3,'calls':[{'name':'repo.save','arguments':'model'}]}]}]}
        model={'name':'対象','dependencies':[],'items':[]};n=Narrator(model,event,{})
        flow=flow_model(n,event);nodes={x['id']:x for x in flow['nodes']}
        ret=next(x['id'] for x in flow['nodes'] if '戻り先画面' in x['text'])
        targets=[nodes[b]['text'] for a,b,l in flow['edges'] if a==ret]
        self.assertEqual(['終了'],targets)
        self.assertTrue(any(x['shape']=='diamond' for x in flow['nodes']))

    def test_unknown_condition_retains_raw_evidence_not_false_translation(self):
        e={'name':'操作','methods':[]};n=Narrator({'items':[],'dependencies':[]},e,{})
        value=n.condition('magicFlag')
        self.assertIn('条件',value);self.assertEqual('magicFlag',n.notes[0]['expression'])

    def test_crlf_inside_table_cell_cannot_create_extra_rows(self):
        from contextbase.specification.core import render
        model={'title':'確認','sections':[{'title':'備考','blocks':[{'kind':'table','value':[['No','項目名','備考'],['1','性別','変換(\r\n code, value)']]}]}]}
        md=render(model);soup=BeautifulSoup(MarkdownIt('commonmark',{'html':True}).enable('table').render(md),'html.parser')
        self.assertEqual(2,len(soup.find_all('tr')))
        self.assertEqual('性別',soup.find_all('tr')[1].find_all('td')[1].get_text())
        self.assertNotIn('\r',md)

    def test_route_constant_alias_is_resolved_without_source_execution(self):
        sources={'Base.java':'class Base { static final String LOGIN_JSP="./JSP/Login.jsp"; static final String STAFF_JSP=LOGIN_JSP; }'}
        n=Narrator({'items':[],'dependencies':['Base.java']},{'name':'登録','methods':[]},sources,{'app/JSP/Login.jsp':'ログイン画面'})
        self.assertEqual('ログイン画面へ表示を戻す',n.statement({'kind':'return','value':'STAFF_JSP'}))

    def test_consolidated_section_is_not_fulfilled_by_overview(self):
        md='# テーブル定義書\n\n## 一覧\nLedgerの定義はこちら\n\n## TBL-001 台帳\n|情報|内容|\n|---|---|\n|物理名|WrongTable|\n'
        d={'db_tables':[{'table':'Ledger','section':'TBL-001 台帳'}]}
        soup=BeautifulSoup(MarkdownIt().enable('table').render(md),'html.parser')
        self.assertEqual({},consolidated_table_entries([(d,Path('x.md'),md,soup,[])]))

    def test_consolidated_scanner_is_bounded_by_next_h2(self):
        md='# 定義\n## TBL-001 台帳\n|情報|内容|\n|---|---|\n|物理名|Ledger|\n\n## TBL-002 別表\n|論理名|物理名|\n|---|---|\n|別項目|secret|'
        soup=BeautifulSoup(MarkdownIt().enable('table').render(md),'html.parser')
        d={'db_tables':[{'table':'Ledger','section':'TBL-001 台帳'}]}
        e=consolidated_table_entries([(d,Path('x.md'),md,soup,[])])
        self.assertNotIn('secret',e['ledger'][2])


if __name__=='__main__':unittest.main()

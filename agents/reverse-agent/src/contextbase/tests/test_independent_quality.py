"""Mutation tests: expectations are hand-written, not copied from the producer."""
import json
from pathlib import Path
import tempfile
import unittest
from PIL import Image,ImageDraw
from contextbase.validation.quality import inspect,scan_sources
from specgen.adapters.java_sql import analyze_sql,sql_details
from specgen.sql import sql_facts

class AuditTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
        self.input=self.root/'input';self.input.mkdir()
        (self.input/'view.html').write_text('<html><body><label>顧客番号<input name="id"></label></body></html>')
        (self.input/'schema.sql').write_text('CREATE TABLE Customer (id INT PRIMARY KEY, name VARCHAR(30));\nUPDATE Customer SET name = ? WHERE id = ?;')
        self.p1=self.root/'ContextBase/01-foundation';self.p2=self.root/'ContextBase/02-detailed'
        self.f={'id':'SCR-001','path':'view.html','name':'顧客画面','kind':'screen'}
        self.model={**self.f,'items':[{'id':'I1','name':'顧客番号'}],'layout':{'images':[{'path':'assets/screen.png'}]},'sql_operations':[]}
        self.db={'tables':[{'name':'Customer','logical_name':{'value':'顧客'},'columns':[{'name':'id','logical_name':{'value':'顧客番号'}},{'name':'name','logical_name':{'value':'氏名'}}]}]}
        self.docs=[{'path':'基本設計書/顧客.md','feature_id':'SCR-001','model':{'sections':[]}}, {'path':'共通/DB仕様書/顧客.md','db_table':'Customer','model':{'sections':[]}}, {'path':'共通/DB操作.md','model':{'sections':[]}}]
        self.write(self.p1/'catalogs/features.json',[self.f]);self.write(self.p1/'database/catalog.json',self.db)
        self.write(self.p2/'functions/SCR-001/feature.json',self.model);self.write(self.p2/'resolved/catalog.json',{'features':[{'id':'SCR-001'}],'documents':self.docs})
        self.screen=self.root/'output/md/基本設計書/顧客.md';self.screen.parent.mkdir(parents=True)
        self.screen.write_text('# 顧客\n## 画面レイアウト\n![画面](assets/screen.png)\n## 項目一覧\n|項目名|種類|\n|---|---|\n|顧客番号|TextBox|\n')
        self.image=self.screen.parent/'assets/screen.png';self.image.parent.mkdir()
        im=Image.new('RGB',(300,120),'white');ImageDraw.Draw(im).rectangle((20,20,240,60),outline='black');im.save(self.image)
        self.dbdoc=self.root/'output/md/共通/DB仕様書/顧客.md';self.dbdoc.parent.mkdir(parents=True)
        self.dbdoc.write_text('# 顧客テーブル定義書\n\n顧客情報の項目定義を示す。原本schema.sqlに宣言された表と列を記載する。\n\n|論理名|物理名|型|\n|---|---|---|\n|顧客番号|id|INT|\n|氏名|name|VARCHAR(30)|\n\n主キーは顧客番号。各列の型は宣言に従う。\n')
        self.opdoc=self.root/'output/md/共通/DB操作.md'
        self.op='''# DB操作
|情報|内容|
|---|---|
|操作ID|SQL-001|
|対象テーブル|Customer|
|操作|更新|
|処理説明|顧客の氏名を指定した顧客番号で更新する。|
|設定項目|氏名へ入力された文字列を設定する。|
|対象条件|顧客番号が指定番号と等しい行を対象とする。|
|確定・取消|呼出側のトランザクション設定に従って確定する。|
|原本|schema.sql:2|
'''
        self.opdoc.write_text(self.op)
    def tearDown(self):self.tmp.cleanup()
    def write(self,p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False))
    def errors(self):return {c['code'] for c in inspect(self.root)['checks'] if not c['pass']}
    def test_good_fixture(self):self.assertEqual(set(),self.errors())
    def test_source_screen_missing_from_context(self):
        self.write(self.p1/'catalogs/features.json',[]);self.assertIn('UI-001',self.errors())
    def test_missing_screen_markdown(self):self.screen.unlink();self.assertIn('UI-003',self.errors())
    def test_missing_layout_block(self):self.screen.write_text('# 顧客\n説明のみ');self.assertIn('UI-003',self.errors())
    def test_missing_image_file(self):self.image.unlink();self.assertIn('UI-005',self.errors())
    def test_corrupt_image(self):self.image.write_bytes(b'bad');self.assertIn('UI-005',self.errors())
    def test_blank_large_image_is_not_layout(self):
        Image.new('RGB',(300,120),'white').save(self.image);self.assertIn('UI-005',self.errors())
    def test_published_item_logical_name_cannot_be_english(self):
        self.screen.write_text(self.screen.read_text().replace('|顧客番号|','|customerID|'));self.assertIn('NAME-005',self.errors())
    def test_published_db_column_logical_name_cannot_be_english(self):
        self.dbdoc.write_text(self.dbdoc.read_text().replace('|氏名|','|name|'));self.assertIn('NAME-005',self.errors())
    def test_column_mentioned_only_in_prose_is_not_defined(self):
        self.dbdoc.write_text(self.dbdoc.read_text().replace('|氏名|name|VARCHAR(30)|','')+'\nnameは原本参照。');self.assertIn('DB-003',self.errors())
    def test_custom_input_folder(self):
        self.input.rename(self.root/'original')
        self.write(self.p1/'manifest.json',{'input':'original'})
        self.assertEqual(set(),self.errors())
    def test_missing_source_cannot_pass(self):
        self.input.rename(self.root/'original')
        with self.assertRaises(ValueError):self.errors()
    def test_tiny_image(self):Image.new('RGB',(1,1)).save(self.image);self.assertIn('UI-005',self.errors())
    def test_reviewed_screen_has_no_exemption(self):
        self.model['reviewed']={'status':'approved'};self.write(self.p2/'functions/SCR-001/feature.json',self.model)
        self.screen.write_text('# 顧客');self.assertIn('UI-003',self.errors())
    def test_db_spec_deleted(self):self.dbdoc.unlink();self.assertIn('DB-002',self.errors())
    def test_db_hidden_from_both_context_and_catalog(self):
        self.write(self.p1/'database/catalog.json',{'tables':[]});self.docs=self.docs[:1]+self.docs[2:]
        self.write(self.p2/'resolved/catalog.json',{'features':[{'id':'SCR-001'}],'documents':self.docs});self.dbdoc.unlink()
        self.assertIn('DB-001',self.errors());self.assertIn('DB-002',self.errors())
    def test_db_column_deleted(self):
        self.dbdoc.write_text(self.dbdoc.read_text().replace('|氏名|name|VARCHAR(30)|',''));self.assertIn('DB-003',self.errors())
    def test_english_feature_name(self):
        self.model['name']='Customer';self.write(self.p2/'functions/SCR-001/feature.json',self.model);self.assertIn('NAME-001',self.errors())
    def test_english_item_name(self):
        self.model['items'][0]['name']='customerId';self.write(self.p2/'functions/SCR-001/feature.json',self.model);self.assertIn('NAME-002',self.errors())
    def test_english_table_logical_name(self):
        self.db['tables'][0]['logical_name']['value']='Customer';self.write(self.p1/'database/catalog.json',self.db);self.assertIn('NAME-003',self.errors())
    def test_english_column_logical_name(self):
        self.db['tables'][0]['columns'][0]['logical_name']['value']='ID';self.write(self.p1/'database/catalog.json',self.db);self.assertIn('NAME-004',self.errors())
    def test_two_update_methods_require_two_descriptions(self):
        (self.input/'repo.java').write_text('class R {\n public void first(){execute("UPDATE Customer SET name=? WHERE id=?");}\n public void second(){execute("UPDATE Customer SET name=? WHERE id=?");}\n}')
        self.opdoc.write_text(self.op+'\n'+self.op.replace('schema.sql:2','repo.java:2 / first@2'))
        bad=[c for c in inspect(self.root)['checks'] if not c['pass']]
        self.assertTrue(any(c['code']=='DML-001' and 'second@3' in c['subject'] for c in bad))
    def test_enforcement_has_nonzero_error(self):
        from contextbase.validation.quality import enforce
        self.dbdoc.unlink()
        with self.assertRaisesRegex(ValueError,'Independent quality gate failed'):enforce(self.root)
    def test_english_physical_names_allowed(self):self.assertEqual(set(),self.errors())
    def test_update_explanation_missing(self):self.opdoc.write_text('# DB操作\nCustomerの更新');self.assertIn('DML-001',self.errors())
    def test_other_table_does_not_satisfy_update(self):self.opdoc.write_text(self.op.replace('|Customer|','|Other|'));self.assertIn('DML-001',self.errors())
    def test_missing_update_assignments(self):self.opdoc.write_text(self.op.replace('氏名へ入力された文字列を設定する。',''));self.assertIn('DML-002',self.errors())
    def test_missing_update_condition(self):self.opdoc.write_text(self.op.replace('顧客番号が指定番号と等しい行を対象とする。',''));self.assertIn('DML-002',self.errors())
    def test_global_db_book_does_not_replace_feature_description(self):
        self.model['sql_operations']=[{'id':'SQL-001','operation':'U'}];self.write(self.p2/'functions/SCR-001/feature.json',self.model)
        self.assertIn('DML-003',self.errors())
    def test_insert_has_its_own_obligation(self):
        with (self.input/'schema.sql').open('a') as f:f.write('\nINSERT INTO Customer (id,name) VALUES (?,?);')
        self.assertIn('DML-001',self.errors())
    def test_comments_do_not_create_db_obligations(self):
        (self.input/'dummy.java').write_text('// INSERT INTO Phantom (x) VALUES (1);\nclass Dummy {}')
        self.assertNotIn('phantom',scan_sources(self.input)['tables'])
    def test_trim_from_is_not_a_table(self):
        (self.input/'sample.java').write_text('class A { String x="SELECT TRIM(\'　\' from 漢字店名) FROM Customer"; }')
        self.assertNotIn('漢字店名',scan_sources(self.input)['tables'])
    def test_constant_target_is_independently_found(self):
        (self.input/'repo.java').write_text('class A { static final String TABLE="注文＿履歴"; String sql="INSERT INTO " + TABLE + " (番号) VALUES (?)"; }')
        self.assertIn('注文＿履歴',scan_sources(self.input)['tables'])

class SqlRegressionTests(unittest.TestCase):
    def test_fullwidth_underscore_identifier_not_truncated(self):
        tables,ops,_=sql_facts('CREATE TABLE 年金＿削除明細 (番号 INT); INSERT INTO 年金＿削除明細 (番号) VALUES (1);')
        self.assertEqual('年金＿削除明細',tables[0]['name']);self.assertEqual('年金＿削除明細',ops[0]['table'])
    def test_dynamic_builder_target_and_set_fields(self):
        text='''class Orders { static final String DB="販売.注文＿履歴"; public void update(int number) { StringBuilder q=new StringBuilder(); q.append("UPDATE ").append(DB); q.append(" SET 金額=").append(number); q.append(" WHERE 番号=1"); execute(q.toString()); }}'''
        q=[q for q in analyze_sql(text,'orders.java')['queries'] if q['operation']=='U'][0]
        self.assertEqual('販売.注文＿履歴',q['table']);self.assertIn('金額',sql_details(q)['columns']);self.assertIn('番号=1',sql_details(q)['where'])
    def test_lock_clause_is_not_an_update_table(self):
        _,ops,_=sql_facts("SELECT 番号 FROM 顧客 FOR UPDATE WAIT 10")
        self.assertEqual(['顧客'],[o['table'] for o in ops]);self.assertEqual(['R'],[o['operation'] for o in ops])
    def test_direct_custom_execution_sql_is_captured(self):
        q=analyze_sql('class A { public void run(){executeMap("SELECT コード FROM 業種");}}','a.java')['queries']
        self.assertEqual(['業種'],[x['table'] for x in q])
    def test_shared_builder_helper_preserves_column_alignment(self):
        text='''class A {
          static final String comma=","; StringBuffer sb=new StringBuffer();
          public void save(Map map){sb.append("INSERT INTO 顧客 (番号,氏名,更新者) VALUES (");sb.append("1"); column(map,"氏名");sb.append(",").append(map.get("更新者")).append(")");execute(sb.toString());}
          private void column(Map map,String key){sb.append(comma);if(map.get(key)!=null){sb.append(map.get(key));}else{sb.append("null");}}
        }'''
        q=next(q for q in analyze_sql(text,'a.java')['queries'] if q['operation']=='C')
        d=sql_details(q);self.assertEqual(3,len(d['values']));self.assertIn('氏名',d['values'][1]);self.assertIn('更新者',d['values'][2])
    def test_no_application_execution(self):
        text='class A { public void run(){Runtime.getRuntime().exec("rm -rf /"); String q="UPDATE Customer SET id=1";} }'
        self.assertTrue(analyze_sql(text,'a.java')['queries'])

if __name__=='__main__':unittest.main()

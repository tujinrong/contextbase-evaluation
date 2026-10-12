from __future__ import annotations
import copy,json,re,tempfile,unittest
from pathlib import Path
from docsite.er_diagram import parse_er
from docsite.diagram import render,parse
from mcterpgen.employee_db import (ASSETS,FEATURE,COMMON,API,SQL,PATHS,NO_DB,refined,audit_document,layout_blocks,check_sources,section)
from mcterpgen.scan import read,functions

ROOT=Path(__file__).resolve().parents[4]

class ErTests(unittest.TestCase):
    def diagram(self):return 'erDiagram\nA["基表"] {\n number ID PK\n}\nB["値"] {\n number 参照ID\n}\nA ||..o{ B : "任意件数"\n'
    def test_cardinality(self):
        e=parse_er(self.diagram())['edges'][0]
        self.assertEqual((e['tail_cardinality'],e['head_cardinality']),('1','0..n'))
    def test_optional_one(self):self.assertEqual(parse_er(self.diagram().replace('||..','|o..'))['edges'][0]['tail_cardinality'],'0..1')
    def test_er_attribute_preserved(self):self.assertIn('PK  ID',parse_er(self.diagram())['nodes']['A']['label'])
    def test_unknown_attribute_fails(self):
        with self.assertRaises(ValueError):parse_er(self.diagram().replace('number ID PK','unknown <tag>'))
    def test_unclosed_fails(self):
        with self.assertRaises(ValueError):parse_er('erDiagram\nA {\n number ID')
    def test_empty_fails(self):
        with self.assertRaises(ValueError):parse_er('erDiagram')
    def test_exec_directive_fails(self):
        with self.assertRaises(ValueError):parse_er(self.diagram()+'click A "https://example.test"')
    def test_er_svg(self):
        svg=render(self.diagram(),'test');self.assertIn('graphviz-er',svg);self.assertIn('0..n',svg)
    def test_flowchart_unchanged(self):self.assertEqual(parse('flowchart LR\nA["x"] --> B["y"]')['edges'][0]['to'],'B')

class EmployeeDbTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from contextbase.external_spec import render as external_render
        from mcterpgen.employee_layout import screens
        from mcterpgen.employee_contract import contract,fields
        views,_,columns=screens(ROOT,fields())
        cls.base=external_render(contract(views,columns));cls.doc=refined(cls.base)
        cls.source=read(ROOT/PATHS['service'])
        cls.methods={m['name']:m for m in functions(cls.source,PATHS['service'],'cs')}
    def test_idempotence(self):self.assertEqual(refined(self.doc),self.doc)
    def test_layout_immutable(self):self.assertEqual(layout_blocks(self.base),layout_blocks(self.doc))
    def test_item_table_immutable(self):self.assertEqual(section(self.base,2),section(self.doc,2))
    def test_contract_complete(self):self.assertEqual(audit_document(self.doc,self.base)['errors'],[])
    def test_missing_logic_fails(self):self.assertTrue(audit_document(self.doc.replace('ANDで判定','一致で判定'),self.base)['errors'])
    def test_missing_delete_phase_fails(self):self.assertTrue(audit_document(self.doc.replace('既存値を全削除','既存値を参照'),self.base)['errors'])
    def test_missing_er_fails(self):self.assertTrue(audit_document(self.doc.replace('    EMP ||..o{ FREE : "社員内部ID一致・社員用対象種別に限定"',''),self.base)['errors'])
    def test_layout_mutation_fails(self):self.assertTrue(audit_document(self.doc.replace('data-width="1500"','data-width="1499"',1),self.base)['errors'])
    def test_source_change_not_silent(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError):check_sources(Path(d))
    def test_common_all_ids(self):
        text=(ASSETS/'common.md').read_text()
        for i in range(1,14):self.assertIn('### CDB-'+str(i).zfill(2),text)
    def test_api_all_ten(self):
        front=read(ROOT/PATHS['frontend']);active=re.sub(r'//[^\n]*','',front)
        self.assertEqual(set(re.findall(r"const methodname = '([^']+)'",active)),set(API))
    def test_database_absent_events_not_fake(self):self.assertEqual(set(NO_DB),{'EMP-03','EMP-07','EMP-08','EMP-10','EMP-15'})
    def test_source_search_has_no_join(self):
        sql=re.sub(r'--[^\n]*','',read(ROOT/SQL));self.assertNotRegex(sql,r'\bJOIN\b');self.assertIn('FROM hrm_emp T1',sql)
    def test_query_read_defect_is_documented(self):
        text=read(ROOT/PATHS['dbutil'])
        stmt=re.search(r'"SELECT \* FROM temp_search_data  LIMIT[^";]+;',text)[0]
        self.assertNotIn('ORDER BY',stmt);self.assertIn('取得時の並び順を再指定していません',self.doc)
    def test_nested_delete_insert_order_matches_source(self):
        src=read(ROOT/PATHS['free']);start=src.index('public static void UpdateFree2List');end=src.index('public static Dictionary',start)
        part=src[start:end];self.assertLess(part.index('db.cmt_free2.DELETE'),part.index('db.cmt_free2.INSERT'))
        self.assertIn('行番号を1から振り直す',self.doc)
    def test_single_values_not_called_insert(self):
        src=read(ROOT/PATHS['free']);part=src[src.index('public static void UpdateFreeList'):src.index('public static void UpdateFree2List')]
        self.assertIn('db.cmt_free.UPDATE',part);self.assertNotIn('db.cmt_free.INSERT',part)
        self.assertIn('新規作成するかはCDB-07の未確認',self.doc)
    def test_save_includes_user_rights_not_just_emp(self):
        part=self.methods['Save']['body']
        for token in ['db.hrm_emp.INSERT','db.cmm_user.INSERT','db.cmm_user_right.INSERT','CmFreeService.UpdateFreeList','CmFreeService.UpdateFree2List']:
            self.assertIn(token,part)
        self.assertEqual(len(API['Save']['tables']),8)
    def test_error_return_not_rollback_guarantee(self):
        src=read(ROOT/PATHS['transaction']);m=[x for x in functions(src,PATHS['transaction'],'cs') if x['name']=='Transction'][0]
        self.assertIn('tran.Commit()',m['body']);self.assertNotIn('returncode',m['body'])
        self.assertIn('返却コードに関係なく確定', (ASSETS/'common.md').read_text())
    def test_csv_uses_correct_helper(self):
        self.assertIn('ExportToCsvBytes',self.methods['CsvExreport']['body'])
        src=read(ROOT/PATHS['csv']);m=[x for x in functions(src,PATHS['csv'],'cs') if x['name']=='ExportToCsvBytes'][0]
        self.assertNotIn('.Replace(',m['body']);self.assertIn('エスケープは行わない',self.doc)
    def test_conflict_null_semantics(self):
        # Independent truth-table example of the literal predicates in the source.
        sql=read(ROOT/SQL)
        self.assertIn('conflict_flg_in IS TRUE',sql)
        for col in ['job_status','emptype','workloc']:self.assertRegex(sql,col+r'_cd_in IS NULL OR')
        requested=[1,None,None];actual=[3,2,4]
        predicates=[req is None or req==got for req,got in zip(requested,actual)]
        self.assertFalse(all(predicates));self.assertTrue(any(predicates))
    def test_current_and_saved_versions_separate(self):
        src=read(ROOT/SQL);params=re.findall(r'\b\w+_in\b',src[:src.index('RETURNS')]);self.assertEqual(len(params),11)
        self.assertIn('ダンプは6引数',(ASSETS/'common.md').read_text())

if __name__=='__main__':unittest.main()

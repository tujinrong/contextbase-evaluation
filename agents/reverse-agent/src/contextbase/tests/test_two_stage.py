from pathlib import Path
import json
import tempfile
import unittest
from contextbase.foundation.core import run as foundation, reconcile_database
from contextbase.detail.core import run as detail
from contextbase.specification.core import run as specification
from contextbase.validation.core import check, source_free_replay
from contextbase.shared.store import verify, read, digest, tree_hashes, safe
from contextbase.shared.schemas import validate, SCHEMAS
from specgen.adapters.csharp_flow import analyze_flow
from jsonschema import Draft202012Validator

MODEL='''public class ScreenModel(IService service) : PageModel {
[BindProperty] [Required] public int? Code {get;set;}
public void OnGet(){ Code = 1; }
public IActionResult OnPost(){
 if (!ModelState.IsValid){ return Page(); }
 service.Save(Code);
 return RedirectToPage("/Index");
}
public IActionResult OnPostClear(){
 ModelState.Clear(); Code = null;
 return Page();
}
}'''

class FlowTests(unittest.TestCase):
    def test_primary_constructor_does_not_hide_handlers(self):
        r=analyze_flow(MODEL,'x.cs')
        self.assertEqual(['OnGet','OnPost','OnPostClear'],[m['name'] for m in r['methods']])
    def test_comments_strings_cannot_create_handler(self):
        r=analyze_flow(MODEL+' // public void Fake(){ }\n /* class X { void Bad(){} } */','x.cs')
        self.assertEqual(3,len(r['methods']))
    def test_guard_return_constrains_following_save(self):
        m=analyze_flow(MODEL,'x.cs')['methods'][1]
        save=next(n for n in m['steps'] if 'service.Save' in n.get('expression',''))
        self.assertIn('NOT (!ModelState.IsValid)',save['guards'])
    def test_else_retains_complement(self):
        r=analyze_flow('class A { void F(){if(x){a=1;}else{a=2;}}}','a.cs')
        self.assertEqual(['NOT (x)'],r['methods'][0]['flow'][0]['else'][0]['guards'])
    def test_nested_if_and_loop(self):
        r=analyze_flow('class A { void F(){foreach(var x in xs){if(x!=null){Save(x);}}}}','a.cs')
        save=r['methods'][0]['flow'][0]['body'][0]['body'][0]
        self.assertEqual(2,len(save['guards']))
    def test_source_line_preserved(self):
        r=analyze_flow('\n\nclass A { void F(){\nreturn;\n}}','a.cs')
        self.assertEqual(4,r['methods'][0]['steps'][0]['line'])
    def test_positional_record_not_a_method(self):
        r=analyze_flow('public record Item(int Code, string Name);','Item.cs')
        self.assertEqual([],r['methods']);self.assertEqual('Item',r['types'][0]['name'])

class TwoStageTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name);source=self.root/'input/Pages';source.mkdir(parents=True)
        (source/'Screen.cshtml').write_text('@page\n<h1>Test</h1><label asp-for="Code">番号</label><input asp-for="Code"><button>保存</button><button asp-page-handler="Clear">消去</button>')
        (source/'Screen.cshtml.cs').write_text(MODEL)
    def phases(self):
        foundation(self.root);detail(self.root);specification(self.root)
    def test_p1_no_delivery(self):
        r=foundation(self.root)
        self.assertEqual(1,r['screens']);self.assertFalse((self.root/'output').exists())
        f=read(self.root/'ContextBase/01-foundation/catalogs/features.json')[0]
        self.assertEqual('Pages/Screen.cshtml.cs',f['companion'])
    def test_p2_structured_handlers_not_final_markdown(self):
        foundation(self.root);r=detail(self.root)
        self.assertEqual(3,r['events']);self.assertFalse((self.root/'output/md').exists())
        fid=read(self.root/'ContextBase/01-foundation/catalogs/features.json')[0]['id']
        f=read(self.root/f'ContextBase/02-detailed/functions/{fid}/feature.json')
        self.assertTrue(f['events'][1]['methods'][0]['flow'])
        self.assertNotIn('markdown',f)
    def test_source_free_generation_matches(self):
        self.phases();self.assertEqual('pass',source_free_replay(self.root)['status'])
    def test_stale_input_rejected(self):
        foundation(self.root);p=self.root/'input/Pages/Screen.cshtml.cs';p.write_text(MODEL+'\n// changed')
        with self.assertRaisesRegex(ValueError,'generation mismatch'):detail(self.root)
    def test_tampered_foundation_rejected(self):
        foundation(self.root);p=self.root/'ContextBase/01-foundation/catalogs/features.json';p.write_text('[]')
        with self.assertRaises(ValueError):detail(self.root)
    def test_tampered_resolved_rejected(self):
        foundation(self.root);detail(self.root)
        p=self.root/'ContextBase/02-detailed/resolved/catalog.json';p.write_text('{}')
        with self.assertRaises(ValueError):specification(self.root)
    def test_warm_foundation_generation_stable(self):
        first=foundation(self.root);second=foundation(self.root)
        self.assertEqual(first['generation'],second['generation']);self.assertEqual(2,second['cache_hits'])
    def test_warm_detail_reuses_semantics(self):
        foundation(self.root);a=detail(self.root);b=detail(self.root)
        self.assertEqual(a['generation'],b['generation']);self.assertEqual(1,b['cache_hits'])
    def test_qa_answers_preserved(self):
        foundation(self.root);detail(self.root)
        p=self.root/'QA/questions.json';q=read(p);q['questions'][0]['answer']='人の回答';p.write_text(json.dumps(q))
        detail(self.root)
        self.assertTrue(any(x['answer']=='人の回答' for x in read(p)['questions']))
    def test_output_deleted_without_context_deleted(self):
        self.phases();before=tree_hashes(self.root/'ContextBase')
        import shutil;shutil.rmtree(self.root/'output');specification(self.root)
        self.assertEqual(before,tree_hashes(self.root/'ContextBase'))
    def test_source_unchanged(self):
        before=tree_hashes(self.root/'input');self.phases();self.assertEqual(before,tree_hashes(self.root/'input'))
    def test_schema_rejects_wrong_io(self):
        self.phases();fid=read(self.root/'ContextBase/02-detailed/manifest.json')['feature_ids'][0]
        model=read(self.root/f'ContextBase/02-detailed/functions/{fid}/feature.json');model['items'][0]['io']='input'
        with self.assertRaises(ValueError):validate('feature',model)
    def test_all_schemas_valid(self):
        for s in SCHEMAS.values():Draft202012Validator.check_schema(s)
    def test_physical_table_not_created_from_model(self):
        r=foundation(self.root);self.assertEqual(0,r['physical_tables']);self.assertGreater(r['data_objects'],0)
    def test_ddl_conflict_retains_both(self):
        source=self.root/'input'
        (source/'a.sql').write_text('CREATE TABLE T (Code varchar(8) NOT NULL);')
        (source/'b.sql').write_text('CREATE TABLE T (Code varchar(12) NOT NULL);')
        foundation(self.root);db=read(self.root/'ContextBase/01-foundation/database/catalog.json')
        self.assertEqual(1,len(db['tables']));self.assertEqual('conflict',db['tables'][0]['columns'][0]['status'])
    def test_missing_feature_fails_without_publishing(self):
        self.phases();before=tree_hashes(self.root/'output')
        with self.assertRaises(ValueError):detail(self.root,feature='not-a-feature')
        self.assertEqual(before,tree_hashes(self.root/'output'))
    def test_safe_rejects_symlink_and_escape(self):
        (self.root/'alias').symlink_to(self.root/'input',target_is_directory=True)
        for path in ['../bad','alias/a.cs']:
            with self.assertRaises(ValueError):safe(self.root,path)
    def test_contract_gate(self):
        self.phases();self.assertEqual(0,check(self.root)['errors'])

if __name__=='__main__':unittest.main()

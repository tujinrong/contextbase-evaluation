from __future__ import annotations
import json,struct,tempfile,unittest
from pathlib import Path
from mcterpgen.scan import functions,vue,archive_schema,masked
from mcterpgen.model import schema,walk,collect
from mcterpgen.render import cell,diagram,feature,layout

class LexicalTests(unittest.TestCase):
    def test_cs_strings_and_comments_are_not_methods(self):
        x=functions('namespace Demo { class Service {\n // public int fake() {}\n public int Real() { var x="}"; return 1; }\n}}','Service.cs','cs')
        self.assertEqual([m['name'] for m in x],['Real']);self.assertIn('return 1',x[0]['body'])
    def test_multiple_methods_keep_own_namespace(self):
        x=functions('namespace A; class Service {\n public int First(int x){return x;}\n public void Second(){First(1);}\n}','a.cs','cs')
        self.assertEqual(len(x),2);self.assertEqual(x[1]['namespace'],'A');self.assertIn('First',x[1]['calls'])
    def test_vue_nested_template_not_truncated(self):
        x=vue('<template><template #title>見出し</template><a-input v-model="value"/><a-button @click="save">登録</a-button></template><script setup>const save=()=>{return 1}</script>','x.vue')
        self.assertEqual(len(x['items']),2);self.assertEqual(len(x['events']),1)
    def test_script_literals_are_not_ui(self):
        x=vue('<template><input v-model="x"/></template><script>const x="<button @click=\'bad\'>危険</button>"</script>','x.vue')
        self.assertEqual(len(x['items']),1);self.assertEqual(len(x['events']),0)
    def test_display_and_operation_not_required(self):
        x=vue('<template><a-input v-model="x" disabled required/><BaseClockButton @click="go">出勤</BaseClockButton></template>','x.vue')
        self.assertEqual(x['items'][0]['role'],'表示');self.assertEqual(x['items'][0]['required'],'入力対象外');self.assertEqual(x['items'][1]['role'],'操作')
    def test_rule_requirement_not_guessed_from_db(self):
        x=vue('<template><AiView label="氏名"><a-input v-model="form.name"/></AiView></template><script>const rules=reactive({name:[{required:true}]})</script>','x.vue')
        self.assertIn('必須',x['items'][0]['required']);self.assertEqual(x['items'][0]['name'],'氏名')
    def test_conditional_edit_state_is_retained(self):
        x=vue('<template><AiView :is-edit-mode="editing" v-if="hasData"><a-input v-model="x" :max-length="20"/></AiView></template>','x.vue')
        self.assertIn('editing',x['items'][0]['condition']);self.assertEqual(x['items'][0]['length'],'20')
    def test_mask_preserves_line_positions(self):
        s='//abc\n"a\\\"{}"\nvoid m() {}';self.assertEqual(len(masked(s)),len(s));self.assertEqual(masked(s).count('\n'),s.count('\n'))

class SchemaTests(unittest.TestCase):
    def test_only_validated_archive_strings(self):
        sql=b'CREATE TABLE public.a (\n id integer NOT NULL\n);\n';head=b'PGDMP'+bytes([1,16,0,4,8]);raw=head+b'xx'+b'\x00'+struct.pack('<I',len(sql))+sql+b'garbage CREATE TABLE secret (id int);\n'
        entries=archive_schema(raw);self.assertEqual(len(entries),1);self.assertEqual(entries[0]['sql'],sql.decode())
    def test_invalid_archive_not_assumed_schema(self):
        with self.assertRaises(ValueError):archive_schema(b'not an archive')
    def test_logical_names_type_and_composite_key(self):
        text="CREATE TABLE public.a (\n id integer NOT NULL,\n amount numeric(12,2),\n note text DEFAULT 'a,b'\n);\nCOMMENT ON TABLE public.a IS '受注';\nCOMMENT ON COLUMN public.a.amount IS '金額';\nALTER TABLE ONLY public.a ADD CONSTRAINT a_pk PRIMARY KEY (id);\n"
        t=schema([{'sql':text}],'dump')['a'];self.assertEqual(t['logical'],'受注');self.assertEqual(len(t['columns']),3);self.assertEqual(t['columns'][1]['type'],'numeric(12,2)');self.assertEqual(t['columns'][0]['key'],'PK')
    def test_call_cycle_terminates(self):self.assertEqual(walk({'A':['B'],'B':['A','C']},'A'),['A','B','C'])
    def test_raw_source_cannot_become_active_html(self):
        self.assertEqual(cell('<script>alert(1)</script>'),'&lt;script&gt;alert(1)&lt;/script&gt;');self.assertIn('&#124;',cell('a|b'))

class CollectionTests(unittest.TestCase):
    def setup_root(self,root):
        a=root/'input/demo/backend/BusinessService/Test/Service.cs';a.parent.mkdir(parents=True)
        a.write_text('namespace MCT.ERP.Service.Demo { class Service {\n public int Save(SaveRequest req) {return 1;}\n} }')
        p=a.with_name('Request.cs');p.write_text('namespace MCT.ERP.Service.Demo {\npublic class InitRequest {public string A {get;set;}}\npublic class SaveRequest {public int B {get;set;}}\n}')
        v=root/'input/demo/frontend/src/views/Demo/index.vue';v.parent.mkdir(parents=True)
        v.write_text('<template><a-button @click="go">登録</a-button></template><script>import {Save} from "./service"; const go=()=>{Save({});}</script>')
        v.with_name('service.ts').write_text('const servicename="Demo"; export const Save=(params)=>{const methodname="Save";return api(servicename,methodname,params)}')
    def test_multiclass_requests_are_not_merged(self):
        with tempfile.TemporaryDirectory() as tmp:
            r=Path(tmp);self.setup_root(r);d=collect(r,'input',True);shapes={s['name']:s for s in d['shapes']}
            self.assertEqual([f['name'] for f in shapes['InitRequest']['fields']],['A']);self.assertEqual([f['name'] for f in shapes['SaveRequest']['fields']],['B'])
    def test_api_link_and_cache_are_target_specific(self):
        with tempfile.TemporaryDirectory() as tmp:
            r=Path(tmp);self.setup_root(r);a=collect(r,'input',True);b=collect(r,'input')
            self.assertEqual(a['features'][0]['id'],'MCT-Demo');self.assertEqual(b['stats']['parsed_this_run'],0);self.assertEqual(b['stats']['cache_hits'],4);self.assertFalse(b['unresolved_api'])
    def test_corrupt_cache_recovered(self):
        with tempfile.TemporaryDirectory() as tmp:
            r=Path(tmp);self.setup_root(r);collect(r,'input',True);cache=next((r/'.specgen-state/mcterp/files').glob('*.json'));cache.write_text('invalid')
            self.assertEqual(collect(r,'input')['stats']['parsed_this_run'],1)
    def test_input_never_executed_or_mutated(self):
        with tempfile.TemporaryDirectory() as tmp:
            r=Path(tmp);self.setup_root(r);before={p:p.read_bytes() for p in (r/'input').rglob('*') if p.is_file()};collect(r,'input',True);self.assertTrue(all(p.read_bytes()==v for p,v in before.items()))

if __name__=='__main__':unittest.main()

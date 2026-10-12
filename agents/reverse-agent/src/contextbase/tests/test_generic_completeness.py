"""Cross-project regressions: no JSBRMS/Pilot names in generic test fixtures."""
from pathlib import Path
import unittest
from specgen.adapters.csharp_flow import analyze_flow
from specgen.adapters.csharp_relations import SemanticIndex
from contextbase.shared.identities import assign, resolve
from contextbase.detail.layout import sanitize_markup, projection
from contextbase.detail.semantics import explain, field_labels, client_events, attach_item_storage
from contextbase.detail.documents import basic_document


def index_for(sources):
    methods=[]
    for path,text in sources.items():
        for m in analyze_flow(text,path)['methods']:
            m['id']=m.get('owner','')+'.'+m['name']+':'+str(m['line']);methods.append(m)
    return SemanticIndex(sources,methods),methods


SOURCES={
 'Program.cs':'builder.Services.AddSingleton<IOrderStore, OrderStore>();',
 'Edit.cs':'class EditModel(IOrderStore orderStore) { public void OnPostSave(){if(!Valid()){return;} orderStore.Save(Entry); } bool Valid(){return true;} public void OnPostDelete(){if(orderStore.Delete(4)){return;}} }',
 'OrderStore.cs':'''class OrderStore : IOrderStore {
 private readonly List<Order> records = new();
 public void Save(Order requested){
  lock(sync){
   var index = records.FindIndex(row => row.Code == requested.Code);
   var replacement = requested.Clone();
   replacement.Date = DateTime.Today;
   if(index >= 0){records[index] = replacement;return;}
   records.Add(replacement);
  }
 }
 public bool Delete(int code){
  var found=records.FirstOrDefault(row=>row.Code==code);
  if(found==null){return false;}
  records.Remove(found);return true;
 }
}'''
}

class RelationTests(unittest.TestCase):
    def test_call_in_condition_is_extracted(self):
        m=analyze_flow(SOURCES['Edit.cs'],'Edit.cs')['methods'][-1]
        self.assertTrue(any(c['name']=='orderStore.Delete' for c in m['calls']))
    def test_literal_full_width_space_preserved(self):
        text='class A { string N(string s){return s.Trim().Replace("　", " ");} }'
        step=analyze_flow(text,'A.cs')['methods'][0]['steps'][0]
        self.assertIn('"　"',step['expression'])
    def test_receiver_resolves_registered_implementation(self):
        index,methods=index_for(SOURCES)
        entry=next(m for m in methods if m['name']=='OnPostSave')
        visits,edges,_=index.trace(entry,set(SOURCES))
        self.assertTrue(any(v['method']['owner']=='OrderStore' for v in visits))
    def test_save_discovers_read_update_create(self):
        index,methods=index_for(SOURCES)
        entry=next(m for m in methods if m['name']=='OnPostSave')
        visits,_,_=index.trace(entry,set(SOURCES))
        effects=index.effects(entry,visits)
        self.assertEqual({'read','update','create'},{r['operation'] for r in effects})
        self.assertTrue(all(r['call_chain'] for r in effects))
        self.assertTrue(all(r['kind']=='memory' and not r['physical_table_verified'] for r in effects))
    def test_custom_local_variable_assignment_is_retained(self):
        index,methods=index_for(SOURCES);entry=next(m for m in methods if m['name']=='OnPostSave')
        visits,_,_=index.trace(entry,set(SOURCES));effects=index.effects(entry,visits)
        self.assertTrue(any(a.get('target')=='replacement.Date' for r in effects for a in r['assignments']))
    def test_conditional_delete_reaches_remove(self):
        index,methods=index_for(SOURCES);entry=next(m for m in methods if m['name']=='OnPostDelete')
        visits,_,_=index.trace(entry,set(SOURCES))
        self.assertIn('delete',{r['operation'] for r in index.effects(entry,visits)})
    def test_two_registrations_remain_ambiguous(self):
        sources={**SOURCES,'Other.cs':'class OtherStore { public void Save(Order r){} }',
                 'Program.cs':SOURCES['Program.cs']+'builder.Services.AddSingleton<IOrderStore, OtherStore>();'}
        index,methods=index_for(sources);entry=next(m for m in methods if m['name']=='OnPostSave')
        visits,_,issues=index.trace(entry,set(sources))
        self.assertTrue(issues);self.assertFalse(any(v['method']['name']=='Save' for v in visits))
    def test_unrelated_same_name_is_not_bound(self):
        sources={'X.cs':'class X { void F(){unknown.Save(1);} }','Y.cs':'class Y { void Save(int n){} }'}
        index,methods=index_for(sources);entry=next(m for m in methods if m['name']=='F')
        visits,_,issues=index.trace(entry,set(sources))
        self.assertEqual(1,len(visits));self.assertTrue(issues)
    def test_parameter_receiver_scope_is_method_local(self):
        sources={'X.cs':'class X { void F(A svc){svc.Run();} void G(B svc){svc.Run();} }',
                 'A.cs':'class A { void Run(){} }','B.cs':'class B { void Run(){} }'}
        index,methods=index_for(sources)
        for name,owner in [('F','A'),('G','B')]:
            visits,_,_=index.trace(next(m for m in methods if m['name']==name),set(sources))
            self.assertEqual(owner,visits[-1]['method']['owner'])
    def test_comments_cannot_register_store(self):
        sources={'X.cs':'// builder.Services.AddSingleton<IX,X>();\nclass X { string note="List<Order> fake = new()"; }'}
        index,_=index_for(sources);self.assertFalse(index.stores);self.assertFalse(index.registrations)
    def test_local_collections_not_persistent_store(self):
        index,_=index_for({'A.cs':'class A { void F(){var xs = new List<Order>();xs.Add(x);} }'})
        self.assertFalse(index.stores)
    def test_recursion_is_bounded(self):
        sources={'X.cs':'class X { void A(){B();} void B(){A();} }'}
        index,methods=index_for(sources);visits,_,issues=index.trace(methods[0],set(sources))
        self.assertEqual(2,len(visits));self.assertTrue(any(i['reason']=='recursive_call' for i in issues))


class IdentityTests(unittest.TestCase):
    def feature(self,path):return {'id':'F-1234567890','kind':'screen','name':path,'path':path,'source_sha256':path}
    def test_readable_id_and_legacy_alias(self):
        fs=[self.feature('b')];assign(fs,project='p')
        self.assertEqual('SCR-001',fs[0]['id']);self.assertEqual('SCR-001',resolve('F-1234567890',fs))
    def test_insertion_does_not_renumber(self):
        fs=[self.feature('b')];ledger=assign(fs,project='p')
        fs=[self.feature('a'),self.feature('b')];assign(fs,ledger,'p')
        self.assertEqual({'a':'SCR-002','b':'SCR-001'},{f['path']:f['id'] for f in fs})
    def test_retired_ids_are_not_reused(self):
        ledger=assign([self.feature('a')],project='p');fs=[self.feature('z')];assign(fs,ledger,'p')
        self.assertEqual('SCR-002',fs[0]['id'])
    def test_explicit_business_id_retained(self):
        fs=[{**self.feature('a'),'id':'100008'}];assign(fs,project='p');self.assertEqual('100008',fs[0]['id'])
    def test_project_mismatch_fails(self):
        ledger=assign([self.feature('a')],project='p')
        with self.assertRaises(ValueError):assign([],ledger,'different')
    def test_rename_retains_id(self):
        ledger=assign([self.feature('a')],project='p');fs=[{**self.feature('b'),'source_sha256':'a'}];assign(fs,ledger,'p')
        self.assertEqual('SCR-001',fs[0]['id'])


class ProjectionTests(unittest.TestCase):
    def test_remove_active_content_and_external_urls(self):
        result=sanitize_markup('<script>alert(1)</script><input onclick="attack()"><iframe src="https://evil"></iframe><img src="file:///secret">')
        self.assertNotIn('<script',result);self.assertNotIn('onclick',result);self.assertNotIn('src=',result)
    def test_bool_model_becomes_checkbox(self):
        result=sanitize_markup('<input asp-for="Entry.Active">',{'Entry.Active':'CheckBox'})
        self.assertIn('type="checkbox"',result)
    def test_razor_nested_quote_expression_does_not_break_dom(self):
        result=sanitize_markup('<input class="form @(Model.Locked ? "locked" : "")" readonly="@Model.Locked">')
        self.assertNotIn('locked"',result);self.assertNotIn('readonly',result)
    def test_projection_carries_css_without_fetching(self):
        texts={'Pages/A.cshtml':'<h1>A</h1>','wwwroot/css/site.css':'body{background:white} @import "https://evil";'}
        result,deps=projection('Pages/A.cshtml',texts,[])
        self.assertIn('background:white',result);self.assertNotIn('https://evil',result);self.assertIn('Content-Security-Policy',result)
    def test_item_and_argument_are_not_collapsed(self):
        result=explain('item.Code == code',{'Code':'番号','code':'番号'})
        self.assertIn('保存データの番号',result);self.assertNotEqual('番号 == 番号',result)
    def test_client_confirm_and_cancel_are_preserved(self):
        markup='<button data-remove>除去</button><script>document.querySelector("[data-remove]")?.addEventListener("click",()=>{ const confirmed=ask({message:"よいですか",mode:"confirm"}); if(!confirmed){return;} remove();});</script>'
        events=client_events(markup,'a.html')
        self.assertEqual('除去',events[0]['name']);self.assertTrue(events[0]['confirmation']);self.assertTrue(events[0]['cancellation_return'])
    def test_byte_limit_replaces_unknown_length(self):
        item={'id':'x','binding':'Entry.Notes','name':'注記','io':'I','description':'','format':'制限なし（仮定）'}
        feature={'companion':'a.cs'};rules=[{'field':'Entry.Notes','message':'長すぎます','guards':['NOT (CountBytes(Entry.Notes) <= 56)'],'evidence':[{'path':'a.cs','line':1}]}]
        attach_item_storage([item],feature,{'a.cs':''},None,[],rules)
        self.assertIn('56',item['format']);self.assertIn('文字数ではない',item['format'])

if __name__=='__main__':unittest.main()

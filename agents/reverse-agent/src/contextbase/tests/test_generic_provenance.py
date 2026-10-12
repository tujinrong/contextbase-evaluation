"""Independent artificial projects expose cross-project names and lost evidence."""
from pathlib import Path
import json
import tempfile
import unittest

from contextbase.detail.core import flow_relations
from contextbase.detail.event_templates import Narrator
from contextbase.detail.semantics import explain, terminology
from contextbase.shared.store import digest
from specgen.adapters.csharp_flow import analyze_flow
from specgen.adapters.csharp_relations import SemanticIndex


class TerminologyProvenanceTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.hashes={'Store.cs':digest('class Store {}')}
        self.context={'project':'orders','input_dir':'input','source_hashes':self.hashes}

    def dictionary(self, name='approved', **changes):
        data={'schema':'contextbase.terminology.v1','trust':'repository-reviewed',
              'project_id':'orders','input_root':'input','source_hashes':dict(self.hashes),
              'types':{'Store':'注文保管'},'fields':{'Reference':'注文照合番号'}}
        data.update(changes)
        path=self.root/'src-dynamic'/name/'terminology.json'
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text(json.dumps(data,ensure_ascii=False),encoding='utf-8')
        return path

    def test_exact_snapshot_preserves_reviewed_types_and_fields(self):
        self.dictionary()
        self.assertEqual({'Store':'注文保管'},terminology(self.root,**self.context))
        self.assertEqual({'Reference':'注文照合番号'},terminology(self.root,'fields',**self.context))

    def test_same_type_other_project_cannot_supply_employee_name(self):
        self.dictionary(project_id='employees',types={'Store':'職員管理'})
        self.assertEqual({},terminology(self.root,**self.context))

    def test_same_project_other_input_is_rejected(self):
        self.dictionary(input_root='prior-source')
        self.assertEqual({},terminology(self.root,**self.context))

    def test_one_changed_source_rejects_old_labels(self):
        self.dictionary(source_hashes={'Store.cs':digest('old class Store {}')})
        self.assertEqual({},terminology(self.root,**self.context))

    def test_partial_snapshot_does_not_hide_unpinned_dependency(self):
        self.dictionary()
        context={**self.context,'source_hashes':{**self.hashes,'Other.cs':digest('other')}}
        self.assertEqual({},terminology(self.root,**context))

    def test_source_roots_alone_are_not_provenance(self):
        path=self.dictionary()
        path.write_text(json.dumps({'trust':'repository-reviewed','source_roots':['orders'],
                                   'types':{'Store':'旧業務'}}),encoding='utf-8')
        self.assertEqual({},terminology(self.root,**self.context))

    def test_missing_current_context_rejects_even_reviewed_dictionary(self):
        self.dictionary()
        self.assertEqual({},terminology(self.root))

    def test_unreviewed_dictionary_and_invalid_label_are_rejected(self):
        self.dictionary('unreviewed',trust='unreviewed')
        self.dictionary('invalid',types={'Store':17})
        self.assertEqual({},terminology(self.root,**self.context))

    def test_conflicting_matching_dictionaries_fail_instead_of_overwrite(self):
        self.dictionary('a');self.dictionary('b',types={'Store':'別の名称'})
        with self.assertRaisesRegex(ValueError,'Conflicting reviewed terminology'):
            terminology(self.root,**self.context)

    def test_nonmatching_profile_is_reported_without_changing_qa(self):
        self.dictionary(project_id='other')
        qa=self.root/'QA/questions.json';qa.parent.mkdir()
        content=b'{"questions":[{"answer":"human","status":"approved"}]}'
        qa.write_bytes(content);notes=[]
        self.assertEqual({},terminology(self.root,diagnostics=notes,**self.context))
        self.assertEqual(content,qa.read_bytes())
        self.assertEqual('project_mismatch',notes[0]['reason'])
        self.assertFalse(notes[0]['adopted'])


class NeutralSessionTests(unittest.TestCase):
    def test_cart_session_keeps_operation_guards_and_source_anchor(self):
        method={'name':'Cart','path':'Cart.cs','steps':[{'expression':'Session.Set("cart", value)',
                  'line':7,'guards':['permitted']} ]}
        relation=flow_relations([method])[0]
        self.assertEqual('セッション保持情報',relation['store'])
        self.assertNotIn('職員',relation['store'])
        self.assertEqual('update',relation['operation'])
        self.assertEqual(['permitted'],relation['guards'])
        self.assertEqual([{'path':'Cart.cs','line':7}],relation['evidence'])

    def narrator(self):
        source='''class SessionGate {
 public bool verify(){ var info = request.getSession().getAttribute("LOGIN_INFO");
 if(info == null){ return false; } return true; }
}'''
        methods=analyze_flow(source,'SessionGate.java')['methods']
        event={'id':'gate','name':'確認','methods':methods}
        return Narrator({'items':[],'dependencies':['SessionGate.java']},event,
                        {'SessionGate.java':source})

    def test_session_confirmation_does_not_invent_employee_or_login_subject(self):
        text=self.narrator().describe_call('verify','')
        self.assertEqual('セッション情報の確認結果を返す',text)
        self.assertNotIn('職員',text)
        self.assertNotIn('ログイン済み',text)

    def test_positive_and_negative_conditions_preserve_opposite_outcomes(self):
        narrator=self.narrator()
        self.assertEqual('セッション情報の確認結果が成立',narrator.condition('verify()'))
        self.assertEqual('セッション情報の確認結果が不成立',narrator.condition('!verify()'))


class EvidencePreservationTests(unittest.TestCase):
    def test_return_delegation_reaches_actual_callee_without_executing_input(self):
        source='''class Gateway {
 public int Invoke(int value){return Delegate(value);}
 private int Delegate(int value){return value + 1;}
}'''
        methods=analyze_flow(source,'Gateway.cs')['methods']
        for method in methods:method['id']=method['name']
        index=SemanticIndex({'Gateway.cs':source},methods)
        entry=next(m for m in methods if m['name']=='Invoke')
        visits,edges,unresolved=index.trace(entry,{'Gateway.cs'})
        self.assertEqual(['Invoke','Delegate'],[v['method']['name'] for v in visits])
        self.assertEqual('Delegate',edges[0]['callee'])
        self.assertEqual('value',edges[0]['arguments'])
        self.assertEqual([],unresolved)

    def test_long_literal_and_meaningful_spaces_survive_public_explanation(self):
        literal='"'+('語 　true null Input.Value && | 01 '*45)+'終端"'
        text=explain('row.Text = '+literal,{'Text':'説明','Value':'値'})
        self.assertIn(literal,text)
        self.assertTrue(text.endswith('終端"'))
        self.assertNotIn('…（詳細仕様に原文）',text)

    def test_model_translation_does_not_change_literal_identifiers_or_backticks(self):
        literal='"Input.Value  null  true  `code`"'
        self.assertEqual('画面入力の値 = '+literal,
                         explain('Input.Value = '+literal,{'Value':'値'}))

    def test_parser_preserves_longer_than_display_limit_call_argument(self):
        literal='"'+('文字　 '*1100)+'最後"'
        method=analyze_flow('class Gate { string Read(){return Echo('+literal+');} }','Gate.cs')['methods'][0]
        call=next(c for c in method['calls'] if c['name']=='Echo')
        self.assertEqual(literal,call['arguments'])


if __name__=='__main__':unittest.main()

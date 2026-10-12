"""Synthetic evidence and handoff checks; no real AI or application executes."""
from datetime import datetime, timedelta, timezone
from pathlib import Path
import json
import tempfile
import unittest
from unittest.mock import patch

from contextbase.ai import capsule, schemas, workflow


class ProvenanceTests(unittest.TestCase):
    def setUp(self):
        home=Path(__file__).resolve().parents[3]/'.tmp'
        home.mkdir(exist_ok=True)
        self.temp=tempfile.TemporaryDirectory(prefix='ai-provenance-',dir=home)
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);self.source=self.root/'source';self.source.mkdir()
        (self.source/'Cart.cs').write_bytes(b'class Cart {}\r\n')
        self.snapshot=self.root/'snapshot'
        capsule.create(self.source,self.snapshot,project_id='synthetic-cart')
        self.doc={'id':'CART','path':'基本設計書/カート.md','title':'カート',
                  'kind':'basic','sourcePaths':['sources/Cart.cs','manifest.json'],
                  'responsibilities':['原本で確認する役割']}
        metadata={'schema':'spec-md/1.0','documentId':'CART','version':'fixture-1',
                  'path':self.doc['path'],'sheets':[{'heading':'概要','kind':'GRID','sheet':'01_概要'}]}
        self.valid_content='<!-- spec-meta: '+json.dumps(metadata,ensure_ascii=False)+' -->\n# カート\n\n## 概要\n\n人工fixtureの原稿。\n'
        self.plan={'systemSummary':'人工カート','documents':[self.doc],'unresolved':[]}
        self.plan_file=self.root/'answer.txt'
        self.plan_bytes=json.dumps(self.plan,ensure_ascii=False,indent=4).encode('utf-8')
        self.plan_file.write_bytes(self.plan_bytes)
        self.started=capsule.verification_state(self.snapshot)['manifestSha256']

    def definition(self):
        bound=workflow.bind_existing_plan(self.snapshot,self.plan_file,self.started)
        return workflow.select_document(Path(bound['planFile']),'CART')

    def fake(self,workspace,job,prompt,schema,timeout):
        job.mkdir(parents=True)
        if schema==schemas.PLAN:value=self.plan
        elif schema==schemas.ANALYSIS:
            value={'documentId':'CART','sourcePathsRead':['sources/Cart.cs'],
                   'facts':[{'id':'F','topic':'宣言','statement':'Cart型を宣言する。',
                             'basis':'observed-source','references':[{'path':'indexed/Cart.cs.txt','startLine':1,'endLine':1}]}],
                   'unresolved':[],'coverageNotes':['人工fixture']}
        elif schema==schemas.DRAFT:
            value={'documentId':'CART','path':self.doc['path'],'content':self.valid_content,
                   'factCorrections':[],'unresolved':[]}
        else:value={'documentId':'CART','approved':True,'findings':[],'unresolved':[]}
        return {'exit_code':0,'metadata':{'status':'passed'},'answer':value}

    def test_recovered_plan_keeps_exact_response_and_unmodified_definition(self):
        definition=self.definition()
        self.assertEqual(self.plan_bytes,self.plan_file.read_bytes())
        self.assertEqual(self.plan_bytes,(self.root/'plan-verified.json').read_bytes())
        self.assertEqual(self.doc,dict(definition))
        self.assertNotIn('handoff',json.dumps(definition))
        self.assertEqual(self.started,definition.handoff['snapshot']['manifestSha256'])

    def test_plan_accepts_only_exact_original_display_index_and_inventory_aliases(self):
        for alias in ('Cart.cs','sources/Cart.cs','indexed/Cart.cs.txt','manifest.json'):
            value={**self.plan,'documents':[{**self.doc,'sourcePaths':[alias]}]}
            workflow._validate_plan(value,capsule.verify(self.snapshot))
        with self.assertRaises(ValueError):
            workflow._validate_plan({**self.plan,'documents':[{**self.doc,'sourcePaths':['other/Cart.cs']}]},capsule.verify(self.snapshot))

    def test_unsafe_windows_output_names_are_rejected_before_any_ai_job(self):
        for path in ('spec/NUL.md','spec/AUX.md','spec/COM1.md','spec/a?.md','spec/a*.md','spec/a\x00.md'):
            with self.subTest(path=path),self.assertRaises(ValueError):
                workflow._validate_plan({**self.plan,'documents':[{**self.doc,'path':path}]},capsule.verify(self.snapshot))

    def test_design_is_allowed_as_plan_material_but_not_observed_implementation(self):
        design=self.root/'design';design.mkdir();(design/'意図.md').write_text('# 意図\n',encoding='utf-8')
        assisted=self.root/'assisted';capsule.create(self.source,assisted,project_id='cart',authorized_reference_directories=(design,))
        manifest=capsule.verify(assisted);path=manifest['referenceFiles'][0]['path']
        workflow._validate_plan({**self.plan,'documents':[{**self.doc,'sourcePaths':[path]}]},manifest)
        fact={'id':'F','basis':'observed-source','references':[{'path':path,'startLine':1,'endLine':1}]}
        with self.assertRaises(ValueError):workflow.references_valid({'facts':[fact]},manifest)
        fact['basis']='reference-design';workflow.references_valid({'facts':[fact]},manifest)

    def test_fact_alias_has_exact_actual_raw_line_bounds(self):
        fact={'id':'F','basis':'observed-source','references':[{'path':'sources/Cart.cs','startLine':1,'endLine':1}]}
        workflow.references_valid({'facts':[fact]},capsule.verify(self.snapshot))
        fact['references'][0]['startLine']=2;fact['references'][0]['endLine']=2
        with self.assertRaises(ValueError):workflow.references_valid({'facts':[fact]},capsule.verify(self.snapshot))

    def test_manifest_is_planning_inventory_not_business_fact(self):
        fact={'id':'F','basis':'observed-source','references':[{'path':'manifest.json','startLine':1,'endLine':1}]}
        with self.assertRaises(ValueError):workflow.references_valid({'facts':[fact]},capsule.verify(self.snapshot))

    def test_invalid_fact_is_corrected_by_a_new_ai_job_not_silently_removed(self):
        definition=self.definition();calls=[]
        def corrected(workspace,job,prompt,schema,timeout):
            answer=self.fake(workspace,job,prompt,schema,timeout)
            calls.append((job.name,prompt))
            if job.name=='analysis':
                answer['answer']['facts'][0]['references'][0]['path']='manifest.json'
            return answer
        job=self.root/'document-job'
        with patch.object(workflow,'run_job',side_effect=corrected):
            result=workflow.document(self.snapshot,definition,job,self.root/'publication')
        self.assertEqual(['analysis','analysis-repair','draft'],[name for name,_ in calls])
        rejected=json.loads((job/'analysis-validation-failure.json').read_text(encoding='utf-8'))
        self.assertEqual('manifest.json',rejected['previousAiAnalysis']['facts'][0]['references'][0]['path'])
        accepted=json.loads((job/'analysis-verified.json').read_text(encoding='utf-8'))
        self.assertEqual('indexed/Cart.cs.txt',accepted['facts'][0]['references'][0]['path'])
        self.assertIn('previousAiAnalysis',calls[1][1])
        self.assertEqual(1,result['analysisFacts'])
        self.assertEqual(self.valid_content,(self.root/'publication'/self.doc['path']).read_text(encoding='utf-8'))

    def test_failed_ai_evidence_repair_does_not_start_drafting(self):
        definition=self.definition();calls=[]
        def invalid(workspace,job,prompt,schema,timeout):
            answer=self.fake(workspace,job,prompt,schema,timeout);calls.append(job.name)
            if schema==schemas.ANALYSIS:
                answer['answer']['facts'][0]['references'][0]['path']='manifest.json'
            return answer
        with patch.object(workflow,'run_job',side_effect=invalid),self.assertRaises(ValueError):
            workflow.document(self.snapshot,definition,self.root/'document-job',self.root/'publication')
        self.assertEqual(['analysis','analysis-repair'],calls)
        self.assertFalse((self.root/'publication').exists())

    def test_changed_new_manifest_seal_rejects_inflated_lines_and_empty_material(self):
        path=self.snapshot/'manifest.json';value=json.loads(path.read_text())
        value['files'][0]['lines']=999;path.write_text(json.dumps(value))
        with self.assertRaises(ValueError):capsule.verify(self.snapshot)
        value['files']=[];path.write_text(json.dumps(value))
        with self.assertRaises(ValueError):capsule.verify(self.snapshot)

    def legacy(self):
        path=self.snapshot/'manifest.json';value=json.loads(path.read_text())
        value['schema']='reverse-ai-source-capsule/1';path.write_text(json.dumps(value))
        (self.snapshot/'seal.json').unlink()
        return path,value

    def test_legacy_capsule_validates_raw_index_metadata_without_migrating_it(self):
        path,value=self.legacy();before=path.read_bytes()
        state=capsule.verification_state(self.snapshot)
        self.assertIn('legacy-v1',state['scope']);self.assertEqual(before,path.read_bytes())
        self.assertFalse((self.snapshot/'seal.json').exists())
        value['files'][0]['lines']=999;path.write_text(json.dumps(value))
        with self.assertRaises(ValueError):capsule.verify(self.snapshot)

    def test_legacy_mode_absent_is_derived_without_changing_original_manifest(self):
        path,value=self.legacy();del value['mode'];del value['referenceFiles'];path.write_text(json.dumps(value))
        before=path.read_bytes();state=capsule.verification_state(self.snapshot)
        self.assertEqual('source-only',state['mode'])
        self.assertEqual('legacy-v1-explicit-no-references',state['modeDerivation'])
        self.assertEqual(before,path.read_bytes())

    def test_legacy_bind_does_not_invent_starting_hash_provenance(self):
        definition=self.definition()
        self.assertEqual('legacy-job-bind:current-verified-capsule-correspondence-only',definition.handoff['origin'])

    def test_legacy_bytes_encoding_and_indexed_path_must_match_raw(self):
        path,value=self.legacy()
        for field,invalid in (('bytes',7),('encoding','cp936'),('indexed','other.txt')):
            original=value['files'][0][field];value['files'][0][field]=invalid;path.write_text(json.dumps(value))
            with self.assertRaises(ValueError):capsule.verify(self.snapshot)
            value['files'][0][field]=original

    def test_wrong_starting_hash_cannot_recover_plan(self):
        with self.assertRaises(ValueError):workflow.bind_existing_plan(self.snapshot,self.plan_file,'0'*64)
        self.assertFalse((self.root/'plan-verified.json').exists())

    def test_unlisted_source_or_design_addition_is_detected(self):
        extra=self.snapshot/'sources/unlisted.cs';extra.write_text('class Unlisted {}')
        with self.assertRaises(ValueError):capsule.verify(self.snapshot)
        extra.unlink();extra=self.snapshot/'reference-designs/unlisted.md';extra.parent.mkdir()
        extra.write_text('# Unauthorized')
        with self.assertRaises(ValueError):capsule.verify(self.snapshot)

    def test_changed_plan_and_handoff_cannot_be_reused(self):
        definition=self.definition();definition.plan_file.write_text('{}')
        with self.assertRaises(ValueError):workflow._definition_state(self.snapshot,definition)

    def test_bound_plan_cannot_be_used_with_same_named_different_source(self):
        definition=self.definition();other=self.root/'other-source';other.mkdir()
        (other/'Cart.cs').write_text('class Other {}\n')
        snap=self.root/'other-snapshot';capsule.create(other,snap,project_id='synthetic-cart')
        with self.assertRaises(ValueError):workflow._definition_state(snap,definition)

    def test_ai_job_mutating_manifest_cannot_produce_verified_plan(self):
        def changed(*args):
            result=self.fake(*args);path=self.snapshot/'manifest.json'
            value=json.loads(path.read_text());value['projectId']='different';path.write_text(json.dumps(value));return result
        with patch.object(workflow,'run_job',side_effect=changed):
            with self.assertRaises(ValueError):workflow.plan(self.snapshot,self.root/'new-plan')
        self.assertFalse((self.root/'new-plan/plan-verified.json').exists())

    def test_successful_document_has_bound_draft_and_review_hashes(self):
        definition=self.definition();out=self.root/'output'
        with patch.object(workflow,'run_job',side_effect=self.fake):
            draft=workflow.document(self.snapshot,definition,self.root/'jobs',out)
            result=workflow.review(self.snapshot,out/self.doc['path'],definition,self.root/'review')
        self.assertEqual('AI_DRAFT_NOT_YET_INDEPENDENTLY_REVIEWED',draft['status'])
        self.assertTrue(result['approved'])
        handoff=json.loads((self.root/'review/review-handoff.json').read_text())
        self.assertEqual(capsule.sha256((out/self.doc['path']).read_bytes()),handoff['documentSha256'])

    def test_document_change_during_review_cannot_be_approved(self):
        definition=self.definition();file=self.root/'draft.md';file.write_text('# Initial\n')
        def changed(*args):
            result=self.fake(*args);file.write_text('# Different\n');return result
        with patch.object(workflow,'run_job',side_effect=changed):
            with self.assertRaises(ValueError):workflow.review(self.snapshot,file,definition,self.root/'review')
        self.assertFalse((self.root/'review/review-verified.json').exists())

    def test_structural_invalid_draft_kept_but_cannot_be_approved(self):
        definition=self.definition()
        def invalid(*args):
            result=self.fake(*args)
            if args[3]==schemas.DRAFT:result['answer']['content']='# No metadata\n'
            return result
        output=self.root/'output'
        with patch.object(workflow,'run_job',side_effect=invalid):
            draft=workflow.document(self.snapshot,definition,self.root/'jobs',output)
            self.assertEqual('STRUCTURE_INVALID',draft['status'])
            self.assertEqual('# No metadata\n',(output/self.doc['path']).read_text())
            with self.assertRaises(ValueError):
                workflow.review(self.snapshot,output/self.doc['path'],definition,self.root/'review')
        self.assertFalse((self.root/'review/review-verified.json').exists())
        self.assertTrue((self.root/'review/structure-approval-conflict.json').exists())

    def test_empty_draft_is_not_exported(self):
        definition=self.definition()
        def empty(*args):
            result=self.fake(*args)
            if args[3]==schemas.DRAFT:result['answer']['content']=' \n'
            return result
        with patch.object(workflow,'run_job',side_effect=empty):
            with self.assertRaises(ValueError):workflow.document(self.snapshot,definition,self.root/'jobs',self.root/'out')
        self.assertFalse((self.root/'out'/self.doc['path']).exists())

    def test_output_symlink_is_rejected_without_writing_to_target(self):
        definition=self.definition();outside=self.root/'outside';outside.mkdir();link=self.root/'output'
        try:link.symlink_to(outside,target_is_directory=True)
        except OSError:self.skipTest('Host does not permit directory symlinks')
        with patch.object(workflow,'run_job',side_effect=self.fake):
            with self.assertRaises(ValueError):workflow.document(self.snapshot,definition,self.root/'jobs',link)
        self.assertFalse((outside/self.doc['path']).exists())

    def test_existing_output_is_never_overwritten_or_sent_to_ai(self):
        definition=self.definition();out=self.root/'output';target=out/self.doc['path']
        target.parent.mkdir(parents=True);target.write_text('# Existing\n')
        with patch.object(workflow,'run_job') as job:
            with self.assertRaises(FileExistsError):workflow.document(self.snapshot,definition,self.root/'jobs',out)
        job.assert_not_called();self.assertEqual('# Existing\n',target.read_text())

    def test_timeout_reserves_thirty_seconds_before_absolute_deadline(self):
        deadline=datetime.now(timezone.utc)+timedelta(seconds=90)
        allowance=workflow._timeout(1800,deadline)
        self.assertGreater(allowance,55);self.assertLessEqual(allowance,60)

    def test_deadline_recomputed_before_each_ai_call(self):
        definition=self.definition();past=datetime.now(timezone.utc)-timedelta(seconds=1)
        with patch.object(workflow,'run_job') as job:
            with self.assertRaisesRegex(RuntimeError,'RuntimeErrorTimeLimit'):
                workflow.document(self.snapshot,definition,self.root/'jobs',self.root/'out',deadline=past)
        job.assert_not_called()

    def test_expiring_deadline_after_analysis_prevents_draft(self):
        definition=self.definition();now=datetime.now(timezone.utc);deadline=now+timedelta(seconds=90)
        with patch.object(workflow,'run_job',side_effect=self.fake) as job, patch.object(workflow,'datetime') as clock:
            clock.now.side_effect=[now,deadline-timedelta(seconds=15)]
            # Pass a real datetime; the clock mock affects only the current time.
            clock.fromisoformat.side_effect=datetime.fromisoformat
            with patch.object(workflow,'_timeout',side_effect=[60,RuntimeError('RuntimeErrorTimeLimit')]):
                with self.assertRaisesRegex(RuntimeError,'RuntimeErrorTimeLimit'):
                    workflow.document(self.snapshot,definition,self.root/'jobs',self.root/'out',deadline=deadline)
        self.assertEqual(1,job.call_count)


if __name__=='__main__':unittest.main()

"""Synthetic routing and tampering tests; no reference specifications or real AI."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from contextbase.ai import batch, capsule, document_contract as contracts, iteration, schemas, workflow
from contextbase.ai import __main__ as cli


class DocumentContractTests(unittest.TestCase):
    def setUp(self):
        home = Path(__file__).resolve().parents[3] / '.tmp'
        home.mkdir(exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(prefix='document-contract-', dir=home)
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        source = self.root / 'source'; source.mkdir()
        (source / 'Entry.cs').write_text('class Entry {}\n', encoding='utf-8')
        (source / 'Dependency.cs').write_text('class Dependency {}\n', encoding='utf-8')
        self.snapshot = self.root / 'snapshot'
        self.manifest = capsule.create(source, self.snapshot, project_id='synthetic-routing')
        self.contract = {'schema': 'reverse-ai-document-contract/1', 'projectId': 'synthetic-routing',
                         'documents': [{'id': 'DOC-01', 'kind': 'detailed-specification',
                                        'path': '詳細仕様書/01_原本と同じ名前.md', 'sourcePaths': ['Entry.cs']}]}
        self.contract_file = self.root / 'routing.json'
        self.original = (json.dumps(self.contract, ensure_ascii=False, indent=4) + '\n').encode('utf-8')
        self.contract_file.write_bytes(self.original)
        self.plan = {'systemSummary': 'Synthetic source discovery', 'unresolved': [], 'documents': [
            {**self.contract['documents'][0], 'title': 'AI-authored title',
             'sourcePaths': ['indexed/Entry.cs.txt', 'sources/Dependency.cs'],
             'responsibilities': ['AI source discovery, not a user business expectation']}]}
        self.job = self.root / 'plan-job'

    def fake(self, workspace, job, prompt, schema, timeout):
        job.mkdir(parents=True)
        self.assertIn('ユーザー指定の文書対応契約', prompt)
        value = copy.deepcopy(self.plan)
        (job / 'answer.txt').write_text(json.dumps(value, ensure_ascii=False), encoding='utf-8')
        return {'exit_code': 0, 'metadata': {'status': 'passed'}, 'answer': value}

    def run_plan(self):
        with patch.object(workflow, 'run_job', side_effect=self.fake):
            return workflow.plan(self.snapshot, self.job, document_contract=self.contract_file)

    def test_contract_accepts_only_routing_not_business_expectations(self):
        contracts.validate(self.contract, self.manifest)
        for field, value in (('title', 'Expected prose'), ('responsibilities', ['Expected conditions']),
                             ('expectedScore', 95), ('tableFields', ['Expected business field'])):
            changed = copy.deepcopy(self.contract)
            changed['documents'][0][field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                contracts.validate(changed, self.manifest)

    def test_project_scope_must_match_the_sealed_capsule(self):
        changed = {**self.contract, 'projectId': 'different-project'}
        with self.assertRaises(ValueError): contracts.validate(changed, self.manifest)

    def test_case_insensitive_ids_and_windows_paths_are_unique(self):
        for replacement in ({'id': 'doc-01', 'path': 'different.md'},
                            {'id': 'DOC-02', 'path': '詳細仕様書/01_原本と同じ名前.MD'}):
            changed = copy.deepcopy(self.contract)
            changed['documents'].append({**changed['documents'][0], **replacement})
            with self.subTest(replacement=replacement), self.assertRaises(ValueError):
                contracts.validate(changed, self.manifest)

    def test_unsafe_paths_empty_entries_and_aliases_are_rejected_before_ai(self):
        for field, value in (('path', '../original.md'), ('path', 'folder/NUL.md'),
                             ('id', ''), ('kind', '  '), ('sourcePaths', []),
                             ('sourcePaths', ['sources/Entry.cs']), ('sourcePaths', ['unknown.cs'])):
            changed = copy.deepcopy(self.contract)
            changed['documents'][0][field] = value
            self.contract_file.write_text(json.dumps(changed), encoding='utf-8')
            with self.subTest(field=field, value=value), patch.object(workflow, 'run_job') as provider:
                with self.assertRaises(ValueError):
                    workflow.plan(self.snapshot, self.job, document_contract=self.contract_file)
                provider.assert_not_called()

    def test_exact_original_paths_and_kinds_allow_discovered_dependency_sources(self):
        workflow._validate_plan(self.plan, self.manifest, self.contract)
        self.run_plan()
        self.assertEqual(self.original, self.contract_file.read_bytes())
        self.assertEqual(self.original, (self.job / contracts.FILENAME).read_bytes())
        definition = workflow.select_document(self.job / 'plan-verified.json', 'DOC-01')
        self.assertEqual(self.plan['documents'][0], dict(definition))
        workflow._definition_state(self.snapshot, definition)
        self.assertEqual(capsule.sha256(self.original), definition.handoff['documentContract']['sha256'])
        self.assertIn('ユーザー指定の文書対応契約', workflow._document_context(self.snapshot, definition))

    def test_missing_additional_renamed_and_kind_changed_documents_are_rejected(self):
        variants = []
        missing = copy.deepcopy(self.plan); missing['documents'] = []; variants.append(missing)
        extra = copy.deepcopy(self.plan); extra['documents'].append({**extra['documents'][0], 'id': 'EXTRA', 'path': 'extra.md'}); variants.append(extra)
        for field, value in (('id', 'RENAMED'), ('path', 'renamed.md'), ('kind', 'common')):
            changed = copy.deepcopy(self.plan); changed['documents'][0][field] = value; variants.append(changed)
        for value in variants:
            with self.subTest(value=value), self.assertRaises(ValueError):
                workflow._validate_plan(value, self.manifest, self.contract)

    def test_plan_cannot_drop_the_required_source_entry(self):
        changed = copy.deepcopy(self.plan)
        changed['documents'][0]['sourcePaths'] = ['Dependency.cs', 'manifest.json']
        with self.assertRaises(ValueError): workflow._validate_plan(changed, self.manifest, self.contract)

    def test_invalid_ai_plan_is_preserved_without_a_verified_handoff(self):
        self.plan['documents'][0]['path'] = 'AI-renamed.md'
        with self.assertRaises(ValueError): self.run_plan()
        self.assertTrue((self.job / 'answer.txt').is_file())
        self.assertTrue((self.job / 'plan-validation-failure.json').is_file())
        self.assertEqual(self.original, (self.job / contracts.FILENAME).read_bytes())
        self.assertFalse((self.job / 'plan-verified.json').exists())
        self.assertFalse((self.job / 'plan-handoff.json').exists())

    def test_external_contract_mutation_during_ai_plan_is_rejected(self):
        def mutate(*args):
            result = self.fake(*args)
            self.contract_file.write_bytes(self.original + b' ')
            return result
        with patch.object(workflow, 'run_job', side_effect=mutate), self.assertRaises(ValueError):
            workflow.plan(self.snapshot, self.job, document_contract=self.contract_file)
        self.assertFalse((self.job / 'plan-verified.json').exists())

    def test_bound_contract_change_or_removal_is_rejected_in_later_phases(self):
        self.run_plan()
        plan_file = self.job / 'plan-verified.json'
        definition = workflow.select_document(plan_file, 'DOC-01')
        pinned = self.job / contracts.FILENAME
        pinned.write_bytes(self.original + b' ')
        with self.assertRaises(ValueError): workflow._definition_state(self.snapshot, definition)
        with self.assertRaises(ValueError): workflow.select_document(plan_file, 'DOC-01')
        pinned.unlink()
        with self.assertRaises(OSError): workflow._definition_state(self.snapshot, definition)

    def test_contract_cannot_be_detached_from_its_handoff(self):
        self.run_plan()
        path = self.job / 'plan-handoff.json'
        value = capsule._load_json(path); del value['documentContract']
        path.write_text(json.dumps(value), encoding='utf-8')
        with self.assertRaises(ValueError): workflow.select_document(self.job / 'plan-verified.json', 'DOC-01')

    def test_plan_job_root_cannot_overlap_the_snapshot(self):
        state = capsule.verification_state(self.snapshot)
        for job in (self.snapshot, self.snapshot / 'new-plan', self.root):
            with self.subTest(job=job), patch.object(workflow, 'run_job') as provider:
                with self.assertRaises(ValueError):
                    workflow.plan(self.snapshot, job, document_contract=self.contract_file)
                provider.assert_not_called()
        self.assertFalse((self.snapshot / 'new-plan').exists())
        self.assertEqual(state, capsule.verification_state(self.snapshot))

    def test_document_output_and_job_roots_cannot_overlap_the_snapshot(self):
        self.run_plan()
        definition = workflow.select_document(self.job / 'plan-verified.json', 'DOC-01')
        state = capsule.verification_state(self.snapshot)
        for output in (self.snapshot, self.snapshot / 'new-output', self.root):
            with self.subTest(output=output), patch.object(workflow, 'run_job') as provider:
                with self.assertRaises(ValueError):
                    workflow.document(self.snapshot, definition, self.root / 'new-document-job', output)
                provider.assert_not_called()
        for job in (self.snapshot, self.snapshot / 'new-job', self.root):
            with self.subTest(job=job), patch.object(workflow, 'run_job') as provider:
                with self.assertRaises(ValueError):
                    workflow.document(self.snapshot, definition, job, self.root / 'new-output')
                provider.assert_not_called()
        self.assertFalse((self.snapshot / 'new-output').exists())
        self.assertFalse((self.snapshot / 'new-job').exists())
        self.assertEqual(state, capsule.verification_state(self.snapshot))

    def test_batch_and_iteration_refuse_overlap_before_creating_artifacts(self):
        self.run_plan()
        plan = self.job / 'plan-verified.json'
        state = capsule.verification_state(self.snapshot)
        for job, output in ((self.snapshot / 'job', self.root / 'output'),
                            (self.root / 'job', self.snapshot / 'output'),
                            (self.root / 'job', self.root)):
            for stage in ('batch', 'iterate'):
                with self.subTest(stage=stage, job=job, output=output), patch.object(workflow, 'run_job') as provider:
                    with self.assertRaises(ValueError):
                        if stage == 'batch':
                            batch.run(self.snapshot, plan, job, output)
                        else:
                            iteration.run(self.snapshot, plan, 'DOC-01', job, output)
                    provider.assert_not_called()
        self.assertFalse((self.snapshot / 'job').exists())
        self.assertFalse((self.snapshot / 'output').exists())
        self.assertFalse((self.root / 'job').exists())
        self.assertEqual(state, capsule.verification_state(self.snapshot))

    def test_contract_kind_enforces_feature_structure_through_draft_and_review(self):
        self.run_plan()
        definition = workflow.select_document(self.job / 'plan-verified.json', 'DOC-01')
        metadata = {'schema': 'spec-md/1.0', 'documentId': 'DOC-01', 'version': 'synthetic-1',
                    'path': definition['path'], 'sheets': [{'heading': '概要', 'kind': 'GRID', 'sheet': '概要'}]}
        # Valid generic Markdown deliberately lacks required feature chapters/events.
        content = '<!-- spec-meta: ' + json.dumps(metadata, ensure_ascii=False) + ' -->\n# Synthetic\n\n## 概要\n\nSynthetic description.\n'
        def stages(workspace, job, prompt, schema, timeout):
            job.mkdir(parents=True)
            if schema == schemas.ANALYSIS:
                value = {'documentId': 'DOC-01', 'sourcePathsRead': ['Entry.cs'], 'unresolved': [],
                         'coverageNotes': ['Synthetic fixture'], 'facts': [{'id': 'F-01', 'topic': 'Declaration',
                         'statement': 'Entry is declared.', 'basis': 'observed-source',
                         'references': [{'path': 'Entry.cs', 'startLine': 1, 'endLine': 1}]}]}
            elif schema == schemas.DRAFT:
                value = {'documentId': 'DOC-01', 'path': definition['path'], 'content': content,
                         'factCorrections': [], 'unresolved': []}
            else:
                value = {'documentId': 'DOC-01', 'approved': True, 'findings': [], 'unresolved': []}
            return {'exit_code': 0, 'metadata': {'status': 'passed'}, 'answer': value}
        output = self.root / 'output'
        with patch.object(workflow, 'run_job', side_effect=stages):
            result = workflow.document(self.snapshot, definition, self.root / 'document-job', output)
            self.assertEqual('STRUCTURE_INVALID', result['status'])
            self.assertIn('FEATURE_CHAPTERS', {item['code'] for item in result['structureFindings']})
            with self.assertRaises(workflow.ReviewStructureConflict):
                workflow.review(self.snapshot, output / definition['path'], definition, self.root / 'review-job')
        self.assertEqual(content, (output / definition['path']).read_text(encoding='utf-8'))
        self.assertFalse((self.root / 'review-job/review-handoff.json').exists())

    def test_cli_forwards_contract_only_to_plan(self):
        arguments = ['plan', '--snapshot', str(self.snapshot), '--job', str(self.job),
                     '--document-contract', str(self.contract_file)]
        with patch('contextbase.ai.workflow.plan', return_value={}) as stage:
            self.assertEqual(0, cli.main(arguments))
        self.assertEqual(self.contract_file, stage.call_args.kwargs['document_contract'])
        with self.assertRaises(SystemExit): cli.main(['review', *arguments[1:]])


if __name__ == '__main__':
    unittest.main()

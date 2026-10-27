"""Synthetic plan assessment boundaries, not a score of real AI decisions."""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from contextbase.ai import capsule, plan_review, workflow


class PlanReviewTests(unittest.TestCase):
    def setUp(self):
        temporary = Path(__file__).resolve().parents[3] / '.tmp'
        temporary.mkdir(exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(prefix='ai-plan-review-', dir=temporary)
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / 'source'
        self.source.mkdir()
        (self.source / 'Gallery.py').write_bytes(b'def browse():\r\n    return []\r\n')
        (self.source / 'startup.py').write_bytes(b'from Gallery import browse\nroute = browse\n')
        self.snapshot = self.root / 'snapshot'
        capsule.create(self.source, self.snapshot, project_id='synthetic-gallery')
        self.doc = {'id': 'GALLERY', 'path': 'spec/gallery.md', 'title': '人工ギャラリー',
                    'kind': 'feature', 'sourcePaths': ['sources/Gallery.py', 'startup.py'],
                    'responsibilities': ['人工入力を確認する']}
        self.plan = {'systemSummary': '人工レビューfixture', 'documents': [self.doc], 'unresolved': []}
        self.plan_bytes = json.dumps(self.plan, ensure_ascii=False, indent=4).encode('utf-8')
        self.plan_file = self.root / 'original-plan.json'
        self.plan_file.write_bytes(self.plan_bytes)
        self.bind(self.snapshot)
        self.answer = self.review_value()
        self.calls = []

    def bind(self, snapshot):
        state = capsule.verification_state(snapshot)
        bound = workflow.bind_existing_plan(snapshot, self.plan_file, state['manifestSha256'])
        self.bound_plan = Path(bound['planFile'])

    def ref(self, path='sources/Gallery.py', line=1):
        return {'path': path, 'startLine': line, 'endLine': line}

    def review_value(self):
        return {
            'schema': 'reverse-ai-plan-review/1', 'referenceMode': 'source-only', 'approved': True,
            'sourcePathsRead': ['sources/Gallery.py', 'startup.py', 'manifest.json'],
            'subjects': [{'id': 'SUB-1', 'kind': 'feature', 'name': '人工閲覧',
                          'basis': 'observed-source', 'references': [self.ref()],
                          'sourcePaths': ['indexed/Gallery.py.txt'], 'documentIds': ['GALLERY']}],
            'documentCoverage': [{'documentId': 'GALLERY', 'path': 'spec/gallery.md', 'subjectIds': ['SUB-1'],
                                  'status': 'covered', 'basis': 'plan-structure',
                                  'rationale': '人工計画と対象が対応する', 'references': []}],
            'reachability': [{'id': 'REACH-1', 'subjectIds': ['SUB-1'], 'entryPoints': [], 'callers': [],
                              'registrations': [], 'searchScope': ['Gallery.py'], 'status': 'declaration-only',
                              'basis': 'observed-source', 'explanation': 'この人工応答は宣言だけを述べる',
                              'references': [self.ref()]}],
            'findings': [], 'blockingUnresolved': [], 'scopeLimits': [],
        }

    def fake_job(self, workspace, job, prompt, schema, timeout):
        self.calls.append({'workspace': workspace, 'job': job, 'prompt': prompt, 'schema': schema, 'timeout': timeout})
        job.mkdir(parents=True)
        self.returned_answer = deepcopy(self.answer)
        self.raw_answer = (' \n' + json.dumps(self.returned_answer, ensure_ascii=False, indent=6) + '\n\n').encode('utf-8')
        (job / 'answer.txt').write_bytes(self.raw_answer)
        return {'answer': self.returned_answer, 'exit_code': 0, 'metadata': {'status': 'passed'}}

    def invoke(self, **kwargs):
        with patch.object(workflow, 'run_job', side_effect=self.fake_job):
            return plan_review.run(self.snapshot, self.bound_plan, self.root / 'review-job', **kwargs)

    def refused(self):
        with self.assertRaises(ValueError):
            self.invoke()
        self.assertFalse((self.root / 'review-job/plan-review-verified.json').exists())
        self.assertFalse((self.root / 'review-job/plan-review-handoff.json').exists())
        self.assertTrue((self.root / 'review-job/answer.txt').is_file())

    def test_original_plan_and_ai_json_bytes_are_preserved(self):
        answer = self.invoke()
        job = self.root / 'review-job'
        self.assertIs(answer, self.returned_answer)
        self.assertEqual(self.raw_answer, (job / 'answer.txt').read_bytes())
        self.assertEqual(self.raw_answer, (job / 'plan-review-verified.json').read_bytes())
        self.assertEqual(self.plan_bytes, self.plan_file.read_bytes())
        self.assertEqual(self.plan_bytes, self.bound_plan.read_bytes())
        handoff = json.loads((job / 'plan-review-handoff.json').read_text(encoding='utf-8'))
        self.assertEqual(capsule.sha256(self.plan_bytes), handoff['planSha256'])
        self.assertEqual(capsule.sha256(self.raw_answer), handoff['reviewSha256'])
        self.assertFalse(handoff['aiResponseBytesModified'])
        self.assertIn('not-formal-business-rubric', handoff['scope'])
        self.assertEqual('legacy-job-bind:current-verified-capsule-correspondence-only', handoff['planOrigin'])

    def test_unapproved_review_is_preserved_without_synthetic_pass(self):
        self.answer['approved'] = False
        self.answer['blockingUnresolved'] = [{'id': 'Q', 'question': '人工不明', 'documentIds': ['GALLERY'],
                                              'subjectIds': ['SUB-1'], 'basis': 'plan-structure', 'references': []}]
        answer = self.invoke()
        self.assertFalse(answer['approved'])
        self.assertEqual(self.answer, answer)

    def test_documented_scope_limit_is_separate_from_blocking_unknown(self):
        self.answer['scopeLimits'] = [{'id': 'L', 'limitation': '外部環境を含まない人工範囲',
                                      'sourcePaths': ['manifest.json'], 'documentIds': ['GALLERY'],
                                      'basis': 'plan-structure', 'references': []}]
        self.assertTrue(self.invoke()['approved'])

    def test_whole_plan_and_long_literal_are_supplied_without_truncation(self):
        # A new bound plan contains a long neutral string, not an expected answer.
        other = self.root / 'long'; other.mkdir()
        plan = deepcopy(self.plan)
        text = ' leading  spaces true null 00042 ' * 500
        plan['documents'][0]['responsibilities'] = [text]
        original = other / 'answer.txt'
        original.write_text(json.dumps(plan, ensure_ascii=False, indent=4), encoding='utf-8')
        bound = workflow.bind_existing_plan(self.snapshot, original,
                                             capsule.verification_state(self.snapshot)['manifestSha256'])
        self.bound_plan = Path(bound['planFile'])
        self.invoke()
        self.assertIn(original.read_bytes().decode('utf-8'), self.calls[0]['prompt'])
        self.assertIn(text, self.calls[0]['prompt'])
        self.assertNotIn(str(self.bound_plan), self.calls[0]['prompt'])

    def test_alias_references_resolve_to_exact_source_and_read_scope(self):
        self.answer['subjects'][0]['references'] = [self.ref('indexed/Gallery.py.txt', 2)]
        self.assertTrue(self.invoke()['approved'])

    def test_reference_design_intent_is_allowed_only_in_assisted_snapshot(self):
        directory = self.root / 'design'; directory.mkdir()
        (directory / 'intent.md').write_text('# 人工意図\n', encoding='utf-8')
        assisted = self.root / 'assisted'
        manifest = capsule.create(self.source, assisted, project_id='synthetic-gallery',
                                  authorized_reference_directories=(directory,))
        plan_root = self.root / 'assisted-plan'; plan_root.mkdir()
        original = plan_root / 'answer.txt'; original.write_bytes(self.plan_bytes)
        bound = workflow.bind_existing_plan(assisted, original, capsule.verification_state(assisted)['manifestSha256'])
        self.snapshot = assisted; self.bound_plan = Path(bound['planFile'])
        path = manifest['referenceFiles'][0]['path']
        self.answer['referenceMode'] = 'training-assisted'
        self.answer['sourcePathsRead'].append(path)
        subject = self.answer['subjects'][0]
        subject['basis'] = 'reference-design'; subject['references'] = [self.ref(path)]
        subject['sourcePaths'] = [path]
        self.assertTrue(self.invoke()['approved'])

    def test_reference_basis_requires_authorized_design_not_just_source(self):
        self.answer['subjects'][0]['basis'] = 'reference-design'
        self.refused()

    def test_reference_design_cannot_establish_observed_source(self):
        self.answer['subjects'][0]['references'] = [self.ref('reference-designs/imaginary.md')]
        self.refused()

    def test_authorized_design_still_cannot_be_observed_implementation(self):
        directory = self.root / 'design'; directory.mkdir()
        (directory / 'intent.md').write_text('# 人工意図\n', encoding='utf-8')
        assisted = self.root / 'assisted'
        manifest = capsule.create(self.source, assisted, project_id='synthetic-gallery',
                                  authorized_reference_directories=(directory,))
        plan_root = self.root / 'assisted-plan'; plan_root.mkdir()
        original = plan_root / 'answer.txt'; original.write_bytes(self.plan_bytes)
        bound = workflow.bind_existing_plan(assisted, original, capsule.verification_state(assisted)['manifestSha256'])
        self.snapshot = assisted; self.bound_plan = Path(bound['planFile'])
        path = manifest['referenceFiles'][0]['path']
        self.answer['referenceMode'] = 'training-assisted'; self.answer['sourcePathsRead'].append(path)
        self.answer['subjects'][0]['references'] = [self.ref(path)]
        self.answer['subjects'][0]['sourcePaths'] = [path]
        self.refused()

    def test_reference_mode_cannot_be_relabelled(self):
        self.answer['referenceMode'] = 'training-assisted'
        self.refused()

    def test_manifest_cannot_establish_business_subject(self):
        self.answer['subjects'][0]['references'] = [self.ref('manifest.json')]
        self.refused()

    def test_line_bounds_and_boolean_line_numbers_are_refused(self):
        self.answer['subjects'][0]['references'] = [self.ref(line=999)]
        self.refused()

    def test_schema_refuses_boolean_as_source_line(self):
        self.answer['subjects'][0]['references'] = [self.ref(line=True)]
        self.refused()

    def test_unknown_document_id_is_not_fuzzy_matched(self):
        self.answer['subjects'][0]['documentIds'] = ['gallery']
        self.refused()

    def test_coverage_output_path_must_match_original_plan_exactly(self):
        self.answer['documentCoverage'][0]['path'] = 'spec/elsewhere.md'
        self.refused()

    def test_every_planned_document_is_assessed_exactly_once(self):
        self.answer['documentCoverage'].append(deepcopy(self.answer['documentCoverage'][0]))
        self.refused()

    def test_subject_ids_are_unique(self):
        self.answer['subjects'].append(deepcopy(self.answer['subjects'][0]))
        self.refused()

    def test_coverage_subject_links_are_bidirectional(self):
        self.answer['subjects'][0]['documentIds'] = []
        self.refused()

    def test_unknown_subject_cannot_be_claimed_as_covered(self):
        self.answer['documentCoverage'][0]['subjectIds'] = ['unknown']
        self.refused()

    def test_unknown_read_path_is_refused(self):
        self.answer['sourcePathsRead'].append('../another/source.py')
        self.refused()

    def test_subject_evidence_must_belong_to_related_and_read_materials(self):
        self.answer['subjects'][0]['sourcePaths'] = ['startup.py']
        self.refused()

    def test_claimed_evidence_cannot_be_omitted_from_read_scope(self):
        self.answer['sourcePathsRead'] = ['startup.py']
        self.refused()

    def test_scoped_not_found_is_preserved_without_claiming_absolute_unused(self):
        self.answer['reachability'][0]['status'] = 'not-found-in-included-scope'
        result = self.invoke()
        self.assertEqual('not-found-in-included-scope', result['reachability'][0]['status'])
        self.assertEqual(['Gallery.py'], result['reachability'][0]['searchScope'])

    def test_reachability_conclusion_requires_search_scope(self):
        self.answer['reachability'][0]['searchScope'] = []
        self.refused()

    def test_confirmed_reachability_requires_source_observed_entry(self):
        self.answer['reachability'][0]['status'] = 'confirmed'
        self.refused()

    def test_confirmed_reachability_can_use_source_entry_evidence(self):
        item = self.answer['reachability'][0]
        item['status'] = 'confirmed'; item['searchScope'].append('startup.py')
        item['entryPoints'] = [{'name': '人工登録', 'basis': 'observed-source',
                                'references': [self.ref('startup.py', 2)]}]
        self.assertEqual('confirmed', self.invoke()['reachability'][0]['status'])

    def test_reachability_evidence_cannot_exceed_declared_search_scope(self):
        self.answer['reachability'][0]['references'] = [self.ref('startup.py', 2)]
        self.refused()

    def test_unknown_reachability_is_not_forced_to_a_source_conclusion(self):
        item = self.answer['reachability'][0]
        item['status'] = 'unknown'; item['basis'] = 'plan-structure'
        item['references'] = []; item['searchScope'] = []
        self.assertEqual('unknown', self.invoke()['reachability'][0]['status'])

    def test_major_findings_cannot_be_approved(self):
        self.answer['findings'] = [{'id': 'F', 'severity': 'major', 'documentIds': ['GALLERY'],
                                   'subjectIds': ['SUB-1'], 'location': '計画', 'defect': '人工欠落',
                                   'repairDirection': 'AIが原文を再確認する', 'basis': 'plan-structure', 'references': []}]
        self.refused()

    def test_blocking_unknown_cannot_be_approved(self):
        self.answer['blockingUnresolved'] = [{'id': 'Q', 'question': '人工不明', 'documentIds': [],
                                              'subjectIds': [], 'basis': 'plan-structure', 'references': []}]
        self.refused()

    def test_provider_failure_never_generates_a_verified_review(self):
        def failed(*args):
            result = self.fake_job(*args); result['metadata']['status'] = 'timeout'; return result
        with patch.object(workflow, 'run_job', side_effect=failed), self.assertRaises(RuntimeError):
            plan_review.run(self.snapshot, self.bound_plan, self.root / 'review-job')
        self.assertFalse((self.root / 'review-job/plan-review-verified.json').exists())
        self.assertTrue((self.root / 'review-job/answer.txt').is_file())

    def test_expired_deadline_starts_no_ai_job(self):
        deadline = datetime.now(timezone.utc) - timedelta(seconds=1)
        with patch.object(workflow, 'run_job') as job, self.assertRaisesRegex(RuntimeError, 'RuntimeErrorTimeLimit'):
            plan_review.run(self.snapshot, self.bound_plan, self.root / 'review-job', deadline=deadline)
        job.assert_not_called()

    def test_deadline_is_forwarded_and_thirty_seconds_reserved(self):
        deadline = datetime.now(timezone.utc) + timedelta(seconds=90)
        self.invoke(timeout=1800, deadline=deadline.isoformat())
        self.assertGreater(self.calls[0]['timeout'], 50)
        self.assertLessEqual(self.calls[0]['timeout'], 60)

    def test_timezone_free_deadline_is_refused_before_ai_job(self):
        with patch.object(workflow, 'run_job') as job, self.assertRaises(ValueError):
            plan_review.run(self.snapshot, self.bound_plan, self.root / 'review-job', deadline='2099-01-01T00:00:00')
        job.assert_not_called()

    def test_plan_change_during_job_is_rejected_without_overwriting_plan(self):
        def changed(*args):
            result = self.fake_job(*args)
            self.bound_plan.write_bytes(self.plan_bytes + b'\n')
            return result
        with patch.object(workflow, 'run_job', side_effect=changed), self.assertRaises(ValueError):
            plan_review.run(self.snapshot, self.bound_plan, self.root / 'review-job')
        self.assertEqual(self.plan_bytes + b'\n', self.bound_plan.read_bytes())
        self.assertFalse((self.root / 'review-job/plan-review-handoff.json').exists())

    def test_snapshot_change_during_job_is_rejected(self):
        def changed(*args):
            result = self.fake_job(*args)
            (self.snapshot / 'sources/Gallery.py').write_bytes(b'different\n')
            return result
        with patch.object(workflow, 'run_job', side_effect=changed), self.assertRaises(ValueError):
            plan_review.run(self.snapshot, self.bound_plan, self.root / 'review-job')
        self.assertFalse((self.root / 'review-job/plan-review-handoff.json').exists())

    def test_changed_handoff_is_rejected(self):
        def changed(*args):
            result = self.fake_job(*args)
            file = self.bound_plan.parent / 'plan-handoff.json'
            file.write_bytes(file.read_bytes() + b'\n')
            return result
        with patch.object(workflow, 'run_job', side_effect=changed), self.assertRaises(ValueError):
            plan_review.run(self.snapshot, self.bound_plan, self.root / 'review-job')
        self.assertFalse((self.root / 'review-job/plan-review-handoff.json').exists())

    def test_existing_job_and_capsule_child_job_are_refused(self):
        existing = self.root / 'existing'; existing.mkdir()
        with patch.object(workflow, 'run_job') as job:
            with self.assertRaises(FileExistsError):
                plan_review.run(self.snapshot, self.bound_plan, existing)
            with self.assertRaises(ValueError):
                plan_review.run(self.snapshot, self.bound_plan, self.snapshot / 'new-job')
        job.assert_not_called()

    def test_unbound_plan_is_refused_before_ai_job(self):
        other = self.root / 'unbound'; other.mkdir()
        file = other / 'plan.json'; file.write_bytes(self.plan_bytes)
        with patch.object(workflow, 'run_job') as job, self.assertRaises(ValueError):
            plan_review.run(self.snapshot, file, self.root / 'review-job')
        job.assert_not_called()

    def test_linked_output_job_is_refused_before_ai_job(self):
        outside = self.root / 'outside'; outside.mkdir()
        link = self.root / 'linked-job'
        try:
            link.symlink_to(outside, target_is_directory=True)
        except OSError:
            self.skipTest('Host does not permit directory symlinks')
        with patch.object(workflow, 'run_job') as job, self.assertRaises(ValueError):
            plan_review.run(self.snapshot, self.bound_plan, link)
        job.assert_not_called()
        self.assertEqual([], list(outside.iterdir()))

    def test_subject_categories_are_not_fixed_to_a_business_dictionary(self):
        self.answer['subjects'][0]['kind'] = 'resource-observation'
        self.answer['subjects'][0]['name'] = '原文の任意の責務'
        result = self.invoke()
        self.assertEqual('resource-observation', result['subjects'][0]['kind'])

    def test_original_response_must_equal_returned_json(self):
        def changed(*args):
            result = self.fake_job(*args)
            result['answer']['approved'] = False
            return result
        with patch.object(workflow, 'run_job', side_effect=changed), self.assertRaises(ValueError):
            plan_review.run(self.snapshot, self.bound_plan, self.root / 'review-job')
        self.assertFalse((self.root / 'review-job/plan-review-verified.json').exists())


if __name__ == '__main__':
    unittest.main()

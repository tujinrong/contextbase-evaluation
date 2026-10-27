"""Synthetic critique orchestration tests; these do not measure AI prose quality."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from contextbase.ai import capsule, iteration, workflow


class IterationTests(unittest.TestCase):
    def setUp(self):
        temporary_root = Path(__file__).resolve().parents[3] / '.tmp'
        temporary_root.mkdir(exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(prefix='ai-iteration-', dir=temporary_root)
        self.root = Path(self.temp.name)
        source = self.root / 'source'
        source.mkdir()
        (source / 'main.py').write_text('value = 7\n', encoding='utf-8')
        self.snapshot = self.root / 'snapshot'
        capsule.create(source, self.snapshot, project_id='synthetic')
        self.definition = {'id': 'D', 'path': 'spec/detail.md', 'kind': 'detail'}
        self.contexts = []
        self.contents = []

    def tearDown(self):
        self.temp.cleanup()

    def draft(self, snapshot, definition, job, output, **kwargs):
        self.contexts.append(kwargs.get('revision_context'))
        content = f'# AI fixture round {len(self.contexts)}\n本文 {len(self.contexts)}\n'
        self.contents.append(content)
        target = output / definition['path']
        target.parent.mkdir(parents=True)
        target.write_text(content, encoding='utf-8', newline='\n')
        return {'contentSha256': capsule.sha256(content.encode('utf-8')), 'structureFindings': []}

    def invoke(self, review, **options):
        with patch('contextbase.ai.workflow.select_document', return_value=self.definition), \
             patch('contextbase.ai.workflow._definition_state', return_value=capsule.verification_state(self.snapshot)), \
             patch('contextbase.ai.workflow.document', side_effect=self.draft), \
             patch('contextbase.ai.workflow.review', side_effect=review):
            return iteration.run(self.snapshot, self.root/'plan.json', 'D', self.root/'jobs',
                                 self.root/'output', **options)

    def test_critique_is_data_and_previous_round_remains_immutable(self):
        critique = {'approved': False, 'findings': [{'defect': 'fixture issue'}], 'unresolved': []}
        result = self.invoke([critique, {'approved': True, 'findings': [], 'unresolved': []}])
        self.assertEqual(result['status'], 'INDEPENDENT_REVIEW_APPROVED')
        self.assertEqual(len(result['rounds']), 2)
        first = self.root/'output/round-01/spec/detail.md'
        self.assertEqual(first.read_text(encoding='utf-8'), self.contents[0])
        self.assertIsNone(self.contexts[0])
        self.assertEqual(self.contexts[1]['previousDraft'], self.contents[0])
        self.assertEqual(self.contexts[1]['previousIndependentReview'], critique)
        self.assertFalse(result['formallyEvaluatedByOriginalRubric'])
        self.assertFalse(result['semanticProseAssembledByPython'])
        self.assertIn('round-02', result['selectedDocument'])

    def test_unapproved_rounds_do_not_become_a_pass(self):
        result = self.invoke([{'approved': False, 'findings': [], 'unresolved': ['unknown']}]*2, max_rounds=2)
        self.assertEqual(result['status'], 'REQUIRES_AI_REVISION')
        self.assertIsNone(result['selectedDocument'])

    def test_text_approval_ends_iteration_without_claiming_image_or_formal_acceptance(self):
        answer={'approved':True,'findings':[],'unresolved':[]}
        result=self.invoke([answer])
        self.assertEqual('INDEPENDENT_REVIEW_APPROVED',result['status'])
        self.assertEqual(1,len(result['rounds']))
        self.assertTrue(Path(result['selectedDocument']).is_file())
        self.assertEqual('text-source-and-structure',result['reviewScope'])
        self.assertFalse(result['visualFidelityVerified'])
        self.assertFalse(result['formallyEvaluatedByOriginalRubric'])
        record=result['rounds'][0]
        self.assertTrue(record['approvalAccepted'])
        self.assertEqual(answer,record['review'])
        self.assertEqual('text-source-and-structure',record['reviewScope'])
        self.assertFalse(record['visualFidelityVerified'])
        self.assertFalse(record['formallyEvaluatedByOriginalRubric'])
        self.assertEqual(result,json.loads((self.root/'jobs/iteration-result.json').read_text()))

    def test_revisions_reuse_completed_analysis_but_keep_the_critique(self):
        original = self.draft
        used = []
        def checkpointed(snapshot, definition, job, output, **options):
            used.append(options.get('analysis_job'))
            answer = original(snapshot, definition, job, output, **options)
            if len(used) == 1:
                capsule.write_json(job/'analysis-handoff.json', {'fixture': 'workflow validates this checkpoint'})
            return answer
        self.draft = checkpointed
        review = {'approved': False, 'findings': [{'defect': 'fixture issue'}], 'unresolved': []}
        result = self.invoke([review, {'approved': True, 'findings': [], 'unresolved': []}], reuse_analysis=True)
        self.assertIsNone(used[0])
        self.assertEqual(self.root/'jobs/round-01', used[1])
        self.assertEqual(review, self.contexts[1]['previousIndependentReview'])
        self.assertEqual('INDEPENDENT_REVIEW_APPROVED', result['status'])

    def test_quality_iterations_reanalyze_even_when_a_checkpoint_exists(self):
        original = self.draft
        used = []
        def checkpointed(snapshot, definition, job, output, **options):
            used.append(options.get('analysis_job'))
            answer = original(snapshot, definition, job, output, **options)
            capsule.write_json(job/'analysis-handoff.json', {'fixture': 'not reused by default'})
            return answer
        self.draft = checkpointed
        result = self.invoke([{'approved': False, 'findings': [], 'unresolved': ['fixture']},
                              {'approved': True, 'findings': [], 'unresolved': []}])
        self.assertEqual([None,None], used)
        self.assertTrue(result['freshAnalysisEachRound'])

    def test_structure_conflict_is_revised_without_falsifying_ai_review(self):
        approved = {'approved': True, 'findings': [], 'unresolved': []}
        issue = {'code': 'SYNTHETIC_STRUCTURE', 'severity': 'ERROR'}
        draft_original = self.draft
        def first_invalid(*args, **kwargs):
            result = draft_original(*args, **kwargs)
            if len(self.contexts) == 1:
                result['structureFindings'] = [issue]
            return result
        self.draft = first_invalid
        result = self.invoke([workflow.ReviewStructureConflict(approved, [issue]), approved])
        self.assertEqual(result['status'], 'INDEPENDENT_REVIEW_APPROVED')
        self.assertTrue(result['rounds'][0]['review']['approved'])
        self.assertFalse(result['rounds'][0]['approvalAccepted'])
        self.assertEqual(self.contexts[1]['structuralFindings'], [issue])

    def test_review_failure_does_not_become_a_pass(self):
        result = self.invoke(RuntimeError('provider failure'))
        self.assertEqual(result['status'], 'FAILED')
        self.assertIsNone(result['selectedDocument'])
        self.assertTrue((self.root/'jobs/round-01/iteration-failure.json').is_file())

    def test_expired_deadline_starts_no_ai_job(self):
        deadline = (datetime.now(timezone.utc)-timedelta(seconds=1)).isoformat()
        result = self.invoke([], deadline=deadline)
        self.assertEqual(result['status'], 'NOT_RUN_TIME_LIMIT')
        self.assertEqual(self.contexts, [])

    def test_existing_output_starts_no_ai_job(self):
        (self.root/'output').mkdir()
        with self.assertRaises(FileExistsError):
            self.invoke([])
        self.assertEqual(self.contexts, [])

    def test_mismatched_draft_bytes_are_never_reviewed(self):
        original = self.draft
        def tampered(*args, **kwargs):
            answer = original(*args, **kwargs)
            answer['contentSha256'] = '0'*64
            return answer
        self.draft = tampered
        result = self.invoke([])
        self.assertEqual(result['status'], 'FAILED')
        self.assertIn('original AI output', result['rounds'][0]['error'])

    def test_snapshot_change_is_rejected(self):
        def changed(*args, **kwargs):
            (self.snapshot/'sources/main.py').write_text('value = 8\n', encoding='utf-8')
            return {'approved': True, 'findings': [], 'unresolved': []}
        with self.assertRaises(ValueError):
            self.invoke(changed)

    def test_invalid_round_limit_starts_no_ai_job(self):
        with self.assertRaises(ValueError):
            self.invoke([], max_rounds=True)
        self.assertEqual(self.contexts, [])


if __name__ == '__main__':
    unittest.main()

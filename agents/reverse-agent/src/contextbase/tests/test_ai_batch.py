"""Synthetic publication scope and batch failure tests, without AI-quality scores."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from contextbase.ai import batch, capsule, workflow


class BatchTests(unittest.TestCase):
    def setUp(self):
        temporary_root = Path(__file__).resolve().parents[3] / '.tmp'
        temporary_root.mkdir(exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(prefix='ai-batch-', dir=temporary_root)
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        source = self.root / 'source'
        source.mkdir()
        (source/'main.py').write_text('value = 7\n', encoding='utf-8')
        self.snapshot = self.root/'snapshot'
        capsule.create(source, self.snapshot, project_id='synthetic')
        documents = [{'id': key, 'path': path, 'kind': kind, 'title': key,
                      'sourcePaths': ['main.py'], 'responsibilities': ['fixture']}
                     for key,path,kind in [('D','spec/detail.md','detailed-specification'),
                                           ('R','reports/limitations.md','analysis-report')]]
        raw_plan = self.root/'answer.txt'
        raw_plan.write_text(json.dumps({'systemSummary':'fixture','documents':documents,'unresolved':[]}),encoding='utf-8')
        bound = workflow.bind_existing_plan(self.snapshot,raw_plan,capsule.verification_state(self.snapshot)['manifestSha256'])
        self.plan = Path(bound['planFile'])

    def invoke(self, **options):
        return batch.run(self.snapshot,self.plan,self.root/'jobs',self.root/'output',**options)

    def test_analysis_reports_are_not_default_publications(self):
        with patch.object(workflow,'document',return_value={'documentId':'D','structureFindings':[],
                                                          'status':'AI_DRAFT_NOT_YET_INDEPENDENTLY_REVIEWED'}) as ai:
            result=self.invoke(independent_review=False)
        self.assertEqual(1,ai.call_count)
        self.assertEqual(['R'],result['analysisReportsExcludedFromPublication'])
        self.assertEqual(['R'],result['notSelected'])
        self.assertEqual(1,result['selected'])
        self.assertEqual(2,result['planned'])
        self.assertEqual('INCOMPLETE',result['status'])

    def test_explicit_analysis_report_needs_a_separate_report_job(self):
        with patch.object(workflow,'document') as ai,self.assertRaises(ValueError):
            self.invoke(document_ids=['R'])
        ai.assert_not_called()
        self.assertFalse((self.root/'jobs').exists())

    def test_changed_plan_pin_stops_before_any_ai_job(self):
        self.plan.write_text('{}',encoding='utf-8')
        with patch.object(workflow,'document') as ai,self.assertRaises((ValueError,KeyError)):
            self.invoke()
        ai.assert_not_called()
        self.assertFalse((self.root/'jobs').exists())

    def test_structure_approval_conflict_is_revision_required(self):
        answer={'documentId':'D','approved':True,'findings':[],'unresolved':[]}
        with patch.object(workflow,'document',return_value={'documentId':'D','structureFindings':[{'code':'fixture'}]}), \
             patch.object(workflow,'review',side_effect=workflow.ReviewStructureConflict(answer,[{'code':'fixture'}])):
            result=self.invoke()
        self.assertEqual('REQUIRES_AI_REVISION',result['documents'][0]['status'])
        self.assertTrue(result['documents'][0]['independentReview']['approved'])
        self.assertFalse(result['documents'][0]['approvalAccepted'])
        self.assertEqual('INCOMPLETE',result['status'])

    def test_provider_failure_is_preserved_and_not_passed(self):
        with patch.object(workflow,'document',side_effect=RuntimeError('provider failure')):
            result=self.invoke()
        self.assertEqual('FAILED',result['documents'][0]['status'])
        folder=capsule.sha256(b'D')[:16]
        self.assertTrue((self.root/'jobs'/folder/'batch-failure.json').exists())
        self.assertFalse(result['formallyEvaluatedByOriginalRubric'])

    def test_timezone_free_deadline_starts_no_ai_job(self):
        with patch.object(workflow,'document') as ai,self.assertRaises(ValueError):
            self.invoke(deadline='2026-10-13T04:47:15')
        ai.assert_not_called()
        self.assertFalse((self.root/'jobs').exists())


if __name__=='__main__':
    unittest.main()

"""Related-document routing from the AI plan, without business expectations."""
from pathlib import Path
import json
import tempfile
import unittest
from contextbase.ai import capsule, workflow


class PlanContextTests(unittest.TestCase):
    def setUp(self):
        temporary_root = Path(__file__).resolve().parents[3]/'.tmp'
        self.temp = tempfile.TemporaryDirectory(prefix='plan-context-',dir=temporary_root)
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        source = self.root/'source'; source.mkdir()
        (source/'main.txt').write_text('Synthetic source\n',encoding='utf-8')
        self.snapshot = self.root/'snapshot'
        capsule.create(source,self.snapshot,project_id='synthetic')
        raw = self.root/'answer.txt'
        values = [dict(id=identity,path=path,title=identity,kind=kind,
            sourcePaths=['main.txt'],responsibilities=[role])
            for identity,path,kind,role in [('FEATURE','docs/feature.md','detail','Feature description'),
              ('SHARED','docs/common/contract.md','common','Shared contract'),
              ('LIMIT','reports/limits.md','analysis-report','Analysis report')]]
        raw.write_text(json.dumps(dict(systemSummary='Synthetic',documents=values,unresolved=[])),encoding='utf-8')
        bound = workflow.bind_existing_plan(self.snapshot,raw,
                  capsule.verification_state(self.snapshot)['manifestSha256'])
        self.plan = Path(bound['planFile'])
        self.definition = workflow.select_document(self.plan,'FEATURE')

    def test_related_document_routing_is_visible_to_feature_writer(self):
        context = workflow._document_context(self.snapshot,self.definition)
        self.assertIn('docs/common/contract.md',context)
        self.assertIn('Shared contract',context)
        self.assertIn('analysis-report',context)
        self.assertIn('生成状態・採点期待値ではありません',context)
        self.assertNotIn(str(self.root),context)
        # The first plan object remains parseable for deferred analysis recovery.
        original,_ = json.JSONDecoder().raw_decode(context.split('\n対象文書計画:\n',1)[1])
        self.assertEqual(dict(self.definition),original)

    def test_changed_related_document_plan_is_rejected(self):
        value = json.loads(self.plan.read_text(encoding='utf-8'))
        value['documents'][1]['path']='docs/common/unrelated.md'
        self.plan.write_text(json.dumps(value),encoding='utf-8')
        with self.assertRaises(ValueError):
            workflow._document_context(self.snapshot,self.definition)

    def test_changed_source_stops_context_generation(self):
        (self.snapshot/'sources/main.txt').write_text('Different\n',encoding='utf-8')
        with self.assertRaises(ValueError):
            workflow._document_context(self.snapshot,self.definition)


if __name__ == '__main__':
    unittest.main()

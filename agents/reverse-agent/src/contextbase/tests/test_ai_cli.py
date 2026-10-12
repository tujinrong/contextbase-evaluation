"""CLI transport tests; all downstream AI stages are mocked, never executed."""
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path
import io
import json
import tempfile
import unittest
from unittest.mock import patch

from contextbase.ai import __main__ as cli


class AiCliTests(unittest.TestCase):
    def setUp(self):
        home=Path(__file__).resolve().parents[3]/'.tmp';home.mkdir(exist_ok=True)
        self.temp=tempfile.TemporaryDirectory(prefix='ai-cli-unit-',dir=home)
        self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name)
        self.snapshot=self.root/'capsule';self.job=self.root/'new-job'
        self.plan=self.root/'plan.json';self.output=self.root/'new-output'
        self.doc=self.root/'document.md';self.deadline='2030-01-01T00:00:00Z'
        self.revision=self.root/'revision.json';self.context={'previousPlan':{'documents':[]},'findings':[{'defect':'人工の構造指摘'}]}
        self.revision.write_text(json.dumps(self.context,ensure_ascii=False),encoding='utf-8')
        self.definition={'id':'DOC-UNIT','path':'document.md'}

    def args(self, command):
        return [command,'--snapshot',str(self.snapshot),'--job',str(self.job),
                '--timeout','901','--deadline',self.deadline]

    def execute(self,args):
        with redirect_stdout(io.StringIO()),redirect_stderr(io.StringIO()):return cli.main(args)

    def test_plan_forwards_deadline_and_revision_context_without_rewriting_it(self):
        with patch('contextbase.ai.workflow.plan',return_value={'status':'MOCK_ONLY'}) as stage:
            self.assertEqual(0,self.execute(self.args('plan')+['--revision-context',str(self.revision)]))
        stage.assert_called_once_with(self.snapshot,self.job,timeout=901,deadline=self.deadline,revision_context=self.context)

    def test_plan_without_optional_context_keeps_none(self):
        with patch('contextbase.ai.workflow.plan',return_value={}) as stage:
            self.assertEqual(0,self.execute(['plan','--snapshot',str(self.snapshot),'--job',str(self.job)]))
        self.assertIsNone(stage.call_args.kwargs['deadline']);self.assertIsNone(stage.call_args.kwargs['revision_context'])

    def test_document_forwards_deadline_and_revision_to_bound_definition(self):
        with patch('contextbase.ai.workflow.select_document',return_value=self.definition) as select, patch('contextbase.ai.workflow.document',return_value={}) as stage:
            self.assertEqual(0,self.execute(self.args('document')+['--plan',str(self.plan),'--document-id','DOC-UNIT','--output',str(self.output),'--revision-context',str(self.revision)]))
        select.assert_called_once_with(self.plan,'DOC-UNIT')
        stage.assert_called_once_with(self.snapshot,self.definition,self.job,self.output,timeout=901,revision_context=self.context,deadline=self.deadline)

    def test_review_forwards_deadline(self):
        with patch('contextbase.ai.workflow.select_document',return_value=self.definition), patch('contextbase.ai.workflow.review',return_value={}) as stage:
            self.assertEqual(0,self.execute(self.args('review')+['--plan',str(self.plan),'--document-id','DOC-UNIT','--document',str(self.doc)]))
        stage.assert_called_once_with(self.snapshot,self.doc,self.definition,self.job,timeout=901,deadline=self.deadline)

    def test_batch_keeps_its_deadline_and_subset_review_options(self):
        with patch('contextbase.ai.batch.run',return_value={}) as stage:
            self.assertEqual(0,self.execute(self.args('batch')+['--plan',str(self.plan),'--output',str(self.output),'--document-id','DOC-UNIT','--workers','3','--without-independent-review']))
        stage.assert_called_once_with(self.snapshot,self.plan,self.job,self.output,document_ids=['DOC-UNIT'],workers=3,deadline=self.deadline,timeout=901,independent_review=False)

    def test_iterate_forwards_rounds_timeout_and_deadline(self):
        with patch('contextbase.ai.iteration.run',return_value={}) as stage:
            self.assertEqual(0,self.execute(self.args('iterate')+['--plan',str(self.plan),'--document-id','DOC-UNIT','--output',str(self.output),'--max-rounds','2']))
        stage.assert_called_once_with(self.snapshot,self.plan,'DOC-UNIT',self.job,self.output,max_rounds=2,timeout=901,deadline=self.deadline)

    def test_iterate_defaults_to_three_rounds(self):
        with patch('contextbase.ai.iteration.run',return_value={}) as stage:
            self.assertEqual(0,self.execute(self.args('iterate')+['--plan',str(self.plan),'--document-id','DOC-UNIT','--output',str(self.output)]))
        self.assertEqual(3,stage.call_args.kwargs['max_rounds'])

    def test_iterate_requires_plan_document_and_output(self):
        for missing in ('--plan','--document-id','--output'):
            arguments=self.args('iterate')
            for flag,value in (('--plan',str(self.plan)),('--document-id','DOC-UNIT'),('--output',str(self.output))):
                if flag!=missing:arguments += [flag,value]
            with patch('contextbase.ai.iteration.run') as stage:
                with self.assertRaises(SystemExit):self.execute(arguments)
                stage.assert_not_called()

    def test_deadline_failure_is_nonzero_not_success(self):
        with patch('contextbase.ai.workflow.plan',side_effect=RuntimeError('RuntimeErrorTimeLimit')):
            self.assertEqual(1,self.execute(self.args('plan')))

    def test_snapshot_remains_explicitly_mode_aware(self):
        source=self.root/'source';reference=self.root/'design'
        with patch('contextbase.ai.capsule.create',return_value={'files':[]}) as stage:
            self.assertEqual(0,self.execute(['snapshot','--source',str(source),'--snapshot',str(self.snapshot),'--authorized-reference-directory',str(reference)]))
        stage.assert_called_once_with(source,self.snapshot,project_id='project',authorized_reference_directories=(reference,))

    def test_unified_cli_preserves_ai_stage_deadline_arguments(self):
        from contextbase import __main__ as unified
        args=self.args('plan')
        with patch('contextbase.ai.__main__.main',return_value=0) as entry:
            self.assertEqual(0,unified.main(['ai',*args]))
        entry.assert_called_once_with(args)


if __name__=='__main__':unittest.main()

"""Source-only applicability is a reviewable declaration, never acceptance."""
from copy import deepcopy
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest

from contextbase_runtime import contracts as c
from contextbase_runtime.adapters import index_source
from contextbase_runtime.agent import AgentWorkspace
from contextbase_runtime.controller import AcceptanceError
from contextbase_runtime.facts import FactIndex, instruction, POLICY as LEGACY_POLICY, EVIDENCE_POLICY
from contextbase_runtime.native_tools import Tools
from contextbase_runtime.sources import SourceAccess
from contextbase_runtime.storage import ArtifactStore
from contextbase_runtime.project_analysis import ProjectAnalysisAgent
from unittest.mock import patch
import test_project_analysis as native_fixture


POLICY = 'contextbase-fact-usage/2'


class FactApplicabilityTests(unittest.TestCase):
    def setUp(self):
        root = Path(__file__).resolve().parents[1] / '.tmp'
        root.mkdir(exist_ok=True)
        self.tmp = tempfile.TemporaryDirectory(prefix='fact-applicability-', dir=root)
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        src = self.root / 'input'
        src.mkdir()
        (src / 'AssemblyInfo.cs').write_text('using System.Runtime.CompilerServices;\n[assembly: InternalsVisibleTo("Tests")]\n', encoding='utf-8')
        self.source = SourceAccess.create(src, self.root / 'snapshot', project_id='applicability', allowed_paths=['.'], excluded_paths=[])
        self.store = ArtifactStore(self.root / 'work')
        self.index = FactIndex.open(self.source, self.store, parser=index_source)
        self.ref = self.source.evidence('AssemblyInfo.cs', 1, 2)
        self.task = {'id': 'author', 'contextId': 'context', 'operation': 'extract', 'stage': 'discovery',
            'origin': 'host-executed', 'requirements': ['catalog'], 'goalRequirementIds': ['catalog'],
            'snapshotId': self.source.snapshot_id, 'authorizedSourcePaths': ['AssemblyInfo.cs'],
            'sourceFactsSha256': self.index.sha256, 'factUsagePolicy': POLICY,
            'goalRequirements': [{'id': 'catalog', 'stage': 'discovery', 'scope': 'all', 'question': 'Analyze source', 'requires': []}]}
        self.unit = {'id': 'u1', 'requirement': 'catalog', 'question': 'Inspect test visibility', 'paths': ['AssemblyInfo.cs']}
        self.record = {'key': 'support.build', 'ownerRequirement': 'catalog', 'kind': 'system', 'name': 'Test visibility',
            'statement': 'Assembly grants internals visibility to Tests.', 'basis': 'observed-source', 'evidence': [self.ref], 'dependsOn': []}
        self.usage = {'recordKey': 'support.build', 'factIds': [], 'indexedEvidence': 'not-applicable',
            'reason': 'The sole indexed using import does not describe the assembly attribute; original text supplies that meaning.'}

    def tools(self, *, read=True):
        tools = Tools(self.source, self.index, self.task, {'task': self.task},
                      validate_final=lambda answer: self.index.validate_usage(answer, self.index.sha256))
        if read:
            tools.handle('read', {'path': 'AssemblyInfo.cs', 'startLine': 1, 'endLine': 2})
        tools.handle('plan_update', {'operation_id': 'plan', 'expected_revision': 0, 'plan': {'units': [self.unit]}})
        draft = {'unitId': 'u1', 'records': [deepcopy(self.record)], 'expectedVersions': [], 'removals': [],
            'unknowns': [], 'followups': [], 'factUsage': [deepcopy(self.usage)], 'remainingQuestions': [], 'complete': True, 'addUnits': []}
        return tools, draft

    def save(self, tools, draft):
        return tools.handle('draft_apply', {'operation_id': 'draft', 'expected_revision': 1, 'unit_id': 'u1',
                                            'include_diagnostics': True, 'draft': draft})

    def submit(self, tools):
        return tools.handle('submit_candidate', {'operation_id': 'submit', 'expected_revision': tools.revision,
            'closures': [{'requirement': 'catalog', 'status': 'supported', 'reason': 'Original source read', 'evidence': [self.ref]}]})

    def verification(self):
        task = {**self.task, 'id': 'verifier', 'operation': 'verify', 'candidate': 'f' * 64,
                'viewSha256': 'a' * 64, 'unknownBindings': [], 'sourceOnlyRecordKeys': ['support.build']}
        check = {'recordKey': 'support.build', 'status': 'pass', 'reason': 'The import is not attribute semantics; source is sufficient.', 'evidence': [self.ref]}
        answer = {'taskId': task['id'], 'candidateSha256': task['candidate'], 'viewSha256': task['viewSha256'],
            'sourceFactsSha256': self.index.sha256, 'checks': [{'requirement': 'catalog', 'status': 'pass', 'reason': 'Checked source', 'evidence': [self.ref]}],
            'unknownChecks': [], 'findings': [], 'unknowns': [], 'factUsageCheck': {'status': 'pass', 'reason': 'Checked associations', 'evidence': [self.ref], 'sourceOnlyChecks': [check]}}
        return task, answer

    def test_original_source_supported_claim_can_freeze_without_irrelevant_import(self):
        self.assertEqual({'import'}, {f['kind'] for f in self.index.document['facts']})
        tools, draft = self.tools()
        self.assertEqual(0, self.save(tools, draft)['factUsageDiagnostics']['issueCount'])
        self.submit(tools)
        self.assertEqual(self.usage, tools.submission['answer']['factUsage'][0])

    def test_ordinary_empty_usage_still_fails_and_declaration_requires_explanation(self):
        for mutation in ('missing', 'blank', 'contradictory'):
            with self.subTest(mutation=mutation):
                answer = {'sourceFactsSha256': self.index.sha256, 'records': [self.record], 'factUsage': [deepcopy(self.usage)]}
                row = answer['factUsage'][0]
                if mutation == 'missing': row.pop('indexedEvidence')
                elif mutation == 'blank': row['reason'] = '  '
                else: row['factIds'] = [self.index.document['facts'][0]['id']]
                with self.assertRaises(ValueError): self.index.validate_usage(answer, self.index.sha256)

    def test_old_task_schema_does_not_offer_new_declaration(self):
        old = {k:v for k,v in self.task.items() if k != 'factUsagePolicy'}
        schema = c.result_schema(old)['properties']['factUsage']['items']
        with self.assertRaises(ValueError): c.validate(self.usage, schema)

    def test_prompt_policy_matches_new_schema_and_preserves_legacy_text(self):
        old = {k:v for k,v in self.task.items() if k != 'factUsagePolicy'}
        self.assertEqual(LEGACY_POLICY, instruction(old))
        self.assertEqual(EVIDENCE_POLICY, instruction(old, evidence=True))
        for evidence in (False, True):
            text=instruction(self.task, evidence=evidence)
            self.assertNotIn('Empty factIds are allowed only', text)
            self.assertIn('set indexedEvidence', text)
            self.assertIn('explicit independent review', text)
        task,_=self.verification()
        self.assertIn('exactly one sourceOnlyChecks', instruction(task, verification=True))
        self.assertIn('Any fail or unknown prevents adoption', instruction(task, verification=True))
        # The same task-bound selection is used by the actual host prompt builder.
        workspace=SimpleNamespace(agent=SimpleNamespace(instruction='Inspect source'),
                                  _semantic_instruction=lambda task:'')
        self.assertNotIn('Empty factIds are allowed only', AgentWorkspace._instruction(workspace, self.task))
        self.assertIn('Empty factIds are allowed only', AgentWorkspace._instruction(workspace, old))

    def test_source_only_does_not_grant_original_text_delivery(self):
        tools, draft = self.tools(read=False)
        self.save(tools, draft)
        with self.assertRaisesRegex(ValueError, 'not supplied'): self.submit(tools)

    def test_patch_preserves_source_only_declaration_and_forged_source_still_fails(self):
        tools, draft = self.tools()
        self.save(tools, draft)
        tools.handle('draft_patch', {'operation_id': 'patch', 'expected_revision': 2, 'unit_id': 'u1',
            'updates': [{'key': 'support.build', 'fields': {'statement': 'Tests can see assembly internals.'}}],
            'include_diagnostics': True})
        self.submit(tools)
        self.assertEqual(self.usage, tools.submission['answer']['factUsage'][0])
        tools, draft = self.tools()
        draft['records'][0]['evidence'][0]['sha256']='0'*64
        self.save(tools, draft)
        with self.assertRaises(ValueError): self.submit(tools)

    def test_explicit_independent_checks_are_required_exact_and_evidenced(self):
        task, answer = self.verification()
        c.validate_result(answer, task, self.source)
        for mutation in ('missing', 'duplicate', 'wrong-key', 'blank-reason', 'no-evidence', 'forged-evidence', 'stale-candidate'):
            with self.subTest(mutation=mutation):
                bad = deepcopy(answer); checks=bad['factUsageCheck']['sourceOnlyChecks']
                if mutation == 'missing': bad['factUsageCheck'].pop('sourceOnlyChecks')
                elif mutation == 'duplicate': checks.append(deepcopy(checks[0]))
                elif mutation == 'wrong-key': checks[0]['recordKey']='old-candidate-record'
                elif mutation == 'blank-reason': checks[0]['reason']=' '
                elif mutation == 'no-evidence': checks[0]['evidence']=[]
                elif mutation == 'forged-evidence': checks[0]['evidence'][0]['sha256']='0'*64
                else: bad['candidateSha256']='0'*64
                with self.assertRaises(ValueError): c.validate_result(bad, task, self.source)

    def test_individual_rejection_prevents_global_pass_from_accepting(self):
        _, answer = self.verification()
        workspace = SimpleNamespace(agent=SimpleNamespace(source_fact_policy=True), fact_index=lambda: self.index,
                                    _catalog_policy=lambda: None, obligations={})
        view = {'records': {}, 'unknowns': {}, 'acceptedRequirements': []}
        for status in ('fail', 'unknown'):
            answer['factUsageCheck']['sourceOnlyChecks'][0]['status']=status
            with self.assertRaises(AcceptanceError): AgentWorkspace._check_adoption(workspace, view, answer)
        answer['factUsageCheck']['sourceOnlyChecks'][0]['status']='pass'
        AgentWorkspace._check_adoption(workspace, view, answer)


class SourceOnlyNativeLifecycleTests(unittest.TestCase):
    setUp = native_fixture.ProjectAnalysisTests.setUp
    run_native = native_fixture.ProjectAnalysisTests.run_native

    def provider(self, *args, **kwargs):
        original_rpc = native_fixture.rpc
        def change(connection, method, parameters):
            parameters = deepcopy(parameters)
            if method == 'tools/call' and parameters['name'] == 'draft_apply':
                for row in parameters['arguments']['draft']['factUsage']:
                    row.update(factIds=[], indexedEvidence='not-applicable',
                        reason='Synthetic author claims indexed syntax cannot express this source interpretation.')
            if method == 'tools/call' and parameters['name'] == 'review_submit':
                review = parameters['arguments']['review']
                task = self.calls[-1]['task']
                self.assertEqual(['catalog.record', 'links.record', 'rules.record'], task['sourceOnlyRecordKeys'])
                review['factUsageCheck']['sourceOnlyChecks'] = [{
                    'recordKey': key, 'status': self.review_status,
                    'reason': 'Synthetic independent applicability assessment against original source.',
                    'evidence': review['factUsageCheck']['evidence']}
                    for key in task['sourceOnlyRecordKeys']]
            return original_rpc(connection, method, parameters)
        with patch.object(native_fixture, 'rpc', side_effect=change):
            return native_fixture.ProjectAnalysisTests.provider(self, *args, **kwargs)

    def test_explicit_source_only_checks_can_pass_real_native_adoption(self):
        self.review_status = 'pass'
        self.assertEqual('complete', self.run_native()['status'])
        self.assertEqual({'catalog','links','rules'}, set(self.agent.status()['acceptedRequirements']))

    def test_available_relevant_facts_can_reject_source_only_claim_despite_global_pass(self):
        for status in ('fail','unknown'):
            with self.subTest(status=status):
                self.agent = ProjectAnalysisAgent.create(self.source, self.root/('rejected-'+status), native_fixture.request())
                self.calls=[]
                self.review_status=status
                result=self.run_native()
                self.assertEqual('needs-investigation',result['status'])
                self.assertEqual([],self.agent.status()['acceptedRequirements'])


if __name__ == '__main__': unittest.main()

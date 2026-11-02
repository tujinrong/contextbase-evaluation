"""Joint native analysis crosses the real broker, candidate, review and adoption seams."""
from copy import deepcopy
from contextlib import nullcontext
import json
from pathlib import Path
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from contextbase_runtime.project_analysis import ProjectAnalysisAgent, validate_export
from contextbase_runtime import contracts
from test_independent_agents import request, simulated_answer
from test_native_mcp import rpc


class ProjectAnalysisTests(unittest.TestCase):
    def setUp(self):
        home = Path(__file__).resolve().parents[1] / '.tmp'
        home.mkdir(exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=home)
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / 'source'
        self.source.mkdir()
        (self.source / 'Registration.cs').write_text('class Registration {\n bool Save(int value) { return value > 0; }\n}\n', encoding='utf-8')
        self.agent = ProjectAnalysisAgent.create(self.source, self.root / 'work', request())
        self.calls = []
        self.wrong_kind = False
        self.skip_read = False
        self.cancel = False
        self.wrong_review = False

    def provider(self, workspace, job, prompt, schema, timeout, **options):
        connection = options['tool_connection']
        def call(name, arguments):
            answer = rpc(connection, 'tools/call', {'name': name, 'arguments': arguments})['result']
            if answer['isError']:
                raise ValueError(answer['content'][0]['text'])
            return json.loads(answer['content'][0]['text'])
        def material(collection):
            text, offset = '', 0
            while True:
                page = call('analysis_state', {'collection': collection, 'offset': offset, 'limit': 12000})
                text += page['text']
                if page['next_offset'] is None:
                    return json.loads(text)
                offset = page['next_offset']
        task, context = material('task'), material('context')
        self.calls.append({'task': task, 'role': options['role_spec'], 'instruction_role': options['instruction_role']})
        ref = self.agent.session.source.evidence('Registration.cs', 1, 3)
        if not self.skip_read:
            call('read', {'path': 'Registration.cs', 'startLine': 1, 'endLine': 3})
        facts = call('query', {'offset': 0, 'limit': 100, 'path': None, 'kind': None,
            'text': None, 'caller': None, 'callee': None, 'route': None})['result']
        if self.cancel:
            self.agent.session.cancel('cancel during native call')
        if task['operation'] == 'verify':
            review = simulated_answer(context)
            if self.wrong_review:
                review['candidateSha256'] = '0' * 64
            submitted = call('review_submit', {'review': review})
        else:
            units = [{'id': key, 'requirement': key, 'question': 'Analyze complete source responsibility',
                      'paths': ['Registration.cs']} for key in task['requirements']]
            call('plan_update', {'operation_id': 'plan', 'expected_revision': 0, 'plan': {'units': units}})
            obligations = {row['id']: row for row in task['goalRequirements']}
            for number, unit in enumerate(units, 1):
                key = unit['requirement']
                kind = {'discovery': 'system', 'relationship': 'relation', 'behavior': 'fact'}[obligations[key]['stage']]
                if self.wrong_kind and key == 'links':
                    kind = 'fact'
                record = {'key': key + '.record', 'ownerRequirement': key, 'kind': kind,
                    'name': key, 'statement': 'Synthetic source interpretation', 'basis': 'observed-source',
                    'evidence': [ref], 'dependsOn': [dep + '.record' for dep in obligations[key]['requires']],
                    'classification': None}
                draft = {'unitId': key, 'records': [record], 'expectedVersions': [], 'removals': [],
                    'unknowns': [], 'followups': [], 'factUsage': [{'recordKey': record['key'],
                        'factIds': [facts['facts'][0]['id']] if facts['facts'] else [], 'reason': 'Source-aligned observation'}],
                    'remainingQuestions': [], 'complete': True, 'addUnits': []}
                call('draft_apply', {'operation_id': key, 'expected_revision': number, 'unit_id': key, 'draft': draft})
            closures = [{'requirement': key, 'status': 'supported', 'reason': 'Synthetic full-scope analysis',
                         'evidence': [ref]} for key in task['requirements']]
            submitted = call('submit_candidate', {'operation_id': 'submit', 'expected_revision': len(units) + 1,
                                                 'closures': closures})
        return {'exit_code': 0, 'metadata': {'status': 'passed'},
                'answer': {'submission_id': submitted['submission_id']}}

    def run_native(self, **kwargs):
        environment = SimpleNamespace(identifier='test-environment', report=lambda: {'testDouble': True})
        with patch('contextbase_runtime.native_environment.scope', return_value=nullcontext(environment)), \
                patch('contextbase_runtime.provider.run_job', side_effect=self.provider):
            return self.agent.run(**kwargs)

    def test_joint_author_and_fresh_verifier_atomically_accept_dependencies(self):
        result = self.run_native()
        self.assertEqual('complete', result['status'])
        self.assertEqual(2, len(self.calls))
        self.assertEqual(['analysis', 'verification'], [row['instruction_role'] for row in self.calls])
        for call in self.calls:
            self.assertEqual('contextbase-draft-unknowns/2', call['task']['draftUnknownPolicy'])
            self.assertEqual('contextbase-fact-usage/2', call['task']['factUsagePolicy'])
        self.assertNotEqual(self.calls[0]['task']['contextId'], self.calls[1]['task']['contextId'])
        self.assertNotEqual(self.calls[0]['role']['instructions_sha256'], self.calls[1]['role']['instructions_sha256'])
        exported = self.agent.export()
        validate_export(exported)
        receipts = exported['payload']['receipts']
        self.assertEqual({'catalog', 'links', 'rules'}, set(receipts))
        self.assertEqual({'catalog': receipts['catalog']['contentSha256']}, receipts['links']['requires'])
        self.assertEqual({'links': receipts['links']['contentSha256']}, receipts['rules']['requires'])
        records = exported['payload']['records']
        self.assertEqual(records['catalog.record']['version'], records['links.record']['dependencies'][0]['version'])

    def test_missing_original_prerequisite_stops_before_provider(self):
        result = self.run_native(requirements=['rules'])
        self.assertEqual('needs-prerequisites', result['status'])
        self.assertFalse(self.calls)

    def test_wrong_kind_cannot_be_frozen_or_adopted(self):
        self.wrong_kind = True
        with self.assertRaisesRegex(ValueError, 'kind|responsibility|obligation'):
            self.run_native()
        self.assertEqual([], self.agent.session.status()['acceptedRequirements'])

    def test_undelivered_original_source_blocks_submission(self):
        self.skip_read = True
        with self.assertRaisesRegex(ValueError, 'not supplied'):
            self.run_native()
        self.assertEqual([], self.agent.session.status()['acceptedRequirements'])

    def test_cancel_revokes_native_tool_mutations(self):
        self.cancel = True
        with self.assertRaisesRegex(ValueError, 'cancel|current|epoch|active'):
            self.run_native()
        self.assertEqual([], self.agent.session.status()['acceptedRequirements'])

    def test_modified_export_dependency_is_rejected_even_with_new_outer_hash(self):
        self.run_native()
        exported = deepcopy(self.agent.export())
        exported['payload']['records']['links.record']['dependencies'][0]['version'] = '0' * 64
        exported['sha256'] = contracts.digest(exported['payload'])
        with self.assertRaises(ValueError):
            validate_export(exported)

    def test_review_cannot_accept_a_different_candidate(self):
        self.wrong_review = True
        with self.assertRaises(ValueError):
            self.run_native()
        self.assertEqual([], self.agent.session.status()['acceptedRequirements'])

    def test_candidate_body_cannot_differ_from_native_submission(self):
        self.run_native()
        session = self.agent.session
        candidate = session._state()['candidates'][0]
        artifact = session.store.get('candidates/' + candidate + '.json')
        task = session.store.get('tasks/' + artifact['taskId'] + '/request.json')
        artifact['answer']['records'][0]['statement'] = 'Changed after native submission'
        with self.assertRaisesRegex(ValueError, 'replay'):
            session._replay_evidence(task, artifact)

    def test_profile_publishes_joint_result_and_rejects_changed_role_profile(self):
        from contextbase_runtime.config import ProjectProfile
        (self.root / 'request.json').write_text(json.dumps(request()), encoding='utf-8')
        instructions = self.root / 'reader.md'
        instructions.write_text('Analyze the complete source through authorized tools.', encoding='utf-8')
        config = self.root / 'project.toml'
        config.write_text('''schema = "contextbase-project/1"
default_profile = "test"
[profiles.test]
source = "source"
request = "request.json"
work = "configured-work"
output = "output"
context_mode = "native"
[profiles.test.roles.analysis]
instructions = "reader.md"
''', encoding='utf-8')
        profile = ProjectProfile.load(config)
        self.agent = ProjectAnalysisAgent.create(profile.source, profile.work(ProjectAnalysisAgent.name),
            profile.request, role_specs=profile.role_specs)
        profile.bind(self.agent)
        self.assertEqual('complete', self.run_native()['status'])
        published = profile.publish(self.agent)
        envelope = json.loads(Path(published['output']).read_text(encoding='utf-8'))
        validate_export(envelope)
        self.assertEqual('project-analysis', envelope['payload']['producer'])
        self.assertEqual(profile.role_specs['analysis']['instructions_sha256'],
                         envelope['payload']['roleSpecs']['analysis']['instructions_sha256'])
        instructions.write_text('Changed author role instructions.', encoding='utf-8')
        changed = ProjectProfile.load(config)
        with self.assertRaisesRegex(ValueError, 'role settings'):
            changed.validate_workspace(self.agent)

"""Author/verification schemas expose only host-authorized task references."""
from copy import deepcopy
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from contextbase_discovery import DiscoveryAgent
from contextbase_runtime import contracts
from contextbase_runtime.wire import CompactWire, bind
from test_independent_agents import request, simulated_answer


SHA = 'a' * 64
EVIDENCE = {'path': 'Registration.cs', 'sha256': SHA, 'startLine': 1, 'endLine': 2}


def task():
    requirements = deepcopy(request()['goal']['requirements'])
    requirements += [
        {'id': 'other_catalog', 'stage': 'discovery', 'scope': 'other', 'question': 'Other catalog.', 'requires': []},
        {'id': 'other_links', 'stage': 'relationship', 'scope': 'other', 'question': 'Other links.',
         'requires': ['other_catalog']}]
    return {'id': '1' * 32, 'contextId': '2' * 32, 'snapshotId': '3' * 64,
            'stage': 'discovery', 'operation': 'extract', 'requirements': ['catalog'],
            'goalRequirementIds': [item['id'] for item in requirements], 'goalRequirements': requirements,
            'authorizedSourcePaths': ['Registration.cs'], 'candidate': None, 'viewSha256': None,
            'unknownBindings': []}


def answer(current):
    return {'taskId': current['id'], 'records': [], 'coverage': [
        {'requirement': 'catalog', 'status': 'not-applicable', 'recordKeys': [], 'evidence': [EVIDENCE]}],
        'unknowns': [], 'followups': []}


def note(**changes):
    return {'stage': 'relationship', 'question': 'Obtain omitted build material.',
            'paths': [], 'requirement': 'links', **changes}


class TaskScopeSchemaTests(unittest.TestCase):
    def schemas(self, current, response):
        yield contracts.result_schema(current), response
        index = SimpleNamespace(sha256='b' * 64, document={
            'files': [{'path': 'Registration.cs', 'sourceSha256': SHA}], 'facts': []})
        compact_task = {**current, 'sourceFactsSha256': index.sha256}
        compact_task.update(bind(compact_task, index))
        wire = CompactWire(compact_task)
        compact_response = {**deepcopy(response), 'sourceFactsSha256': index.sha256}
        if current['operation'] == 'verify':
            compact_response['factUsageCheck'] = {'status': 'pass', 'reason': 'Synthetic independent fact check.',
                                                'evidence': [EVIDENCE]}
        else:
            compact_response['factUsage'] = []
        yield wire.schema(contracts.transport_schema(compact_task)), wire.encode_response(compact_response)

    def assert_valid_both(self, current, response):
        for schema, encoded in self.schemas(current, response):
            contracts.validate(encoded, schema)

    def assert_invalid_both(self, current, response):
        for schema, encoded in self.schemas(current, response):
            with self.assertRaises(ValueError):
                contracts.validate(encoded, schema)

    def test_normal_and_compact_followups_reject_omitted_paths_but_allow_sealed_paths(self):
        current = task()
        response = answer(current)
        for path in ('Project.slnx', 'database/generate.mjs', '../Registration.cs'):
            with self.subTest(path=path):
                response['followups'] = [note(paths=[path])]
                self.assert_invalid_both(current, response)
        response['followups'] = [note(paths=['Registration.cs'])]
        self.assert_valid_both(current, response)

    def test_future_stage_requirement_and_real_null_are_allowed_but_mismatches_are_not(self):
        current = task()
        response = answer(current)
        for stage, requirement in (('relationship', 'links'), ('behavior', 'rules'),
                                   ('discovery', 'catalog'), ('behavior', None)):
            with self.subTest(stage=stage, requirement=requirement):
                response['followups'] = [note(stage=stage, requirement=requirement)]
                self.assert_valid_both(current, response)
        for requirement in ('catalog', 'other_links', 'invented', 'null'):
            with self.subTest(requirement=requirement):
                response['followups'] = [note(stage='relationship', requirement=requirement)]
                self.assert_invalid_both(current, response)

    def test_empty_authorized_inventory_only_allows_empty_followup_path_arrays(self):
        current = task()
        current['authorizedSourcePaths'] = []
        response = answer(current)
        response['followups'] = [note(paths=[])]
        self.assert_valid_both(current, response)
        response['followups'] = [note(paths=['Registration.cs'])]
        self.assert_invalid_both(current, response)

    def test_unknowns_and_verification_blockers_can_name_future_goals_but_not_invent_ids(self):
        current = task()
        response = answer(current)
        unknown = {'id': 'missing', 'question': 'Obtain a missing future input.',
                   'relatedRequirements': ['rules'], 'blocksRequirements': ['rules'],
                   'scopeReason': 'This affects the explicitly requested behavior obligation.'}
        response['unknowns'] = [unknown]
        self.assert_valid_both(current, response)
        for field in ('relatedRequirements', 'blocksRequirements'):
            damaged = deepcopy(response)
            damaged['unknowns'][0][field] = ['invented']
            self.assert_invalid_both(current, damaged)
        current.update(operation='verify', candidate='c' * 64, viewSha256='d' * 64,
                       unknownBindings=[{'id': 'missing', 'sha256': SHA}])
        verified = {'taskId': current['id'], 'candidateSha256': current['candidate'],
            'viewSha256': current['viewSha256'], 'checks': [
                {'requirement': 'catalog', 'status': 'pass', 'reason': 'Synthetic source check.', 'evidence': [EVIDENCE]}],
            'unknownChecks': [{'unknownId': 'missing', 'unknownSha256': SHA, 'status': 'blocking',
                              'blocksRequirements': ['rules'], 'reason': 'Future obligation affected.', 'evidence': []}],
            'findings': [], 'unknowns': [unknown]}
        self.assert_valid_both(current, verified)
        verified['unknownChecks'][0]['blocksRequirements'] = ['invented']
        self.assert_invalid_both(current, verified)

    def test_task_schemas_do_not_mutate_shared_constants_or_legacy_followup_shape(self):
        original_unknown, original_followup = deepcopy(contracts.UNKNOWN), deepcopy(contracts.FOLLOWUP)
        current = task()
        contracts.result_schema(current)
        contracts.transport_schema(current)
        current.update(operation='verify', candidate=SHA, viewSha256=SHA)
        contracts.result_schema(current)
        self.assertEqual(original_unknown, contracts.UNKNOWN)
        self.assertEqual(original_followup, contracts.FOLLOWUP)
        legacy = task()
        legacy.pop('authorizedSourcePaths')
        response = answer(legacy)
        response['followups'] = [note(paths=['Project.slnx'])]
        self.assert_valid_both(legacy, response)
        self.assertEqual(original_followup, contracts.result_schema(legacy)['properties']['followups']['items'])

    def test_public_discovery_records_sealed_paths_and_delivers_missing_material_followup(self):
        home = Path(__file__).resolve().parents[1] / '.tmp'
        home.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(prefix='task-scope-schema-', dir=home) as temporary:
            root = Path(temporary)
            source = root / 'source'
            (source / 'database').mkdir(parents=True)
            (source / 'Registration.cs').write_bytes(
                b'class Registration {\n bool Save(int value) { return value > 0; }\n}\n')
            (source / 'Project.slnx').write_bytes(b'<Solution/>')
            (source / 'database/generate.mjs').write_bytes(b'// Synthetic omitted material, never executed.')
            req = request()
            req['excludedPaths'] = ['Project.slnx', 'database/generate.mjs']
            for compact in (False, True):
                with self.subTest(compact=compact):
                    agent = DiscoveryAgent.create(source, root / ('work-' + str(compact)), req)
                    tasks = []
                    def provider(workspace, directory, prompt, schema, timeout):
                        delivered = json.loads(prompt[prompt.index('{"request":'):])
                        identifier = delivered['task']['id']
                        canonical = agent.session.store.get('tasks/' + identifier + '/canonical-context.json') \
                            if compact else delivered
                        tasks.append(canonical['task'])
                        response = simulated_answer(canonical)
                        if canonical['task']['operation'] == 'extract':
                            response['followups'] = [note(question='Obtain omitted Project.slnx and database/generate.mjs.', paths=[])]
                        encoded = CompactWire(canonical['task']).encode_response(response) if compact else response
                        contracts.validate(encoded, schema)
                        return {'exit_code': 0, 'metadata': {'status': 'passed'}, 'answer': encoded}
                    with patch('contextbase_runtime.provider.run_job', side_effect=provider):
                        self.assertEqual('complete', agent.run(inline_sources=True, compact=compact)['status'])
                    self.assertEqual(2, len(tasks))
                    for current in tasks:
                        stored = agent.session.store.get('tasks/' + current['id'] + '/request.json')
                        self.assertEqual(['Registration.cs'], stored['authorizedSourcePaths'])
                    self.assertEqual([], agent.export()['payload']['followups'][0]['paths'])


if __name__ == '__main__':
    unittest.main()

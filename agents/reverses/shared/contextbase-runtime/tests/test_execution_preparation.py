"""Each execution mode prepares only its consumed provider inputs and artifacts."""
from contextlib import contextmanager
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from contextbase_discovery import DiscoveryAgent
from contextbase_runtime import contracts, controller, evidence_dialog, repair
from contextbase_runtime.controller import Session
from contextbase_runtime.wire import CompactWire, POLICY as WIRE_POLICY
from test_independent_agents import request, simulated_answer
import test_evidence_agents as evidence_fixture
import test_incremental_agents as incremental_fixture
import test_project_analysis as native_fixture
import test_repair as repair_fixture


class ExecutionPreparationTests(unittest.TestCase):
    def setUp(self):
        home = Path(__file__).resolve().parents[1] / '.tmp'
        home.mkdir(exist_ok=True)
        self.temporary = tempfile.TemporaryDirectory(prefix='execution-preparation-', dir=home)
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.source = self.root / 'source'
        self.source.mkdir()
        (self.source / 'Registration.cs').write_text(
            'class Registration {\n bool Save(int value) { return value > 0; }\n}\n', encoding='utf-8')

    @contextmanager
    def without_outer_encoding(self, *, schema=True):
        encode = Mock(side_effect=AssertionError('An unused whole-context prompt was serialized'))
        outer_schema = Mock(side_effect=AssertionError('An unused outer transport schema was constructed'))
        proxy = SimpleNamespace(**{key: value for key, value in vars(contracts).items()
                                   if not key.startswith('__')})
        proxy.transport_schema = outer_schema
        with patch.object(controller, 'json', SimpleNamespace(dumps=encode)):
            if schema:
                with patch.object(controller, 'contracts', proxy):
                    yield
            else:
                yield
        encode.assert_not_called()
        if schema:
            outer_schema.assert_not_called()

    def assert_direct_input(self, session, prompt, schema):
        delivered = json.loads(prompt.rsplit('\n', 1)[-1])
        task = delivered['task']
        canonical = (session.store.get('tasks/' + task['id'] + '/canonical-context.json')
                     if task.get('wireSha256') else delivered)
        task = canonical['task']
        instruction = session._instruction(task)
        expected_schema = contracts.transport_schema(task)
        if task.get('repairSeedSha256'):
            seed = session.store.get('repair-seed.json')
            expected_schema = contracts.transport_schema(task, repair.response_schema(seed, task))
        if task.get('wireBinding'):
            wire = CompactWire(task)
            self.assertEqual(wire.context(canonical), delivered)
            expected_schema = wire.schema(expected_schema)
            instruction += '\n' + WIRE_POLICY
        self.assertEqual(controller.POLICY + '\n' + instruction + '\n'
                         + json.dumps(delivered, ensure_ascii=False), prompt)
        self.assertEqual(expected_schema, schema)
        self.assertEqual(delivered, session.store.get('tasks/' + task['id'] + '/context.json'))
        return canonical

    def test_direct_and_compact_provider_inputs_are_preserved(self):
        for compact in (False, True):
            with self.subTest(compact=compact):
                agent = DiscoveryAgent.create(self.source, self.root / ('work-' + str(compact)), request())
                calls = []
                def provider(workspace, job, prompt, schema, timeout):
                    context = self.assert_direct_input(agent.session, prompt, schema)
                    calls.append(context)
                    answer = simulated_answer(context)
                    if compact:
                        answer = CompactWire(context['task']).encode_response(answer)
                    return {'exit_code': 0, 'metadata': {'status': 'passed'}, 'answer': answer}
                candidate = agent.session.execute('discovery', inline_sources=True,
                                                  compact=compact, runner=provider)
                self.assertEqual(1, len(calls))
                self.assertEqual('extract', candidate['operation'])
                self.assertEqual(calls[0]['task']['id'], candidate['result']['taskId'])

    def test_evidence_uses_its_round_prompt_and_preserves_the_root_context(self):
        fixture = evidence_fixture.EvidenceAgentTests()
        fixture.setUp()
        self.addCleanup(fixture.tearDown)
        agent = fixture.create()
        def provider(workspace, job, prompt, schema, timeout, **options):
            context = json.loads(prompt.rsplit('\n', 1)[-1])
            task = context['task']
            expected = (controller.POLICY + '\n' + agent.session._instruction(task) + '\n'
                        + evidence_dialog.POLICY + '\n'
                        + json.dumps(context, sort_keys=True, ensure_ascii=False,
                                     separators=(',', ':'), allow_nan=False))
            self.assertEqual(expected, prompt)
            self.assertEqual(contracts.transport_schema(task, evidence_dialog.response_schema(
                task, contracts.transport_schema(task))), schema)
            return fixture.provider(workspace, job, prompt, schema, timeout, **options)
        with self.without_outer_encoding(schema=False), \
                patch('contextbase_runtime.provider.run_job', side_effect=provider):
            self.assertEqual('complete', agent.run()['status'])
        for identifier in agent.session._state()['tasks']:
            context = agent.session.store.get('tasks/' + identifier + '/context.json')
            setup = agent.session.store.get('tasks/' + identifier + '/evidence/setup.json')
            self.assertEqual(context, setup['context'])

    def test_native_and_incremental_do_not_prepare_unused_outer_inputs(self):
        for mode in ('native', 'incremental'):
            with self.subTest(mode=mode):
                if mode == 'native':
                    fixture = native_fixture.ProjectAnalysisTests()
                    fixture.setUp()
                    self.addCleanup(fixture.doCleanups)
                    agent = fixture.agent
                    run = fixture.run_native
                else:
                    fixture = incremental_fixture.IncrementalAgentTests()
                    fixture.setUp()
                    self.addCleanup(fixture.tearDown)
                    agent = fixture.create()
                    run = lambda: fixture.run_agent(agent)
                with self.without_outer_encoding():
                    self.assertEqual('complete', run()['status'])
                for identifier in agent.session._state()['tasks']:
                    root = 'tasks/' + identifier
                    if mode == 'native':
                        self.assertFalse(agent.session.store.path(root + '/context.json').exists())
                        transport = agent.session.store.get(root + '/transport.json')
                        manifest = agent.session.store.get('native-transcripts/'
                            + transport['metadata']['nativeTranscriptSha256'] + '.json')
                        self.assertEqual(agent.session.store.get(root + '/request.json'),
                                         manifest['context']['task'])
                        setup_paths = list(agent.session.store.path(root + '/native').glob('*/setup.json'))
                        self.assertEqual(1, len(setup_paths))
                        setup = agent.session.store.get(setup_paths[0].relative_to(agent.work).as_posix())
                        self.assertEqual(setup['context'], manifest['context'])
                    else:
                        context = agent.session.store.get(root + '/context.json')
                        self.assertEqual(agent.session.store.get(root + '/request.json'), context['task'])

    def test_repair_and_compact_repair_provider_inputs_are_preserved(self):
        for compact in (False, True):
            with self.subTest(compact=compact):
                fixture = repair_fixture.RepairTests()
                fixture.setUp()
                self.addCleanup(fixture.tearDown)
                def provider(workspace, job, prompt, schema, timeout, **options):
                    self.assert_direct_input(fixture.agent.session, prompt, schema)
                    return fixture.provider(workspace, job, prompt, schema, timeout, **options)
                outer_schema = Mock(wraps=contracts.transport_schema)
                proxy = SimpleNamespace(**{key: value for key, value in vars(contracts).items()
                                           if not key.startswith('__')})
                proxy.transport_schema = outer_schema
                with patch.object(controller, 'contracts', proxy), \
                        patch('contextbase_runtime.provider.run_job', side_effect=provider):
                    result = fixture.agent.repair(fixture.old.work, fixture.old_task, ['catalog.record'],
                                                  inline_sources=True, compact=compact)
                self.assertEqual('complete', result['status'])
                # One repair-author schema and one ordinary-verifier schema.
                self.assertEqual(2, outer_schema.call_count)

    def test_native_and_incremental_validate_before_the_first_provider_call(self):
        for mode in ('native', 'incremental'):
            with self.subTest(mode=mode):
                session = Session.create(self.source, self.root / ('invalid-' + mode), request(),
                                         **{mode + '_mode': True})
                prepare = session._prepare
                def invalid_task(*args, **kwargs):
                    task = prepare(*args, **kwargs)
                    return {**task, 'operation': 'invalid-operation'}
                provider = Mock(side_effect=AssertionError('Invalid task reached provider'))
                with patch.object(session, '_prepare', side_effect=invalid_task), self.assertRaises(ValueError):
                    session.execute('discovery', runner=provider)
                provider.assert_not_called()

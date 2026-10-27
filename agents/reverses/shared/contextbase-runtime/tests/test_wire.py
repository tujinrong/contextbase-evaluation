"""Task-local compact transport expands exactly before host domain validation."""
from copy import deepcopy
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from contextbase_discovery import DiscoveryAgent
from contextbase_runtime import contracts
from contextbase_runtime.wire import CompactWire, VERSION, bind
from test_independent_agents import request, simulated_answer


SHA = 'a' * 64
EVIDENCE = {'path': 'Registration.cs', 'sha256': SHA, 'startLine': 1, 'endLine': 2}


def codec(task_id='1' * 32):
    index = SimpleNamespace(sha256='b' * 64, document={
        'files': [{'path': 'Registration.cs', 'sourceSha256': SHA}],
        'facts': [{'id': 'symbol:' + 'c' * 64, 'kind': 'symbol'}]})
    task = {'id': task_id, 'contextId': task_id + '-context', 'snapshotId': 'd' * 64,
            'candidate': None, 'viewSha256': None, 'sourceFactsSha256': index.sha256}
    task.update(bind(task, index))
    return CompactWire(task)


class WireCodecTests(unittest.TestCase):
    def test_roundtrip_restores_exact_canonical_evidence_and_fact_ids(self):
        wire = codec()
        canonical = {'evidence': [EVIDENCE], 'factUsage': [
            {'recordKey': 'record', 'factIds': ['symbol:' + 'c' * 64], 'reason': 'Synthetic support.'}]}
        raw = wire.encode_response(canonical)
        self.assertEqual({'file', 'startLine', 'endLine'}, set(raw['evidence'][0]))
        self.assertNotIn('sha256', raw['evidence'][0])
        self.assertIn(raw['factUsage'][0]['factIds'][0], wire.facts)
        self.assertEqual(canonical, wire.decode_response(raw))
        schema = wire.schema(contracts.obj({'evidence': contracts.arr(contracts.EVIDENCE),
            'factUsage': contracts.arr(contracts.obj({'recordKey': contracts.TEXT,
                'factIds': contracts.STRINGS, 'reason': contracts.TEXT}))}))
        contracts.validate(raw, schema)
        self.assertEqual({'file', 'startLine', 'endLine'},
                         set(schema['properties']['evidence']['items']['properties']))

    def test_old_alias_wrong_frame_hash_and_unknown_file_or_fact_are_rejected(self):
        wire = codec()
        canonical = {'evidence': [EVIDENCE], 'factUsage': [
            {'recordKey': 'record', 'factIds': ['symbol:' + 'c' * 64], 'reason': 'Synthetic support.'}]}
        for mutation in ('frame', 'file', 'fact', 'old-alias'):
            raw = wire.encode_response(canonical)
            if mutation == 'frame':
                raw['wireSha256'] = '0' * 64
            elif mutation == 'file':
                raw['evidence'][0]['file'] = 'unknown-file'
            elif mutation == 'fact':
                raw['factUsage'][0]['factIds'] = ['unknown-fact']
            else:
                raw = codec('2' * 32).encode_response(canonical)
                raw['wireSha256'] = wire.task['wireSha256']
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                wire.decode_response(raw)

    def test_constructor_rejects_changed_snapshot_candidate_context_or_binding(self):
        wire = codec()
        for field in ('snapshotId', 'candidate', 'viewSha256', 'contextId', 'sourceFactsSha256'):
            task = deepcopy(wire.task)
            task[field] = 'changed'
            with self.subTest(field=field), self.assertRaises(ValueError):
                CompactWire(task)
        task = deepcopy(wire.task)
        task['wireBinding']['files']['extra'] = {'path': 'extra.cs', 'sha256': SHA}
        with self.assertRaises(ValueError):
            CompactWire(task)


class WireDiscoveryTests(unittest.TestCase):
    def setUp(self):
        home = Path(__file__).resolve().parents[1] / '.tmp'
        home.mkdir(exist_ok=True)
        self.temporary = tempfile.TemporaryDirectory(prefix='wire-discovery-', dir=home)
        self.root = Path(self.temporary.name)
        self.source = self.root / 'source'
        self.source.mkdir()
        (self.source / 'Registration.cs').write_bytes(
            b'class Registration {\n bool Save(int value) { return value > 0; }\n}\n')
        self.agent = DiscoveryAgent.create(self.source, self.root / 'work', request())
        self.frames = []
        self.operation = None

    def tearDown(self):
        self.temporary.cleanup()

    def provider(self, workspace, directory, prompt, schema, timeout):
        context = json.loads(prompt[prompt.index('{"request":'):])
        task_id = context['task']['id']
        canonical = self.agent.session.store.get('tasks/' + task_id + '/canonical-context.json')
        wire = CompactWire(canonical['task'])
        self.operation = canonical['task']['operation']
        answer = simulated_answer(canonical)
        raw = wire.encode_response(answer)
        contracts.validate(raw, schema)
        self.frames.append({'context': context, 'canonical': canonical, 'wire': wire,
                            'answer': answer, 'raw': raw})
        return {'exit_code': 0, 'metadata': {'status': 'passed'}, 'answer': raw}

    def test_public_discovery_expands_both_task_local_frames_before_persisting_candidates(self):
        with patch('contextbase_runtime.provider.run_job', side_effect=self.provider):
            self.assertEqual('complete', self.agent.run(compact=True, inline_sources=True)['status'])
        self.assertEqual(2, len(self.frames))
        author, reviewer = self.frames
        self.assertNotEqual(author['wire'].task['contextId'], reviewer['wire'].task['contextId'])
        self.assertTrue(set(author['wire'].files).isdisjoint(reviewer['wire'].files))
        self.assertTrue(set(author['wire'].facts).isdisjoint(reviewer['wire'].facts))
        self.assertIsNone(author['wire'].binding['candidate'])
        self.assertEqual(reviewer['canonical']['task']['candidate'], reviewer['wire'].binding['candidate'])
        self.assertEqual(reviewer['canonical']['task']['viewSha256'], reviewer['wire'].binding['viewSha256'])
        state = self.agent.session._state()
        candidate = self.agent.session.store.get('candidates/' + state['candidates'][0] + '.json')
        verification = self.agent.session.store.get('verifications/' + state['verifications'][0] + '.json')
        self.assertEqual(author['answer'], candidate['answer'])
        self.assertEqual(reviewer['answer'], verification['answer'])
        for frame, saved in ((author, candidate), (reviewer, verification)):
            task = frame['canonical']['task']
            self.assertNotIn('wireBinding', frame['context']['task'])
            self.assertEqual(VERSION, frame['context']['wireEncoding']['schema'])
            materialization = self.agent.session.store.get('tasks/' + task['id'] + '/materialization.json')
            self.assertEqual(task['wireSha256'], materialization['wireSha256'])
            self.assertEqual(contracts.digest(frame['raw']), materialization['rawAnswerSha256'])
            self.assertEqual(contracts.digest(frame['answer']), materialization['canonicalAnswerSha256'])
            self.assertEqual(VERSION, saved['provenance']['responseEncoding'])
            self.assertEqual(task['wireSha256'], saved['provenance']['wireSha256'])
            self.assertEqual(contracts.digest(frame['raw']), saved['provenance']['rawAnswerSha256'])
        for record in author['raw']['records']:
            for evidence in record['evidence']:
                self.assertEqual({'file', 'startLine', 'endLine'}, set(evidence))
        for usage in author['raw']['factUsage']:
            self.assertTrue(usage['factIds'])
            self.assertTrue(set(usage['factIds']).issubset(author['wire'].facts))
            self.assertTrue(set(usage['factIds']).isdisjoint(author['wire'].facts.values()))

    def test_end_of_batch_integrity_failure_cannot_persist_candidate_or_adopt_review(self):
        for operation in ('extract', 'verify'):
            with self.subTest(operation=operation):
                self.agent = DiscoveryAgent.create(self.source, self.root / ('work-' + operation), request())
                source = self.agent.session.source
                original_many = source.verify_evidence_many
                failures = []
                def batch(refs):
                    if self.operation != operation:
                        return original_many(refs)
                    original_verify = source._verify
                    calls = []
                    def fail_at_end():
                        calls.append(True)
                        if len(calls) == 2:
                            failures.append(True)
                            raise ValueError('Synthetic end-of-batch source mutation')
                        original_verify()
                    with patch.object(source, '_verify', side_effect=fail_at_end):
                        return original_many(refs)
                self.operation = None
                with patch('contextbase_runtime.provider.run_job', side_effect=self.provider), \
                     patch.object(source, 'verify_evidence_many', side_effect=batch), self.assertRaises(ValueError):
                    self.agent.run(compact=True, inline_sources=True)
                state = self.agent.session._state()
                self.assertEqual([], state['acceptedRequirements'])
                self.assertEqual([], state['verifications'])
                if operation == 'extract':
                    self.assertEqual([], state['candidates'])
                self.assertEqual(1, len(failures))


if __name__ == '__main__':
    unittest.main()

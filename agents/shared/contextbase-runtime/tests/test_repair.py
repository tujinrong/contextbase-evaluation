"""Rejected drafts remain untrusted through bounded repair and independent review."""
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from contextbase_discovery import DiscoveryAgent
from contextbase_runtime import contracts, repair
from contextbase_runtime.controller import AcceptanceError
from contextbase_runtime.wire import CompactWire
from test_independent_agents import request, simulated_answer


class RepairTests(unittest.TestCase):
    def setUp(self):
        home = Path(__file__).resolve().parents[1] / '.tmp'
        home.mkdir(exist_ok=True)
        self.temporary = tempfile.TemporaryDirectory(prefix='rejected-repair-', dir=home)
        self.root = Path(self.temporary.name)
        self.source = self.root / 'source'
        self.source.mkdir()
        (self.source / 'Registration.cs').write_bytes(
            b'class Registration {\n bool Save(int value) { return value > 0; }\n}\n')
        self.old = DiscoveryAgent.create(self.source, self.root / 'rejected', request())
        def rejected(workspace, directory, prompt, schema, timeout):
            context = json.loads(prompt[prompt.index('{"request":'):])
            self.old_task = context['task']['id']
            answer = simulated_answer(context)
            answer['records'][0].update(kind='common', classification={
                'category': 'common', 'scope': 'registration', 'responsibility': 'Normalize source input',
                'consumers': ['missing.consumer'], 'rationale': 'Synthetic shared responsibility.',
                'alternative': 'Considered main processing.'})
            answer['unknowns'] = [{'id': 'outside', 'question': 'An unresolved future detail.',
                'relatedRequirements': ['rules'], 'blocksRequirements': [],
                'scopeReason': 'Outside the current catalog obligation.'}]
            contracts.validate(answer, schema)
            return {'exit_code': 0, 'metadata': {'status': 'passed'}, 'answer': answer}
        with patch('contextbase_runtime.provider.run_job', side_effect=rejected), self.assertRaises(ValueError):
            self.old.run(inline_sources=True)
        self.agent = DiscoveryAgent.create(self.source, self.root / 'repair', request())
        self.frames = []
        self.patch_mutator = None
        self.fail_review = False

    def tearDown(self):
        self.temporary.cleanup()

    def seed_and_task(self):
        seed = repair.install(self.agent, self.old.work, self.old_task, ['catalog.record'])
        task = self.agent.session.prepare('discovery')
        return seed, task

    def patch_answer(self, seed, task):
        selected = task['repairRecords'][0]
        replacement = deepcopy(next(item for item in seed['answer']['records'] if item['key'] == selected['key']))
        replacement['classification']['consumers'] = ['catalog.entry']
        return {'taskId': task['id'], 'repairSeedSha256': task['repairSeedSha256'], 'status': 'repaired',
                'reason': 'Replace the unsupported consumer with its source-backed entry.',
                'replacements': [{'key': selected['key'], 'expectedRecordHash': selected['expectedRecordHash'],
                                  'replacement': replacement, 'factUsage': None}]}

    def provider(self, workspace, directory, prompt, schema, timeout):
        delivered = json.loads(prompt[prompt.index('{"request":'):])
        task = delivered['task']
        canonical = self.agent.session.store.get('tasks/' + task['id'] + '/canonical-context.json') \
            if task.get('wireSha256') else delivered
        task = canonical['task']
        if task['operation'] == 'extract':
            seed = self.agent.session.store.get('repair-seed.json')
            answer = self.patch_answer(seed, task)
            if self.patch_mutator:
                self.patch_mutator(answer)
        else:
            answer = simulated_answer(canonical)
            if self.fail_review:
                answer['checks'][0].update(status='fail', reason='Independent source review rejects the proposed repair.')
        raw = CompactWire(task).encode_response(answer) if task.get('wireBinding') else answer
        contracts.validate(raw, schema)
        self.frames.append({'context': canonical, 'answer': deepcopy(answer), 'raw': deepcopy(raw)})
        return {'exit_code': 0, 'metadata': {'status': 'passed'}, 'answer': raw}

    def public_repair(self, **kwargs):
        with patch('contextbase_runtime.provider.run_job', side_effect=self.provider):
            return self.agent.repair(self.old.work, self.old_task, ['catalog.record'], inline_sources=True, **kwargs)

    def test_combination_changes_only_authorized_whole_record_and_preserves_all_other_content(self):
        seed, task = self.seed_and_task()
        before = deepcopy(seed)
        patch_answer = self.patch_answer(seed, task)
        contracts.validate(patch_answer, repair.response_schema(seed, task))
        combined = repair.combine(seed, task, patch_answer)
        self.assertEqual(seed, before)
        self.assertEqual(patch_answer['replacements'][0]['replacement'], combined['records'][0])
        self.assertEqual(seed['answer']['records'][1:], combined['records'][1:])
        for field in ('coverage', 'unknowns', 'followups', 'factUsage'):
            self.assertEqual(seed['answer'][field], combined[field])
        self.assertEqual(task['id'], combined['taskId'])
        usage = deepcopy(seed['answer']['factUsage'][0])
        usage['reason'] = 'Explicitly rechecked the same source fact.'
        patch_answer['replacements'][0]['factUsage'] = usage
        self.assertEqual(usage, repair.combine(seed, task, patch_answer)['factUsage'][0])

    def test_seed_hash_duplicate_unauthorized_and_identity_changes_are_rejected(self):
        seed, task = self.seed_and_task()
        for mutation in ('seed', 'patch-seed', 'duplicate', 'unauthorized', 'hash', 'kind', 'owner', 'key', 'usage-owner'):
            local_seed, changed = deepcopy(seed), self.patch_answer(seed, task)
            item = changed['replacements'][0]
            if mutation == 'seed':
                local_seed['trust'] = 'Changed untrusted seed text.'
            elif mutation == 'patch-seed':
                changed['repairSeedSha256'] = '0' * 64
            elif mutation == 'duplicate':
                changed['replacements'].append(deepcopy(item))
            elif mutation == 'unauthorized':
                item['key'] = 'catalog.entry'
            elif mutation == 'hash':
                item['expectedRecordHash'] = '0' * 64
            elif mutation in {'kind', 'owner', 'key'}:
                item['replacement'][{'owner': 'ownerRequirement'}.get(mutation, mutation)] = 'changed'
            else:
                item['factUsage'] = {**deepcopy(seed['answer']['factUsage'][0]), 'recordKey': 'catalog.entry'}
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                repair.combine(local_seed, task, changed)

    def test_install_rejects_wrong_source_request_keys_and_nonfresh_workspace(self):
        for index, keys in enumerate(([], ['catalog.record', 'catalog.record'], ['missing'])):
            agent = DiscoveryAgent.create(self.source, self.root / ('keys-' + str(index)), request())
            with self.subTest(keys=keys), self.assertRaises(ValueError):
                repair.install(agent, self.old.work, self.old_task, keys)
        self.agent.session.prepare('discovery')
        with self.assertRaises(ValueError):
            repair.install(self.agent, self.old.work, self.old_task, ['catalog.record'])
        changed = request()
        changed['goal']['question'] += ' Changed goal.'
        agent = DiscoveryAgent.create(self.source, self.root / 'wrong-request', changed)
        with self.assertRaises(ValueError):
            repair.install(agent, self.old.work, self.old_task, ['catalog.record'])
        (self.source / 'Registration.cs').write_bytes(b'class Changed {}\n')
        agent = DiscoveryAgent.create(self.source, self.root / 'wrong-source', request())
        with self.assertRaises(ValueError):
            repair.install(agent, self.old.work, self.old_task, ['catalog.record'])

    def test_public_compact_repair_still_needs_independent_verification_and_records_its_origin(self):
        self.assertEqual('complete', self.public_repair(compact=True)['status'])
        self.assertEqual(['extract', 'verify'], [frame['context']['task']['operation'] for frame in self.frames])
        self.assertNotEqual(self.frames[0]['context']['task']['contextId'], self.frames[1]['context']['task']['contextId'])
        state = self.agent.session._state()
        candidate = self.agent.session.store.get('candidates/' + state['candidates'][0] + '.json')
        seed = self.agent.session.store.get('repair-seed.json')
        self.assertEqual('repaired-rejected-draft', candidate['provenance']['proposalOrigin'])
        self.assertEqual(contracts.digest(seed), candidate['provenance']['repairSeedSha256'])
        self.assertEqual(seed['answer']['coverage'], candidate['answer']['coverage'])
        self.assertEqual(seed['answer']['unknowns'], candidate['answer']['unknowns'])
        self.assertEqual(['catalog.entry'], candidate['answer']['records'][0]['classification']['consumers'])
        self.assertEqual(['catalog'], self.agent.status()['acceptedRequirements'])

    def test_residual_dangling_dependency_is_rejected_after_patch_combination(self):
        self.patch_mutator = lambda answer: answer['replacements'][0]['replacement'].update(dependsOn=['missing.record'])
        with self.assertRaises(ValueError):
            self.public_repair()
        state = self.agent.session._state()
        self.assertEqual([], state['candidates'])
        self.assertEqual([], state['acceptedRequirements'])

    def test_failed_independent_verification_cannot_adopt_a_repaired_candidate(self):
        self.fail_review = True
        result = self.public_repair()
        self.assertEqual('needs-investigation', result['status'])
        state = self.agent.session._state()
        self.assertEqual(1, len(state['candidates']))
        self.assertEqual([], state['acceptedRequirements'])
        with self.assertRaises(AcceptanceError):
            self.agent.session.adopt(state['candidates'][0])

    def test_adopt_replays_raw_patch_and_rejects_mismatch_with_stored_candidate(self):
        repair.install(self.agent, self.old.work, self.old_task, ['catalog.record'])
        with patch('contextbase_runtime.provider.run_job', side_effect=self.provider):
            proposed = self.agent.session.execute('discovery', inline_sources=True)
            self.agent.session.verify(proposed['id'], inline_sources=True)
        candidate = self.agent.session.store.get('candidates/' + proposed['id'] + '.json')
        relative = 'tasks/' + candidate['taskId'] + '/transport.json'
        transport = self.agent.session.store.get(relative)
        transport['answer']['replacements'][0]['replacement']['statement'] = 'Changed after independent verification.'
        # Reseal the outer artifact to exercise semantic replay, not just the
        # ArtifactStore corruption check. The old candidate remains unchanged.
        self.agent.session.store.path(relative).write_text(json.dumps({
            'sha256': contracts.digest(transport), 'payload': transport}), encoding='utf-8')
        with self.assertRaises((AcceptanceError, ValueError)):
            self.agent.session.adopt(proposed['id'])
        self.assertEqual([], self.agent.status()['acceptedRequirements'])

    def test_injected_runner_completes_public_repair_path_without_gaining_trusted_adoption(self):
        result = self.agent.repair(self.old.work, self.old_task, ['catalog.record'],
                                   inline_sources=True, runner=self.provider)
        self.assertEqual('needs-investigation', result['status'])
        self.assertEqual(2, len(self.frames))
        state = self.agent.session._state()
        self.assertEqual(1, len(state['candidates']))
        self.assertEqual(1, len(state['verifications']))
        self.assertEqual([], state['acceptedRequirements'])


if __name__ == '__main__':
    unittest.main()

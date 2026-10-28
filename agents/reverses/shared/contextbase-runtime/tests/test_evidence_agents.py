"""Public independent Agents retrieve originals before canonical adoption.

Provider replies are synthetic. The fixtures never execute an input program.
"""
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from contextbase_discovery import DiscoveryAgent
from contextbase_relationship import RelationshipAgent
from contextbase_behavior import BehaviorAgent
from contextbase_runtime import contracts
from contextbase_runtime.evidence_dialog import VERSION
from test_independent_agents import request, simulated_answer


class EvidenceAgentTests(unittest.TestCase):
    def setUp(self):
        temporary_root = Path(__file__).resolve().parents[1] / '.tmp'
        temporary_root.mkdir(exist_ok=True)
        self.temporary = tempfile.TemporaryDirectory(prefix='evidence-agents-', dir=temporary_root)
        self.root = Path(self.temporary.name)
        self.source = self.root / 'source'
        self.source.mkdir()
        (self.source / 'Registration.cs').write_text(
            'class Registration {\n bool Save(int value) { return value > 0; }\n}\n', encoding='utf-8')
        self.agents = {}
        self.calls = []
        self.mutate = None
        self.skip_requests = False
        self.cancel_during_provider = False

    def tearDown(self):
        self.temporary.cleanup()

    def create(self, agent_type=DiscoveryAgent, *, handoff=None, name=None):
        agent = agent_type.create(self.source, self.root / (name or agent_type.name),
                                  request(), handoff=handoff, evidence_mode=True)
        self.agents[agent.session.source.root] = agent
        return agent

    def provider(self, workspace, job, prompt, schema, timeout):
        # Only the final JSON line is context; policy prose is not parsed as data.
        context = json.loads(prompt.rsplit('\n', 1)[-1])
        self.calls.append(deepcopy(context))
        agent = self.agents[Path(workspace)]
        task = context['task']
        wrapper = {'protocol': VERSION, 'taskId': task['id'], 'action': 'requests',
                   'requests': [], 'answer': None, 'workingNotes': ''}
        if context['evidenceDialog']['round'] == 1 and not self.skip_requests:
            path = context['inventory']['files'][0]['path']
            wrapper['requests'] = [
                {'operation': 'query', 'offset': 0, 'limit': 100,
                 **{key: None for key in ('path', 'kind', 'text', 'caller', 'callee', 'route')}},
                {'operation': 'read', 'path': path, 'startLine': 1, 'endLine': None},
            ]
        else:
            # Synthetic-answer construction may inspect the actual index, but
            # this copy is never delivered as model context or recorded as a
            # retrieval receipt. Real answer citations must still pass the host.
            fixture_context = deepcopy(context)
            fixture_context['structure'] = agent.session.fact_index().context()
            answer = simulated_answer(fixture_context)
            if self.mutate:
                self.mutate(context, answer)
            wrapper.update(action='finish', requests=[], answer=answer)
        if self.cancel_during_provider:
            self.cancel_during_provider = False
            agent.session.cancel('Synthetic cancellation while the provider was in flight.')
        return {'exit_code': 0, 'metadata': {'status': 'passed'}, 'answer': wrapper}

    def run_agent(self, agent):
        with patch('contextbase_runtime.provider.run_job', side_effect=self.provider):
            return agent.run()

    def test_three_independent_agents_retrieve_originals_and_keep_full_review_bindings(self):
        handoff = None
        all_agents = []
        for agent_type in (DiscoveryAgent, RelationshipAgent, BehaviorAgent):
            agent = self.create(agent_type, handoff=handoff)
            all_agents.append(agent)
            self.assertEqual('complete', self.run_agent(agent)['status'])
            handoff = agent.export()
        self.assertEqual(['catalog', 'links', 'rules'], handoff['payload']['acceptedRequirements'])
        tasks = {}
        for context in self.calls:
            task = context['task']
            tasks.setdefault(task['id'], []).append(context)
            self.assertEqual(VERSION, task['evidencePolicy'])
            self.assertEqual('host-evidence-requests', context['sourceDelivery']['mode'])
            self.assertNotIn('files', context['sourceDelivery'])
            for collection in ('symbols', 'calls', 'entries', 'imports'):
                self.assertNotIn(collection, context['structure'])
            if task['operation'] == 'verify':
                self.assertEqual(task['viewSha256'], context['candidate']['viewSha256'])
                self.assertEqual(task['requirements'], context['verificationView']['acceptedRequirements'])
                self.assertNotIn('currentRecords', context)
        # D extraction/verification, R premise check/extraction/verification,
        # B premise check/extraction/verification each own an independent context.
        self.assertEqual(8, len(tasks))
        self.assertEqual(8, len({calls[0]['task']['contextId'] for calls in tasks.values()}))
        for calls in tasks.values():
            self.assertEqual([1, 2], [item['evidenceDialog']['round'] for item in calls])
            self.assertEqual([], calls[0]['evidenceDialog']['deliveryLedger'])
            delivered = calls[1]['evidenceDialog']['latestEvidence']
            self.assertEqual({'query', 'read'}, {item['request']['operation'] for item in delivered})
            self.assertTrue(all(item['reply']['taskId'] == calls[0]['task']['id'] for item in delivered))
        extracts = [context for context in self.calls
                    if context['task']['operation'] == 'extract' and context['evidenceDialog']['round'] == 1]
        self.assertEqual(['discovery', 'relationship', 'behavior'], [c['task']['stage'] for c in extracts])
        self.assertNotIn('verifiedCatalog', extracts[1]['assignment'])
        self.assertEqual('currentRecords', extracts[1]['assignment']['recordsLocation'])
        self.assertNotIn('verifiedRelationships', extracts[2]['assignment'])
        self.assertNotIn('supportingCatalog', extracts[2]['assignment'])
        self.assertEqual('currentRecords', extracts[2]['assignment']['recordsLocation'])
        for agent in all_agents:
            for identifier in agent.status()['verifications']:
                artifact = agent.session.store.get('verifications/' + identifier + '.json')
                self.assertEqual('codex-ephemeral-evidence-dialog', artifact['provenance']['transport'])
                self.assertTrue(artifact['provenance']['independenceVerified'])

    def test_unknown_or_failed_full_view_check_still_prevents_adoption(self):
        for verdict in ('unknown', 'fail'):
            with self.subTest(verdict=verdict):
                agent = self.create(name=verdict)
                def reject(context, answer):
                    if context['task']['operation'] == 'verify':
                        answer['checks'][0]['status'] = verdict
                self.mutate = reject
                result = self.run_agent(agent)
                self.assertEqual('needs-investigation', result['status'])
                self.assertEqual([], agent.status()['acceptedRequirements'])
                self.assertEqual(1, len(agent.status()['verifications']))

    def test_canonical_source_citations_require_this_task_to_read_the_original(self):
        agent = self.create()
        self.skip_requests = True
        with self.assertRaises(ValueError):
            self.run_agent(agent)
        self.assertEqual([], agent.status()['candidates'])
        self.assertEqual([], agent.status()['acceptedRequirements'])
        self.assertEqual('stopped', agent.status()['status'])

    def test_injected_transport_cannot_become_a_trusted_adoption(self):
        agent = self.create()
        result = agent.run(runner=self.provider)
        self.assertEqual('needs-investigation', result['status'])
        self.assertEqual([], agent.status()['acceptedRequirements'])
        proposal = agent.session.store.get('candidates/' + result['pending']['candidate'] + '.json')
        self.assertEqual('injected-test-transport', proposal['provenance']['kind'])
        self.assertFalse(proposal['provenance']['independenceVerified'])

    def test_cancelled_provider_result_cannot_record_a_candidate(self):
        agent = self.create()
        self.cancel_during_provider = True
        with self.assertRaises(ValueError):
            self.run_agent(agent)
        state = agent.status()
        self.assertEqual('cancelled', state['status'])
        self.assertEqual([], state['candidates'])
        self.assertEqual([], state['verifications'])
        self.assertTrue(all(status == 'cancelled' for status in state['tasks'].values()))

    def corrupt_transcript(self, agent, task_id):
        path = agent.session.store.path('tasks/' + task_id + '/evidence/transcript.json')
        stored = json.loads(path.read_text(encoding='utf-8'))
        payload = stored['payload']
        payload['tampered'] = True
        # Keep the outer storage digest valid: replay must also enforce the
        # immutable transcript identity held by the canonical provenance.
        stored['sha256'] = contracts.digest(payload)
        path.write_text(json.dumps(stored, ensure_ascii=False), encoding='utf-8')

    def test_transcript_tampering_is_rechecked_before_normal_adoption(self):
        agent = self.create()
        with patch('contextbase_runtime.provider.run_job', side_effect=self.provider):
            proposed = agent.session.execute('discovery')
            agent.session.verify(proposed['id'])
        candidate = agent.session.store.get('candidates/' + proposed['id'] + '.json')
        self.corrupt_transcript(agent, candidate['taskId'])
        with self.assertRaises(ValueError):
            agent.session.adopt(proposed['id'])
        self.assertEqual([], agent.status()['acceptedRequirements'])

    def test_transcript_tampering_cannot_activate_an_external_handoff(self):
        discovery = self.create()
        self.assertEqual('complete', self.run_agent(discovery)['status'])
        recipient = self.create(RelationshipAgent, handoff=discovery.export())
        from contextbase_runtime import handoff as transfer
        activate = transfer._activate
        def tamper_before_activation(agent, candidate_id, verification_id):
            artifact = agent.session.store.get('verifications/' + verification_id + '.json')
            self.corrupt_transcript(agent, artifact['taskId'])
            return activate(agent, candidate_id, verification_id)
        with patch('contextbase_runtime.provider.run_job', side_effect=self.provider):
            with patch('contextbase_runtime.handoff._activate', side_effect=tamper_before_activation):
                with self.assertRaises(ValueError):
                    recipient.run()
        self.assertEqual([], recipient.status()['acceptedRequirements'])
        self.assertIsNone(recipient.status()['revision'])


if __name__ == '__main__':
    unittest.main()

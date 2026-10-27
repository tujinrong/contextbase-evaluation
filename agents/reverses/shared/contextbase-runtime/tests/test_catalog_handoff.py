"""Modern catalog policy and exact unknown identities survive portable handoff."""
from contextlib import contextmanager
from copy import deepcopy
import builtins
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from contextbase_discovery import DiscoveryAgent
from contextbase_relationship import RelationshipAgent
from contextbase_runtime import catalog, contracts
from contextbase_runtime.handoff import revalidate
from test_independent_agents import add_fact_usage, request, simulated_answer


class CatalogHandoffTests(unittest.TestCase):
    def setUp(self):
        home = Path(__file__).resolve().parents[1] / '.tmp'
        home.mkdir(exist_ok=True)
        self.temporary = tempfile.TemporaryDirectory(prefix='catalog-handoff-', dir=home)
        self.root = Path(self.temporary.name)
        self.producer = self.root / 'producer'
        self.source = self.producer / 'source'
        self.receiver_source = self.root / 'independent-source'
        for source in (self.source, self.receiver_source):
            source.mkdir(parents=True)
            (source / 'Registration.cs').write_text(
                'class Registration {\n bool Save(int value) { return value > 0; }\n}\n', encoding='utf-8')
        self.contexts = []
        self.mode = 'typed'
        self.omit_scope = False

    def tearDown(self):
        self.temporary.cleanup()

    def provider(self, workspace, job, prompt, schema, timeout):
        context = json.loads(prompt[prompt.index('{"request":'):])
        self.contexts.append(context)
        answer = simulated_answer(context)
        task = context['task']
        if task['operation'] == 'extract' and task['stage'] == 'discovery':
            if self.mode == 'pending':
                obligations = {item['id']: item for item in task['goalRequirements']}
                for record in answer['records']:
                    if record['kind'] == 'function':
                        owner = record['ownerRequirement']
                        record.update(kind='unclassified', classification={
                            'category': 'pending', 'scope': obligations[owner]['scope'],
                            'tentativeKind': 'function', 'impact': 'outside-obligation',
                            'reason': 'Synthetic deployment concern outside this obligation.', 'unknownIds': ['local']})
                answer['unknowns'] = [{
                    'id': 'local', 'question': 'Synthetic unresolved deployment detail.',
                    'relatedRequirements': list(task['requirements']), 'blocksRequirements': [],
                    'scopeReason': 'Outside the requested static registration obligation.'}]
            elif self.mode == 'empty':
                answer['records'] = []
                for coverage in answer['coverage']:
                    coverage.update(status='not-applicable', recordKeys=[])
        if task['operation'] == 'verify' and self.omit_scope:
            answer['scopeChecks'] = []
        add_fact_usage(context, answer)
        return {'exit_code': 0, 'metadata': {'status': 'passed'}, 'answer': answer}

    def run_agent(self, agent, **kwargs):
        with patch('contextbase_runtime.provider.run_job', side_effect=self.provider):
            return agent.run(inline_sources=True, **kwargs)

    def revalidate(self, agent):
        with patch('contextbase_runtime.provider.run_job', side_effect=self.provider):
            return revalidate(agent, timeout=30, inline_sources=True, runner=None)

    @contextmanager
    def unavailable_producer(self):
        retired = self.root / 'unavailable-producer'
        self.producer.rename(retired)
        forbidden = (self.producer.absolute(), retired.absolute())
        def guard(original):
            def checked(file, *args, **kwargs):
                if isinstance(file, (str, bytes, os.PathLike)):
                    path = Path(os.fsdecode(file)).absolute()
                    if any(path == prefix or prefix in path.parents for prefix in forbidden):
                        raise AssertionError('Receiver attempted to read producer source/work: ' + str(path))
                return original(file, *args, **kwargs)
            return checked
        with patch('builtins.open', side_effect=guard(builtins.open)), \
             patch('io.open', side_effect=guard(io.open)):
            yield

    def test_same_local_pending_id_from_two_author_contexts_stays_exact_during_receiver_run(self):
        req = request()
        req['goal']['requirements'].append({
            'id': 'other_catalog', 'stage': 'discovery', 'scope': 'registration',
            'question': 'Inspect a second independent synthetic concern.', 'requires': []})
        req['goal']['requirements'][1]['requires'].append('other_catalog')
        self.mode = 'pending'
        discovery = DiscoveryAgent.create(self.source, self.producer / 'work', req)
        author_ids = {}
        for owner in ('catalog', 'other_catalog'):
            start = len(self.contexts)
            self.assertEqual('complete', self.run_agent(discovery, requirements=[owner])['status'])
            author_ids[owner] = next(item['task']['id'] for item in self.contexts[start:]
                                     if item['task']['operation'] == 'extract')
        envelope = discovery.export()
        payload = envelope['payload']
        self.assertEqual(catalog.VERSION, payload['catalogPolicy'])
        expected_ids = {identifier + ':local' for identifier in author_ids.values()}
        self.assertEqual(expected_ids, set(payload['unknowns']))
        for owner, identifier in author_ids.items():
            self.assertEqual([identifier + ':local'],
                             payload['records'][owner + '.record']['classification']['unknownIds'])
        self.assertNotIn(str(self.producer), json.dumps(envelope))
        start = len(self.contexts)
        with self.unavailable_producer():
            relationship = RelationshipAgent.create(
                self.receiver_source, self.root / 'relationship', req, handoff=envelope)
            incoming = relationship.session.store.get('incoming.json')
            self.assertEqual(catalog.VERSION, incoming['payload']['catalogPolicy'])
            self.assertEqual('complete', self.run_agent(relationship)['status'])
            result = relationship.export()
        local = self.contexts[start:]
        self.assertEqual('verify', local[0]['task']['operation'])
        self.assertEqual(catalog.VERSION, local[0]['task']['catalogPolicy'])
        self.assertEqual(expected_ids, {item['id'] for item in local[0]['task']['unknownBindings']})
        self.assertEqual({'discovery': envelope['sha256']}, result['payload']['premises'])
        for owner, identifier in author_ids.items():
            self.assertEqual([identifier + ':local'],
                             result['payload']['records'][owner + '.record']['classification']['unknownIds'])

    def test_empty_modern_catalog_retains_policy_and_requires_receiver_scope_review(self):
        self.mode = 'empty'
        discovery = DiscoveryAgent.create(self.source, self.producer / 'work', request())
        self.assertEqual('complete', self.run_agent(discovery)['status'])
        envelope = discovery.export()
        self.assertEqual({}, envelope['payload']['records'])
        self.assertEqual(catalog.VERSION, envelope['payload']['catalogPolicy'])
        stripped = deepcopy(envelope)
        stripped['payload'].pop('catalogPolicy')
        stripped['sha256'] = contracts.digest(stripped['payload'])
        with patch('contextbase_runtime.provider.run_job') as provider:
            with self.assertRaises(ValueError):
                RelationshipAgent.create(self.receiver_source, self.root / 'missing-empty-policy',
                                         request(), handoff=stripped)
            provider.assert_not_called()
        with self.unavailable_producer():
            relationship = RelationshipAgent.create(
                self.receiver_source, self.root / 'relationship', request(), handoff=envelope)
            start = len(self.contexts)
            self.assertIsNone(self.revalidate(relationship))
            verification = self.contexts[start]['task']
            self.assertEqual(catalog.VERSION, verification['catalogPolicy'])
            self.assertEqual([], verification['classificationBindings'])
            self.assertEqual(['registration'], catalog.scopes(verification))
            self.assertEqual(['catalog'], relationship.status()['acceptedRequirements'])
            rejected = RelationshipAgent.create(
                self.receiver_source, self.root / 'missing-scope-review', request(), handoff=envelope)
            self.omit_scope = True
            with self.assertRaises(ValueError):
                self.revalidate(rejected)
            self.assertEqual([], rejected.status()['acceptedRequirements'])

    def test_typed_artifact_cannot_strip_or_replace_its_policy_marker(self):
        discovery = DiscoveryAgent.create(self.source, self.producer / 'work', request())
        self.assertEqual('complete', self.run_agent(discovery)['status'])
        envelope = discovery.export()
        for index, policy in enumerate((None, 'contextbase-catalog/invalid')):
            damaged = deepcopy(envelope)
            if policy is None:
                damaged['payload'].pop('catalogPolicy')
            else:
                damaged['payload']['catalogPolicy'] = policy
            damaged['sha256'] = contracts.digest(damaged['payload'])
            with self.subTest(policy=policy), patch('contextbase_runtime.provider.run_job') as provider:
                with self.assertRaises(ValueError):
                    RelationshipAgent.create(self.receiver_source, self.root / ('invalid-' + str(index)),
                                             request(), handoff=damaged)
                provider.assert_not_called()


if __name__ == '__main__':
    unittest.main()

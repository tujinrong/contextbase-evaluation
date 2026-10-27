"""Classification policy exercised through real host state, with synthetic AI."""
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from contextbase_discovery import DiscoveryAgent
from contextbase_runtime import catalog, contracts
from contextbase_runtime.agents import POLICY
from contextbase_runtime.provider import COMMON_POLICY
from test_independent_agents import add_fact_usage, request, simulated_answer


class CatalogControllerTests(unittest.TestCase):
    def setUp(self):
        home = Path(__file__).resolve().parents[1] / '.tmp'
        home.mkdir(exist_ok=True)
        self.temporary = tempfile.TemporaryDirectory(prefix='catalog-policy-', dir=home)
        self.root = Path(self.temporary.name)
        self.source = self.root / 'source'
        self.source.mkdir()
        (self.source / 'Registration.cs').write_text(
            'class Registration {\n bool Save(int value) { return value > 0; }\n}\n', encoding='utf-8')
        self.contexts = []
        self.agent = DiscoveryAgent.create(self.source, self.root / 'work', request())

    def tearDown(self):
        self.temporary.cleanup()

    def provider(self, workspace, directory, prompt, schema, timeout):
        context = json.loads(prompt[prompt.index('{"request":'):])
        self.contexts.append(context)
        answer = simulated_answer(context)
        if getattr(self, 'mutate', None):
            self.mutate(context, answer)
        add_fact_usage(context, answer)
        return {'exit_code': 0, 'metadata': {'status': 'passed'}, 'answer': answer}

    def run_agent(self, **kwargs):
        with patch('contextbase_runtime.provider.run_job', side_effect=self.provider):
            return self.agent.run(inline_sources=True, **kwargs)

    def test_policy_and_verification_set_are_host_owned(self):
        self.assertEqual('complete', self.run_agent()['status'])
        author, verifier = self.contexts
        self.assertEqual(catalog.VERSION, author['task']['catalogPolicy'])
        self.assertNotEqual(author['task']['contextId'], verifier['task']['contextId'])
        binding = verifier['task']['classificationBindings']
        self.assertEqual(['catalog.record'], [item['key'] for item in binding])
        self.assertEqual(verifier['verificationView']['records']['catalog.record']['version'], binding[0]['sha256'])
        self.assertEqual(['registration'], catalog.scopes(verifier['task']))

    def test_large_catalog_verifies_without_duplicating_its_full_view(self):
        def large_catalog(context, answer):
            if context['task']['operation'] == 'extract':
                answer['records'][0]['statement'] = 'Synthetic claim ' + 'x' * 350_000
        self.mutate = large_catalog
        self.assertEqual('complete', self.run_agent()['status'])
        author, verifier = self.contexts
        prompt = (COMMON_POLICY + '\nUser task (within that boundary):\n' + POLICY + '\n'
                  + self.agent.session._instruction(verifier['task']) + '\n'
                  + json.dumps(verifier, ensure_ascii=False))
        self.assertLess(len(prompt), 1_048_576,
                        'A repeated verification view must not overflow the transport limit')
        self.assertNotIn('view', verifier['candidate'])
        stored = self.agent.session.store.get(
            'candidates/' + verifier['task']['candidate'] + '.json')
        self.assertEqual(stored['view'], verifier['verificationView'])
        self.assertIn('records', stored['answer'])
        self.assertNotIn('records', verifier['candidate']['answer'])
        self.assertNotIn('currentRecords', verifier)
        projected = {key: deepcopy(value) for key, value in stored.items() if key != 'view'}
        projected['answer'].pop('records')
        projected['recordsLocation'] = 'verificationView.records'
        self.assertEqual(projected, verifier['candidate'])
        self.assertEqual(author['sourceDelivery'], verifier['sourceDelivery'])

    def test_old_flat_function_or_null_metadata_cannot_be_adopted(self):
        def null_metadata(context, answer):
            if context['task']['operation'] == 'extract':
                answer['records'][0]['classification'] = None
        self.mutate = null_metadata
        with self.assertRaisesRegex(ValueError, 'typed classification'):
            self.run_agent()
        self.assertEqual([], self.agent.status()['acceptedRequirements'])

    def test_independent_over_split_finding_blocks_even_when_catalog_passes(self):
        def over_split(context, answer):
            if context['task']['operation'] == 'verify':
                answer['scopeChecks'][0].update(status='fail', reason='Navigation was counted as a main task.')
        self.mutate = over_split
        result = self.run_agent()
        self.assertEqual('needs-investigation', result['status'])
        self.assertEqual([], self.agent.status()['acceptedRequirements'])

    def test_independent_over_merge_finding_blocks_even_when_catalog_passes(self):
        def over_merge(context, answer):
            if context['task']['operation'] == 'verify':
                answer['classificationChecks'][0].update(status='fail', reason='Independent business outcomes were merged.')
        self.mutate = over_merge
        self.assertEqual('needs-investigation', self.run_agent()['status'])
        self.assertEqual([], self.agent.status()['acceptedRequirements'])

    def test_classification_version_cannot_be_replayed(self):
        def stale_check(context, answer):
            if context['task']['operation'] == 'verify':
                answer['classificationChecks'][0]['recordSha256'] = '0' * 64
        self.mutate = stale_check
        with self.assertRaisesRegex(ValueError, 'fingerprint'):
            self.run_agent()
        self.assertEqual([], self.agent.status()['acceptedRequirements'])

    def test_zero_record_scope_still_requires_independent_scope_check(self):
        def empty_catalog(context, answer):
            if context['task']['operation'] == 'extract':
                answer['records'] = []
                answer['coverage'][0]['recordKeys'] = []
            else:
                self.assertEqual([], context['task']['classificationBindings'])
                self.assertEqual(['registration'], catalog.scopes(context['task']))
                answer['scopeChecks'] = []
        self.mutate = empty_catalog
        with self.assertRaises(ValueError):
            self.run_agent()
        self.assertEqual([], self.agent.status()['acceptedRequirements'])

    def test_pending_that_changes_count_blocks_even_with_positive_review(self):
        def pending(context, answer):
            if context['task']['operation'] == 'extract':
                answer['records'][0].update(kind='unclassified', classification={
                    'category': 'pending', 'scope': 'registration', 'tentativeKind': 'function',
                    'impact': 'count-or-coverage', 'reason': 'Business parentage is unknown.', 'unknownIds': ['partition']})
                answer['unknowns'] = [{'id': 'partition', 'question': 'Is this an independent task?',
                    'relatedRequirements': ['catalog'], 'blocksRequirements': ['catalog'],
                    'scopeReason': 'Its classification changes the requested main-function count.'}]
        self.mutate = pending
        result = self.run_agent()
        self.assertEqual('needs-investigation', result['status'])
        self.assertIn('Pending catalog classification', result['pending']['reason'])
        self.assertEqual([], self.agent.status()['acceptedRequirements'])

    def test_semantic_parent_revision_invalidates_cross_owner_child_without_version_dag_edge(self):
        req = request()
        req['goal']['requirements'] = [
            {'id': key, 'stage': 'discovery', 'scope': 'registration', 'question': 'Inspect ' + key, 'requires': []}
            for key in ('parent', 'child')]
        self.agent = DiscoveryAgent.create(self.source, self.root / 'cross-owner', req)
        def child(context, answer):
            if context['task']['operation'] == 'extract' and context['task']['requirements'] == ['child']:
                evidence = answer['records'][0]['evidence']
                answer['records'] = [{'key': 'child.operation', 'ownerRequirement': 'child', 'kind': 'operation',
                    'name': 'Prepare', 'statement': 'Prepare the business operation.', 'basis': 'observed-source',
                    'evidence': evidence, 'dependsOn': [], 'classification': {'category': 'operation',
                        'scope': 'registration', 'parent': 'parent.record', 'purpose': 'Prepare',
                        'useContext': 'Preparation for the parent task', 'outcome': 'Prepared',
                        'rationale': 'A step, not an independent goal.', 'alternative': 'Considered separate outcome.',
                        'entryRefs': ['parent.entry']}}]
                answer['coverage'][0]['recordKeys'] = ['child.operation']
        self.mutate = child
        self.assertEqual('complete', self.run_agent(requirements=['parent'])['status'])
        self.assertEqual('complete', self.run_agent(requirements=['child'])['status'])
        self.assertEqual([], self.agent.status()['records']['child.operation']['dependencies'])
        revised = self.agent.session.revise(['parent'], 'The parent business classification changed.')
        self.assertEqual([], revised['acceptedRequirements'])
        self.assertEqual({'parent', 'child'}, set(revised['invalidatedRequirements']))

    def test_one_entry_can_support_two_business_contexts(self):
        def with_operation(context, answer):
            if context['task']['operation'] == 'extract':
                main = answer['records'][0]
                operation = {**deepcopy(main), 'key': 'catalog.prepare', 'kind': 'operation',
                    'name': 'Prepare input', 'classification': {'category': 'operation',
                        'scope': 'registration', 'parent': 'catalog.record', 'purpose': 'Prepare input',
                        'useContext': 'Editing preparation', 'outcome': 'Input ready',
                        'rationale': 'Same technical entry, subordinate business step.',
                        'alternative': 'Independent inquiry would be a different context.',
                        'entryRefs': ['catalog.entry']}}
                answer['records'].append(operation)
                answer['coverage'][0]['recordKeys'].append(operation['key'])
        self.mutate = with_operation
        self.assertEqual('complete', self.run_agent()['status'])
        self.assertEqual(1, sum(record['kind'] == 'function' for record in self.agent.status()['records'].values()))


if __name__ == '__main__':
    unittest.main()

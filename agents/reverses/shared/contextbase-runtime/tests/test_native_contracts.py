"""Native contract snapshots cannot be weakened through caller-owned objects."""
import unittest

from contextbase_runtime import candidate_amendment as amendment, contracts as c
from contextbase_runtime.native_contracts import ToolContracts
from test_candidate_amendment import fixture


def author_task():
    return {
        'id': 'author',
        'operation': 'extract',
        'stage': 'discovery',
        'origin': 'host-executed',
        'requirements': ['catalog'],
        'goalRequirementIds': ['catalog'],
        'goalRequirements': [{
            'id': 'catalog', 'stage': 'discovery', 'scope': 'all',
            'question': 'Analyze source', 'requires': [],
        }],
        'authorizedSourcePaths': ['A.cs'],
    }


class NativeContractsTests(unittest.TestCase):
    def test_mutating_input_task_cannot_expand_assigned_requirements(self):
        task = author_task()
        contracts = ToolContracts(task)
        task['requirements'].append('outside')
        task['authorizedSourcePaths'].append('outside.cs')
        arguments = {
            'operation_id': 'plan', 'expected_revision': 0,
            'plan': {'units': [{
                'id': 'unit', 'requirement': 'outside',
                'question': 'Outside the assigned goal', 'paths': ['outside.cs'],
            }]},
        }
        with self.assertRaisesRegex(ValueError, 'Invalid native tool arguments'):
            contracts.validate('plan_update', arguments)

    def test_mutating_advertised_schema_cannot_weaken_validation(self):
        contracts = ToolContracts(author_task())
        definitions = contracts.schemas()
        plan = next(item for item in definitions if item['name'] == 'plan_update')
        plan['inputSchema'].clear()
        definitions.append({'name': 'review_submit', 'inputSchema': {}})
        with self.assertRaisesRegex(ValueError, 'required'):
            contracts.validate('plan_update', {})
        with self.assertRaisesRegex(ValueError, 'not authorized'):
            contracts.validate('review_submit', {})
        self.assertNotEqual(definitions, contracts.schemas())

    def test_described_contracts_are_isolated_from_later_reads_and_validation(self):
        contracts = ToolContracts(author_task())
        before = contracts.describe('result', None)
        altered = contracts.describe('result', None)
        altered['schema']['properties']['records']['items']['properties']['kind']['enum'].append('invented')
        self.assertEqual(before, contracts.describe('result', None))
        with self.assertRaisesRegex(ValueError, 'Unknown classification category'):
            contracts.describe('classification', 'invented')

    def test_reviewer_cannot_gain_author_mutations(self):
        task = author_task()
        task.update(operation='verify', candidate='a' * 64, viewSha256='b' * 64,
                    unknownBindings=[])
        contracts = ToolContracts(task)
        names = {item['name'] for item in contracts.schemas()}
        self.assertIn('review_submit', names)
        for name in ('plan_update', 'draft_apply', 'submit_candidate', 'submit_amendment'):
            self.assertNotIn(name, names)
            with self.assertRaisesRegex(ValueError, 'not authorized'):
                contracts.validate(name, {})

    def test_amendment_schema_keeps_exact_seed_and_selection_after_input_mutation(self):
        seed, task, spec, _ = fixture()
        task['requirements'] = [row['id'] for row in task['goalRequirements']]
        task.update(stage=None, jointPolicy=c.JOINT_POLICY,
                    nativeToolsPolicy='contextbase-native-tools/1',
                    executionScope=list(task['requirements']))
        seed.update(schema=amendment.NATIVE_SEED_VERSION, stage=None,
                    jointPolicy=c.JOINT_POLICY, nativeToolsPolicy='contextbase-native-tools/1',
                    requirements=list(task['requirements']))
        spec.update(schema=amendment.NATIVE_VERSION, seedSha256=c.digest(seed), addKinds=[])
        retained = {'seed': seed, 'spec': spec}
        contracts = ToolContracts(task, retained)
        before = contracts.schemas()
        retained['seed']['baseCandidateSha256'] = '0' * 64
        retained['spec']['replaceKeys'].clear()
        task['amendmentOperationId'] = '0' * 64
        self.assertEqual(before, contracts.schemas())
        names = {item['name'] for item in before}
        self.assertIn('submit_amendment', names)
        self.assertNotIn('submit_candidate', names)


if __name__ == '__main__':
    unittest.main()

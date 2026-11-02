"""Normal D/R execution, independent review and replay use compiler bindings."""
from copy import deepcopy
import unittest
from unittest.mock import patch

import test_incremental_agents as fixtures
from contextbase_discovery import DiscoveryAgent
from contextbase_relationship import RelationshipAgent


class SemanticAgentFlowTests(unittest.TestCase):
    def setUp(self):
        self.fixture = fixtures.IncrementalAgentTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.tearDown)
        self.root = self.fixture.root
        source = self.fixture.source
        (source / 'Example.csproj').write_text('<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup>'
            '<TargetFramework>net10.0</TargetFramework></PropertyGroup></Project>', encoding='utf-8')
        (source / 'Entry.cs').write_text('class Entry {\n static void Start() { Registration.Accept(1); }\n}\n', encoding='utf-8')
        (source / 'Registration.cs').write_text('class Registration {\n public static bool Accept(int value) { return value > 0; }\n}\n', encoding='utf-8')

    def create(self, kind, *, handoff=None, name=None):
        agent = kind.create(self.fixture.source, self.root / (name or kind.name), fixtures.request(),
            incremental_mode=True, handoff=handoff,
            semantic_options={'project': 'Example.csproj', 'configuration': 'Release'})
        self.fixture.agents[agent.session.source.root] = agent
        return agent

    def test_normal_discovery_then_relationship_receive_static_bindings_and_adopt(self):
        discovery = self.create(DiscoveryAgent)
        self.assertEqual('complete', self.fixture.run_agent(discovery)['status'])
        relationship = self.create(RelationshipAgent, handoff=discovery.export())
        self.assertEqual('complete', self.fixture.run_agent(relationship)['status'])
        contexts = self.fixture.calls
        self.assertTrue(all(c['task']['semanticPolicy'] == 'contextbase-semantic-evidence/1' for c in contexts))
        self.assertTrue(all(c['task']['semanticIndexSha256'] for c in contexts))
        self.assertTrue(any(c['task']['stage'] == 'discovery' and c['incremental']['phase'] == 'review' for c in contexts))
        self.assertTrue(any(c['task']['stage'] == 'relationship' and c['incremental']['phase'] == 'draft' for c in contexts))
        first_entry = next(c for c in contexts if c['evidenceDialog']['round'] == 1
                           and c['incremental']['phase'] == 'draft'
                           and (c['incremental']['unit'] or {}).get('id') == 'entry-unit')
        initial = first_entry['evidenceDialog']['latestEvidence']
        bindings = [row for p in initial for row in p['reply']['result'].get('semanticBindings', [])]
        self.assertTrue(bindings, 'Normal initial delivery must use the index before the model asks for it')
        self.assertTrue(any(row['status'] == 'resolved' for row in bindings))
        self.assertEqual(relationship.status()['acceptedRequirements'], ['catalog', 'links'])
        self.assertTrue(all(f['data']['resolution'] == 'unresolved'
                            for f in discovery.session.fact_index().by_id.values() if f['kind'] == 'call'))

    def test_incremental_resume_replays_bound_initial_delivery_without_reextracting(self):
        agent = self.create(DiscoveryAgent)
        self.fixture.fail_once = ('draft', 'function-unit')
        with self.assertRaises(RuntimeError):
            self.fixture.run_agent(agent)
        self.fixture.fail_once = None
        before = deepcopy(self.fixture.calls)
        self.fixture.agents[agent.session.source.root] = DiscoveryAgent(agent.work)
        reopened = self.fixture.agents[agent.session.source.root]
        reopened.session.resume(fixtures.request())
        self.assertEqual('complete', self.fixture.run_agent(reopened)['status'])
        old_plan = {c['task']['id'] for c in before if c['incremental']['phase'] == 'plan'}
        new_plan = {c['task']['id'] for c in self.fixture.calls[len(before):] if c['incremental']['phase'] == 'plan'}
        self.assertEqual(set(), new_plan)
        self.assertEqual(1, len(old_plan))
        reopened.export()  # adoption/export replays source, semantic receipts and immutable task bindings

    def test_normal_run_rejects_changed_current_source_before_model_call(self):
        agent = self.create(DiscoveryAgent)
        (self.fixture.source / 'New.cs').write_text('class New {}', encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'Current source differs'):
            self.fixture.run_agent(agent)
        self.assertEqual([], self.fixture.calls)


if __name__ == '__main__':
    unittest.main()

"""The existing one-click entry point also supports opted-in host evidence."""
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from contextbase_discovery import DiscoveryAgent, launch
from contextbase_runtime.config import ProjectProfile
from contextbase_runtime.evidence_dialog import VERSION
from test_reporting import request, synthetic_provider


class EvidenceLaunchTests(unittest.TestCase):
    def setUp(self):
        temporary_root = Path(__file__).resolve().parents[1] / '.tmp'
        temporary_root.mkdir(exist_ok=True)
        self.temporary = tempfile.TemporaryDirectory(prefix='evidence-one-click-', dir=temporary_root)
        self.root = Path(self.temporary.name)
        self.source = self.root / 'source'
        self.source.mkdir()
        self.original = b'class Fixture {\n bool Save() { return true; }\n}\n'
        (self.source / 'Fixture.cs').write_bytes(self.original)
        (self.root / 'request.json').write_text(json.dumps(request()), encoding='utf-8')
        self.config = self.root / 'contextbase.toml'
        self.config.write_text('schema="contextbase-project/1"\ndefault_profile="sample"\n'
            '[profiles.sample]\nsource="source"\nrequest="request.json"\n'
            'output="results"\nwork="work"\ncontext_mode="evidence"\n', encoding='utf-8')
        self.profile = ProjectProfile.load(self.config)
        self.calls = []

    def tearDown(self):
        self.temporary.cleanup()

    def provider(self, workspace, job, prompt, schema, timeout):
        context = json.loads(prompt.rsplit('\n', 1)[-1])
        self.calls.append(deepcopy(context))
        task = context['task']
        wrapper = {'protocol': VERSION, 'taskId': task['id'], 'action': 'requests',
                   'requests': [], 'answer': None, 'workingNotes': ''}
        if context['evidenceDialog']['round'] == 1:
            wrapper['requests'] = [
                {'operation': 'query', 'offset': 0, 'limit': 100,
                 **{key: None for key in ('path', 'kind', 'text', 'caller', 'callee', 'route')}},
                {'operation': 'read', 'path': 'Fixture.cs', 'startLine': 1, 'endLine': None},
            ]
        else:
            # The full index is consulted only by the synthetic reply builder;
            # no full tables are sent to the provider in evidence mode.
            agent = DiscoveryAgent(Path(workspace).parent)
            fixture = {'request': context['request'], **deepcopy(context)}
            fixture['structure'] = agent.session.fact_index().context()
            response = synthetic_provider(workspace, job, json.dumps(fixture), schema, timeout)
            wrapper.update(action='finish', requests=[], answer=response['answer'])
        return {'exit_code': 0, 'metadata': {'status': 'passed'}, 'answer': wrapper}

    def test_one_click_publishes_the_adopted_evidence_result_without_touching_other_work(self):
        protected = {}
        for name in ('discovery-agent', 'relationship-agent', 'behavior-agent'):
            path = self.profile.work(name) / 'keep.txt'
            path.parent.mkdir(parents=True)
            path.write_text('human work for ' + name, encoding='utf-8')
            protected[path] = path.read_bytes()
        with patch('contextbase_runtime.provider.run_job', side_effect=self.provider):
            result = launch.start(self.config, emit=lambda _: None)
        self.assertEqual('complete', result['status'])
        self.assertTrue(result['published'])
        self.assertEqual({'first-inventory', 'second-inventory'}, set(result['acceptedRequirements']))
        output = self.profile.output('discovery-agent').parent
        self.assertTrue(all((output / name).is_file() for name in launch.FILES))
        formal = json.loads((output / 'contextbase.json').read_text(encoding='utf-8'))
        self.assertEqual(result['formalSha256'], formal['sha256'])
        self.assertIn(formal['sha256'], (output / 'review.md').read_text(encoding='utf-8'))
        validation = json.loads((output / 'result/validation.json').read_text(encoding='utf-8'))
        self.assertEqual({'first-inventory', 'second-inventory'},
                         {item['requirement'] for item in validation['answer']['checks']})
        self.assertEqual(self.original, (self.source / 'Fixture.cs').read_bytes())
        for path, data in protected.items():
            self.assertEqual(data, path.read_bytes())
        agent = DiscoveryAgent(Path(result['work']))
        self.assertEqual(VERSION, agent.session.config['evidencePolicy'])
        for task_id in agent.status()['tasks']:
            task = agent.session.store.get('tasks/' + task_id + '/request.json')
            self.assertEqual(VERSION, task['evidencePolicy'])
            self.assertNotIn('wireBinding', task)
        self.assertEqual(8, len(self.calls))
        for context in self.calls:
            self.assertEqual('discovery-agent', context['agent']['name'])
            self.assertEqual('host-evidence-requests', context['sourceDelivery']['mode'])
            self.assertNotIn('files', context['sourceDelivery'])
            self.assertNotIn('symbols', context['structure'])
        home, _ = launch._prepare_home(self.profile)
        self.assertFalse((home / 'staging').exists())

    def test_publish_existing_evidence_work_does_not_start_another_model_run(self):
        manual = self.profile.work('discovery-agent')
        agent = DiscoveryAgent.create(self.source, manual, self.profile.request, evidence_mode=True)
        self.profile.bind(agent)
        with patch('contextbase_runtime.provider.run_job', side_effect=self.provider):
            self.assertEqual('complete', agent.run()['status'])
        with patch('contextbase_runtime.provider.run_job', side_effect=AssertionError('No second inference')) as provider:
            result = launch.start(self.config, publish_work=manual, emit=lambda _: None)
            provider.assert_not_called()
        self.assertTrue(result['published'])
        self.assertEqual(str(manual), result['work'])
        self.assertEqual(agent.export()['sha256'], result['formalSha256'])


if __name__ == '__main__':
    unittest.main()

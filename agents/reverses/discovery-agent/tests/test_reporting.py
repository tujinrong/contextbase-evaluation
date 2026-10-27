"""Reports exercise adopted public discovery runs with synthetic provider replies."""
from copy import deepcopy
import json
from pathlib import Path
import re
import tempfile
import unittest
from unittest.mock import patch
from urllib.parse import unquote

from contextbase_discovery import DiscoveryAgent
from contextbase_discovery.reporting import prepare_report
from contextbase_runtime import catalog, contracts


def request():
    return {'schema': contracts.VERSION, 'projectId': 'report-fixture',
            'goal': {'id': 'inspect', 'question': 'Inspect permitted fixture responsibilities.', 'requirements': [
                {'id': 'first-inventory', 'stage': 'discovery', 'scope': 'first',
                 'question': 'Inventory first scope.', 'requires': []},
                {'id': 'second-inventory', 'stage': 'discovery', 'scope': 'second',
                 'question': 'Inventory second scope.', 'requires': []}]},
            'allowedPaths': ['.'], 'excludedPaths': []}


def synthetic_provider(workspace, job, prompt, schema, timeout):
    context = json.loads(prompt[prompt.index('{"request":'):])
    task = context['task']
    original = context['inventory']['files'][0]
    evidence = {'path': original['path'], 'startLine': 1, 'endLine': 2, 'sha256': original['sha256']}
    if task['operation'] == 'verify':
        answer = {'taskId': task['id'], 'candidateSha256': task['candidate'], 'viewSha256': task['viewSha256'],
                  'checks': [{'requirement': key, 'status': 'pass', 'reason': 'Synthetic check.',
                              'evidence': [evidence]} for key in task['requirements']],
                  'unknownChecks': [], 'unknowns': [], 'findings': [],
                  'sourceFactsSha256': task['sourceFactsSha256'],
                  'factUsageCheck': {'status': 'pass', 'reason': 'Synthetic relevance check.', 'evidence': [evidence]},
                  'classificationChecks': [{'key': item['key'], 'recordSha256': item['sha256'], 'status': 'pass',
                                           'reason': 'Synthetic classification.', 'evidence': [evidence]}
                                          for item in task['classificationBindings']],
                  'scopeChecks': [{'scope': scope, 'status': 'pass', 'reason': 'Synthetic coverage.',
                                   'evidence': [evidence]} for scope in catalog.scopes(task)]}
    else:
        obligations = {item['id']: item for item in task['goalRequirements']}
        records = []
        for key in task['requirements']:
            records += [{'key': key + '.function', 'ownerRequirement': key, 'kind': 'function',
                         'name': key + ' function', 'statement': 'Synthetic user responsibility.',
                         'basis': 'observed-source', 'evidence': [evidence], 'dependsOn': [],
                         'classification': {'category': 'main', 'scope': obligations[key]['scope'],
                            'area': 'Fixture area', 'actors': ['Fixture operator'], 'businessObject': 'Fixture item',
                            'purpose': 'Inspect the fixture', 'trigger': 'Start', 'outcome': 'Fixture inspected',
                            'rationale': 'Synthetic purpose', 'alternative': 'Could be a supporting operation',
                            'entryRefs': [key + '.entry']}},
                        {'key': key + '.entry', 'ownerRequirement': key, 'kind': 'entry',
                         'name': key + ' entry', 'statement': 'Synthetic entry.', 'basis': 'observed-source',
                         'evidence': [evidence], 'dependsOn': [], 'classification': None}]
        facts = [dict(zip(context['structure'][table]['columns'], row))
                 for table in ('symbols', 'calls', 'entries', 'imports')
                 for row in context['structure'][table]['rows']]
        supporting = [item['id'] for item in facts if item['startLine'] <= 2 and item['endLine'] >= 1][:1]
        answer = {'taskId': task['id'], 'records': records,
                  'coverage': [{'requirement': key, 'status': 'supported',
                                'recordKeys': [key + '.function', key + '.entry'], 'evidence': [evidence]}
                               for key in task['requirements']],
                  'unknowns': [], 'followups': [], 'sourceFactsSha256': task['sourceFactsSha256'],
                  'factUsage': [{'recordKey': item['key'], 'factIds': supporting,
                                 'reason': 'Fixture declaration evidence.' if supporting else 'Unsupported fixture.'}
                                for item in records]}
    return {'exit_code': 0, 'metadata': {'status': 'passed'}, 'answer': answer}


class ReportingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='discovery-report-')
        self.root = Path(self.temp.name)
        self.source = self.root / 'independent-source'
        self.source.mkdir()
        (self.source / 'Fixture.cs').write_text('class Fixture {\n bool Save() { return true; }\n}\n', encoding='utf-8')
        self.agent = DiscoveryAgent.create(self.source, self.root / 'work', request())
        self.destination = self.root / 'staging/prepared'
        self.final = self.root / 'results/discovery-agent'

    def tearDown(self):
        self.temp.cleanup()

    def adopted(self, provider=synthetic_provider):
        with patch('contextbase_runtime.provider.run_job', side_effect=provider):
            result = self.agent.run(inline_sources=True)
        self.assertEqual('complete', result['status'])
        return self.agent.export()

    def test_custom_requirements_multiple_scopes_and_final_links_have_one_adopted_version(self):
        envelope = self.adopted()
        summary = prepare_report(self.agent, envelope, self.destination, self.final)
        self.assertEqual(envelope, json.loads((self.destination / 'contextbase.json').read_text(encoding='utf-8')))
        self.assertEqual({'first-inventory', 'second-inventory'}, set(summary['acceptedRequirements']))
        self.assertEqual({'function': 2, 'entry': 2}, summary['recordCounts'])
        self.assertEqual(7, len(summary['files']))
        self.assertEqual(envelope['sha256'], summary['formalSha256'])
        verification = json.loads((self.destination / 'result/validation.json').read_text(encoding='utf-8'))
        self.assertEqual({'first-inventory', 'second-inventory'},
                         {item['requirement'] for item in verification['answer']['checks']})
        review = (self.destination / 'review.md').read_text(encoding='utf-8')
        self.assertIn(envelope['sha256'], review)
        self.assertIn('first\\-inventory function', review)
        self.assertIn('second\\-inventory function', review)
        self.assertNotIn('CSharp_ASPNET', review)
        self.assertNotIn('candidate.json', review)
        source_links = [link for link in re.findall(r'\]\(([^)]+)\)', review) if '#L' in link]
        self.assertTrue(source_links)
        for link in source_links:
            self.assertEqual((self.source / 'Fixture.cs').resolve(),
                             (self.final / unquote(link.split('#', 1)[0])).resolve())
        self.assertFalse((self.destination / 'result/candidate.json').exists())
        self.assertFalse((self.destination / '.tmp').exists())
        self.assertEqual(4, len(re.findall(r'Fixture declaration evidence',
            (self.destination / 'facts/facts-review.md').read_text(encoding='utf-8'))))

    def test_unadopted_result_cannot_create_formal_report(self):
        with self.assertRaisesRegex(ValueError, 'locally adopted'):
            prepare_report(self.agent, {}, self.destination, self.final)
        self.assertFalse(self.destination.exists())

    def test_resealed_wrong_envelope_is_not_a_locally_adopted_result(self):
        envelope = self.adopted()
        wrong = deepcopy(envelope)
        wrong['payload']['request']['projectId'] = 'another-project'
        wrong['sha256'] = contracts.digest(wrong['payload'])
        with self.assertRaisesRegex(ValueError, 'locally adopted export'):
            prepare_report(self.agent, wrong, self.destination, self.final)
        self.assertFalse(self.destination.exists())

    def test_changed_original_source_is_not_silently_linked_to_a_snapshot(self):
        envelope = self.adopted()
        (self.source / 'Fixture.cs').write_text('changed source', encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'Original source changed'):
            prepare_report(self.agent, envelope, self.destination, self.final)
        self.assertFalse(self.destination.exists())

    def test_unrelated_later_verification_is_not_selected_instead_of_active_receipt(self):
        envelope = self.adopted()
        original_get = self.agent.session.store.get

        def damaged(relative):
            item = original_get(relative)
            if relative.startswith('verifications/'):
                item['answer']['viewSha256'] = 'a' * 64
            return item

        with patch.object(self.agent.session.store, 'get', side_effect=damaged):
            with self.assertRaisesRegex(ValueError, 'verification content binding'):
                prepare_report(self.agent, envelope, self.destination, self.final)
        self.assertFalse(self.destination.exists())

    def test_nonempty_staging_is_not_overwritten(self):
        envelope = self.adopted()
        self.destination.mkdir(parents=True)
        marker = self.destination / 'unrelated.txt'
        marker.write_text('preserve', encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'must be empty'):
            prepare_report(self.agent, envelope, self.destination, self.final)
        self.assertEqual('preserve', marker.read_text(encoding='utf-8'))

    def test_adopted_minor_findings_are_visible_in_human_review(self):
        def advisory(*args):
            result = synthetic_provider(*args)
            if 'checks' in result['answer']:
                check = result['answer']['checks'][0]
                result['answer']['findings'] = [{'id': 'advice', 'severity': 'minor',
                    'requirement': check['requirement'], 'detail': 'Human confirmation remains useful.',
                    'evidence': check['evidence']}]
            return result

        envelope = self.adopted(advisory)
        summary = prepare_report(self.agent, envelope, self.destination, self.final)
        review = (self.destination / 'review.md').read_text(encoding='utf-8')
        self.assertIn('Human confirmation remains useful.', review)
        self.assertEqual({'minor': 1}, summary['verificationFindingCounts'])


if __name__ == '__main__':
    unittest.main()

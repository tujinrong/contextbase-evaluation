"""Public discovery consumes snapshot facts and independently checks their use."""
from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from contextbase_discovery import DiscoveryAgent
from test_independent_agents import request, simulated_answer


class FactControllerTests(unittest.TestCase):
    def setUp(self):
        home = Path(__file__).resolve().parents[1] / '.tmp'
        home.mkdir(exist_ok=True)
        self.temporary = tempfile.TemporaryDirectory(prefix='fact-controller-', dir=home)
        self.root = Path(self.temporary.name)
        self.source = self.root / 'source'
        self.source.mkdir()
        self.text = '''using System;
[Route("api/items")]
public class RegistrationController {
 [HttpPost("save")]
 public object Save() {
  Validate();
  return Store();
 }
 void Other() {
  FarAway();
 }
}
'''
        (self.source / 'Registration.cs').write_bytes(self.text.encode('utf-8'))
        self.contexts = []
        self.mutate = None
        self.agent = DiscoveryAgent.create(self.source, self.root / 'work', request())

    def tearDown(self):
        self.temporary.cleanup()

    def provider(self, workspace, job, prompt, schema, timeout):
        context = json.loads(prompt[prompt.index('{"request":'):])
        self.contexts.append(context)
        answer = simulated_answer(context)
        if self.mutate:
            self.mutate(context, answer)
        return {'exit_code': 0, 'metadata': {'status': 'passed'}, 'answer': answer}

    def run_agent(self, agent=None):
        with patch('contextbase_runtime.provider.run_job', side_effect=self.provider):
            return (agent or self.agent).run(inline_sources=True)

    def table(self, context, kind):
        table = context['structure'][kind]
        return [dict(zip(table['columns'], row)) for row in table['rows']]

    def test_real_fact_rows_are_delivered_once_with_original_text_and_same_verification_stamp(self):
        self.assertEqual('complete', self.run_agent()['status'])
        author, verifier = self.contexts
        self.assertNotEqual(author['task']['contextId'], verifier['task']['contextId'])
        self.assertEqual(author['task']['sourceFactsSha256'], verifier['task']['sourceFactsSha256'])
        self.assertEqual(author['structure']['indexSha256'], author['task']['sourceFactsSha256'])
        calls = self.table(author, 'calls')
        self.assertEqual({'Validate', 'Store', 'FarAway'}, {item['name'] for item in calls})
        entries = self.table(author, 'entries')
        self.assertEqual(['api/items/save'], [item['route'] for item in entries])
        self.assertTrue(all(item['id'].startswith('call:') and item['callerId'] for item in calls))
        self.assertNotIn(json.dumps(author['structure'], sort_keys=True),
                         json.dumps(author['assignment'], sort_keys=True))
        for context in self.contexts:
            files = context['sourceDelivery']['files']
            self.assertEqual(self.text, files[0]['sourceText'])
            self.assertNotIn('numberedText', files[0])
        candidate = verifier['candidate']['answer']
        self.assertNotIn('records', candidate)
        self.assertNotIn('currentRecords', verifier)
        self.assertEqual('verificationView.records', verifier['candidate']['recordsLocation'])
        self.assertEqual(set(verifier['verificationView']['records']),
                         {usage['recordKey'] for usage in candidate['factUsage']})
        fact_ids = {item['id'] for kind in ('symbols', 'calls', 'entries', 'imports')
                    for item in self.table(author, kind)}
        for usage in candidate['factUsage']:
            self.assertTrue(usage['factIds'])
            self.assertTrue(set(usage['factIds']).issubset(fact_ids))

    def test_author_cannot_invent_a_fact_identifier(self):
        def forged(context, answer):
            if context['task']['operation'] == 'extract':
                answer['factUsage'][0]['factIds'] = ['call:' + '0' * 64]
        self.mutate = forged
        with self.assertRaises(ValueError):
            self.run_agent()
        self.assertEqual([], self.agent.status()['acceptedRequirements'])
        self.assertEqual(1, len(self.contexts))

    def test_discovery_author_task_and_transport_schema_only_offer_its_owned_record_kinds(self):
        expected = set(DiscoveryAgent.record_kinds)
        observed = []
        def scoped_provider(workspace, job, prompt, schema, timeout):
            context = json.loads(prompt[prompt.index('{"request":'):])
            if context['task']['operation'] == 'extract':
                kinds = context['task'].get('recordKinds')
                self.assertIsNotNone(kinds, 'The author task must declare this agent\'s permitted record kinds')
                self.assertEqual(expected, set(kinds))
                enum = schema['properties']['records']['items']['properties']['kind']['enum']
                self.assertEqual(expected, set(enum))
                self.assertFalse({'fact', 'relation'} & set(enum))
                observed.append(context['task']['id'])
            return self.provider(workspace, job, prompt, schema, timeout)
        with patch('contextbase_runtime.provider.run_job', side_effect=scoped_provider):
            self.assertEqual('complete', self.agent.run(inline_sources=True)['status'])
        self.assertEqual(1, len(observed))

    def test_author_cannot_reuse_the_index_stamp_from_another_snapshot(self):
        other_source = self.root / 'other-source'
        other_source.mkdir()
        (other_source / 'Registration.cs').write_text(self.text + '// A distinct source snapshot.\n', encoding='utf-8')
        other = DiscoveryAgent.create(other_source, self.root / 'other-work', request())
        self.assertEqual('complete', self.run_agent(other)['status'])
        previous_stamp = self.contexts[0]['task']['sourceFactsSha256']
        self.contexts.clear()
        def stale(context, answer):
            if context['task']['operation'] == 'extract':
                self.assertNotEqual(previous_stamp, context['task']['sourceFactsSha256'])
                answer['sourceFactsSha256'] = previous_stamp
        self.mutate = stale
        with self.assertRaises(ValueError):
            self.run_agent()
        self.assertEqual([], self.agent.status()['acceptedRequirements'])

    def test_independent_fact_usage_fail_or_unknown_prevents_adoption(self):
        for status in ('fail', 'unknown'):
            with self.subTest(status=status):
                agent = DiscoveryAgent.create(self.source, self.root / ('work-' + status), request())
                def reject(context, answer):
                    if context['task']['operation'] == 'verify':
                        answer['factUsageCheck'].update(status=status, reason='Synthetic claim relevance remains unsupported.')
                self.mutate = reject
                self.assertEqual('needs-investigation', self.run_agent(agent)['status'])
                self.assertEqual([], agent.status()['acceptedRequirements'])

    def test_existing_fact_must_overlap_the_record_source_evidence(self):
        def disjoint(context, answer):
            if context['task']['operation'] == 'extract':
                far = next(item for item in self.table(context, 'calls') if item['name'] == 'FarAway')
                self.assertGreater(far['startLine'], answer['records'][0]['evidence'][0]['endLine'])
                answer['factUsage'][0]['factIds'] = [far['id']]
        self.mutate = disjoint
        with self.assertRaises(ValueError):
            self.run_agent()
        self.assertEqual([], self.agent.status()['acceptedRequirements'])

    def test_author_must_account_for_every_record_and_cannot_ignore_available_facts(self):
        for change in ('omit-record', 'empty-facts'):
            with self.subTest(change=change):
                agent = DiscoveryAgent.create(self.source, self.root / ('work-' + change), request())
                def incomplete(context, answer):
                    if context['task']['operation'] == 'extract':
                        if change == 'omit-record':
                            answer['factUsage'].pop()
                        else:
                            answer['factUsage'][0]['factIds'] = []
                self.mutate = incomplete
                with self.assertRaises(ValueError):
                    self.run_agent(agent)
                self.assertEqual([], agent.status()['acceptedRequirements'])

    def test_public_query_and_validate_index_use_real_facts_without_a_provider(self):
        from contextbase_discovery.__main__ import main
        source = self.root / 'query-source'
        source.mkdir()
        (source / 'Registration.cs').write_bytes(self.text.encode('utf-8'))
        (source / 'notes.txt').write_text('Synthetic unsupported material.\n', encoding='utf-8')
        agent = DiscoveryAgent.create(source, self.root / 'query-work', request())
        def cli(command, *extra, expected=0):
            with redirect_stdout(io.StringIO()) as output:
                code = main([command, '--work', str(agent.work), *extra])
            result = json.loads(output.getvalue())
            self.assertEqual(expected, code, result)
            return result
        with patch('contextbase_runtime.provider.run_job') as provider:
            calls = cli('query', '--callee', 'Validate')
            self.assertEqual(1, calls['matchedCount'])
            self.assertEqual('Validate', calls['facts'][0]['data']['name'])
            self.assertEqual('call', calls['facts'][0]['kind'])
            entries = cli('query', '--route', 'api/items/save')
            self.assertEqual('entry', entries['facts'][0]['kind'])
            self.assertEqual('POST', entries['facts'][0]['data']['verb'])
            empty = cli('query', '--path', 'notes.txt', '--text', 'no-syntax-match')
            self.assertEqual([], empty['facts'])
            self.assertEqual(0, empty['matchedCount'])
            self.assertEqual('unsupported', empty['files'][0]['status'])
            self.assertEqual('pass', cli('validate-index')['status'])
            cli('query', '--path', 'unknown.cs', expected=1)
            provider.assert_not_called()


if __name__ == '__main__':
    unittest.main()

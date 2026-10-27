"""Optional composition uses independent agents and advances one local slice."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from contextbase.analysis_pipeline import run
from contextbase_runtime import catalog, contracts


class OptionalPipelineTests(unittest.TestCase):
    def test_each_local_slice_uses_three_public_agents_and_portable_reverification(self):
        home = Path(__file__).resolve().parents[3] / '.tmp'
        home.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(prefix='public-agent-pipeline-', dir=home) as temporary:
            root = Path(temporary)
            source = root / 'source'
            source.mkdir()
            (source / 'Rules.java').write_text('class Rules {\n boolean allowed(int value) { return value > 0; }\n}\n',
                                                encoding='utf-8')
            obligations = []
            for scope in ('first', 'second'):
                previous = []
                for stage in contracts.STAGES:
                    identifier = scope + '-' + stage
                    obligations.append({'id': identifier, 'stage': stage, 'scope': scope,
                                        'question': 'Inspect ' + identifier, 'requires': previous})
                    previous = [identifier]
            request = {'schema': contracts.VERSION, 'projectId': 'synthetic-pipeline',
                'goal': {'id': 'inspect', 'question': 'Inspect both scopes.', 'requirements': obligations},
                'allowedPaths': ['.'], 'excludedPaths': []}
            calls = []
            def provider(work, job, prompt, schema, timeout):
                context = json.loads(prompt[prompt.index('{"request":'):])
                task = context['task']
                calls.append(task)
                material = context['inventory']['files'][0]
                evidence = {'path': material['path'], 'sha256': material['sha256'], 'startLine': 1, 'endLine': 2}
                if task['operation'] == 'verify':
                    answer = {'taskId': task['id'], 'candidateSha256': task['candidate'],
                              'viewSha256': task['viewSha256'], 'unknownChecks': [], 'findings': [], 'unknowns': [],
                              'checks': [{'requirement': key, 'status': 'pass', 'reason': 'Synthetic source check.',
                                          'evidence': [evidence]} for key in task['requirements']]}
                    if task.get('catalogPolicy') == catalog.VERSION:
                        answer['classificationChecks'] = [
                            {'key': item['key'], 'recordSha256': item['sha256'], 'status': 'pass',
                             'reason': 'Synthetic classification check.', 'evidence': [evidence]}
                            for item in task['classificationBindings']]
                        answer['scopeChecks'] = [
                            {'scope': scope, 'status': 'pass', 'reason': 'Synthetic scope coverage check.',
                             'evidence': [evidence]} for scope in catalog.scopes(task)]
                else:
                    lookup = {item['id']: item for item in obligations}
                    answer = {'taskId': task['id'], 'unknowns': [], 'followups': [],
                        'records': [{'key': key, 'ownerRequirement': key,
                            'kind': {'discovery': 'function', 'relationship': 'relation', 'behavior': 'fact'}[task['stage']],
                            'name': key, 'statement': 'Synthetic fact.', 'basis': 'observed-source',
                            'evidence': [evidence], 'dependsOn': lookup[key]['requires']} for key in task['requirements']],
                        'coverage': [{'requirement': key, 'status': 'supported', 'recordKeys': [key],
                                      'evidence': [evidence]} for key in task['requirements']]}
                    if task.get('catalogPolicy') == catalog.VERSION:
                        for item in answer['records']:
                            key = item['ownerRequirement']
                            item['classification'] = {
                                'category': 'main', 'scope': lookup[key]['scope'], 'area': 'Synthetic area',
                                'actors': ['Synthetic operator'], 'businessObject': 'Synthetic record',
                                'purpose': 'Process the record', 'trigger': 'Submit', 'outcome': 'Processed',
                                'rationale': 'Observed source responsibility', 'alternative': 'Considered an internal operation',
                                'entryRefs': [key + '.entry']}
                        answer['records'] += [
                            {'key': key + '.entry', 'ownerRequirement': key, 'kind': 'entry',
                             'name': key + ' entry', 'statement': 'Synthetic source entry.', 'basis': 'observed-source',
                             'evidence': [evidence], 'dependsOn': [], 'classification': None}
                            for key in task['requirements']]
                        for item in answer['coverage']:
                            item['recordKeys'].append(item['requirement'] + '.entry')
                if 'sourceFactsSha256' in task:
                    answer['sourceFactsSha256'] = task['sourceFactsSha256']
                    if task['operation'] == 'verify':
                        answer['factUsageCheck'] = {'status': 'pass', 'reason': 'Synthetic independent fact relevance check.',
                                                   'evidence': [evidence]}
                    else:
                        structure = context['structure']
                        facts = [dict(zip(structure[key]['columns'], row))
                            for key in ('symbols', 'calls', 'entries', 'imports') for row in structure[key]['rows']]
                        answer['factUsage'] = []
                        for record in answer['records']:
                            available = [fact['id'] for fact in facts if any(
                                structure['files'][fact['file']]['path'] == ref['path']
                                and fact['startLine'] <= ref['endLine'] and ref['startLine'] <= fact['endLine']
                                for ref in record['evidence'])]
                            answer['factUsage'].append({'recordKey': record['key'], 'factIds': available[:1],
                                'reason': 'Synthetic overlapping source fact.' if available else 'No indexed fact overlaps this source evidence.'})
                return {'exit_code': 0, 'metadata': {'status': 'passed'}, 'answer': answer}
            with patch('contextbase_runtime.provider.run_job', side_effect=provider):
                result = run(source, root / 'work', request, inline_sources=True)
            self.assertEqual('complete', result['status'])
            self.assertEqual(16, len(calls))
            self.assertEqual(['discovery', 'relationship', 'behavior'] * 2,
                             [item['stage'] for item in calls if item['operation'] == 'extract'])
            self.assertEqual(6, len({item['sessionId'] for item in calls}))
            self.assertEqual(2, len(result['handoffs']))
            for item in result['handoffs']:
                self.assertEqual([o['id'] for o in obligations if o['scope'] == item['scope']],
                                 item['handoff']['payload']['acceptedRequirements'])
                self.assertEqual(6, len(item['handoff']['payload']['request']['goal']['requirements']))

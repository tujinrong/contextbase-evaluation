"""Recoverable query errors never become source evidence or new progress."""
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest

from contextbase_runtime import contracts as c, incremental, review_set
from contextbase_runtime.adapters import index_source
from contextbase_runtime.facts import FactIndex
from contextbase_runtime.sources import SourceAccess
from contextbase_runtime.storage import ArtifactStore


class IncrementalRequestRecoveryTests(unittest.TestCase):
    def setUp(self):
        home = Path(__file__).resolve().parents[1] / '.tmp'
        home.mkdir(exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(prefix='incremental-requests-', dir=home)
        self.root = Path(self.temp.name)
        original = self.root / 'original'
        original.mkdir()
        (original / 'A.cs').write_text('class A { }\n', encoding='utf-8')
        self.source = SourceAccess.create(original, self.root / 'snapshot',
            project_id='query-recovery', allowed_paths=['.'], excluded_paths=[])
        self.store = ArtifactStore(self.root / 'work')
        self.index = FactIndex.open(self.source, self.store, parser=index_source)
        obligation = {'id': 'catalog', 'stage': 'discovery', 'scope': 'system',
                      'question': 'Catalog synthetic source', 'requires': []}
        self.task = {'id': 'root-task', 'contextId': 'root-context', 'executionEpoch': 0,
            'sessionId': 'fixture', 'operation': 'extract', 'stage': 'discovery',
            'origin': 'host-executed', 'snapshotId': self.source.snapshot_id,
            'baseVersion': 0, 'baseRevision': None, 'candidate': None, 'viewSha256': None,
            'feedback': None, 'goalRequirements': [obligation], 'goalRequirementIds': ['catalog'],
            'requirements': ['catalog'], 'authorizedSourcePaths': ['A.cs'], 'unknownBindings': [],
            'incrementalPolicy': incremental.VERSION, 'reviewSetPolicy': review_set.VERSION,
            'evidenceIndexSha256': self.index.sha256}
        self.context = {'task': deepcopy(self.task), 'request': {},
            'inventory': self.source.manifest, 'structure': {},
            'currentRecords': {}, 'currentUnknowns': {}}
        self.materials = incremental._collections([{'key': 'a', 'statement': 'draft'}])
        self.calls = []

    def tearDown(self):
        self.temp.cleanup()

    def provider(self, batches, final=None, mutate=None):
        def execute(workspace, job, prompt, schema, timeout):
            context = json.loads(prompt.rsplit('\n', 1)[-1])
            self.calls.append(deepcopy(context))
            number = context['evidenceDialog']['round']
            wrapper = {'protocol': incremental.VERSION, 'taskId': context['task']['id'],
                       'action': 'finish', 'requests': [], 'answer': final or {'value': 'done'},
                       'workingNotes': ''}
            if number <= len(batches):
                wrapper.update(action='requests', requests=batches[number - 1], answer=None)
            if mutate:
                mutate(number)
            return {'exit_code': 0, 'metadata': {'status': 'passed'}, 'answer': wrapper}
        return execute

    def dialog(self, provider, cached=None, result_schema=None):
        return incremental._dialog(self.source, self.index, self.store, self.task,
            self.context, 'plan', None, self.materials, 'Synthetic request recovery.',
            result_schema or c.obj({'value': c.TEXT}), provider, 10, lambda: None, cached)

    @staticmethod
    def read(path='A.cs', start=1, end=1):
        return {'operation': 'read', 'path': path, 'startLine': start, 'endLine': end}

    @staticmethod
    def missing_material():
        return {'operation': 'material', 'collection': 'records', 'key': 'missing',
                'offset': 0, 'limit': 100}

    def test_bad_source_request_returns_bound_error_and_other_batch_evidence_survives(self):
        answer, pointer = self.dialog(self.provider([[self.read('missing.cs'), self.read()]]))
        self.assertEqual({'value': 'done'}, answer)
        dialog = self.calls[-1]['evidenceDialog']
        error, valid = dialog['latestEvidence']
        self.assertEqual('invalid-request', error['reply']['status'])
        self.assertEqual(c.digest(error['request']), error['reply']['requestSha256'])
        self.assertEqual(self.calls[-1]['task']['id'], error['reply']['taskId'])
        self.assertIn('correction', error['reply']['result']['error'])
        self.assertEqual('ok', valid['reply']['status'])
        self.assertEqual('A.cs', valid['reply']['result']['evidence']['path'])
        self.assertTrue(self.store.path('calls/' + pointer + '/complete.json').exists())

    def test_bad_material_can_be_corrected_and_entire_dialog_replays_without_provider(self):
        valid = {'operation': 'material', 'collection': 'records', 'key': 'a',
                 'offset': 0, 'limit': 100}
        answer, pointer = self.dialog(self.provider([[self.missing_material()], [valid]]))
        error = self.calls[1]['evidenceDialog']['latestEvidence'][0]['reply']
        self.assertEqual('invalid-request', error['status'])
        self.assertEqual([], self.calls[1]['evidenceDialog']['retainedEvidence'])
        self.assertEqual([], self.calls[1]['evidenceDialog']['retainedMaterials'])

        def no_provider(*args, **kwargs):
            raise AssertionError('A completed dialog must replay without a provider')

        self.assertEqual((answer, pointer), self.dialog(no_provider, cached=pointer))
        row_path = self.store.path('calls/' + pointer + '/round-0001.json')
        row = self.store.get('calls/' + pointer + '/round-0001.json')
        row['pairs'][0]['reply']['result']['error']['message'] = 'Changed error'
        reply = row['pairs'][0]['reply']
        reply['resultSha256'] = c.digest(reply['result'])
        reply['replySha256'] = c.digest({k: v for k, v in reply.items() if k != 'replySha256'})
        row_path.write_text(json.dumps({'payload': row, 'sha256': c.digest(row)}), encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'trace changed'):
            self.dialog(no_provider, cached=pointer)

    def test_repeated_errors_never_reset_no_progress_guard(self):
        with self.assertRaisesRegex(ValueError, 'no source, material or draft progress'):
            self.dialog(self.provider([[self.missing_material()]] * 4))
        self.assertEqual(3, len(self.calls))

    def test_failed_read_cannot_be_used_as_source_evidence_in_final_answer(self):
        ref = self.source.evidence('A.cs', 1, 1)
        with self.assertRaisesRegex(ValueError, 'not supplied as original text'):
            self.dialog(self.provider([[self.read(start=99, end=99)]], final={'evidence': [ref]}),
                        result_schema=c.obj({'evidence': c.arr(c.EVIDENCE)}))

    def test_source_integrity_error_is_fatal_and_never_sent_as_request_correction(self):
        def corrupt(number):
            if number == 1:
                (self.source.root / 'A.cs').write_text('class Corrupt { }\n', encoding='utf-8')
        with self.assertRaises(ValueError):
            self.dialog(self.provider([[self.read()]], mutate=corrupt))
        self.assertEqual(1, len(self.calls))


if __name__ == '__main__':
    unittest.main()

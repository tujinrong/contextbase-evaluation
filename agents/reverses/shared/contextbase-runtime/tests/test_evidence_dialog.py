"""The host dialog supplies source without promoting delivery into approval."""
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from contextbase_runtime import contracts
from contextbase_runtime.adapters import index_source
from contextbase_runtime.evidence_dialog import VERSION, WINDOW_POLICY, _input_size, replay, run
from contextbase_runtime.facts import FactIndex
from contextbase_runtime.sources import SourceAccess
from contextbase_runtime.storage import ArtifactStore


def query(**changes):
    return {'operation': 'query', 'offset': 0, 'limit': 100, 'path': None,
            'kind': None, 'text': None, 'caller': None, 'callee': None, 'route': None, **changes}


class EvidenceDialogTests(unittest.TestCase):
    def setUp(self):
        home = Path(__file__).resolve().parents[1] / '.tmp'
        home.mkdir(exist_ok=True)
        self.temporary = tempfile.TemporaryDirectory(prefix='evidence-dialog-', dir=home)
        self.root = Path(self.temporary.name)
        original = self.root / 'original'
        original.mkdir()
        self.text = 'class A {\r\n void Save() { Write(); }\r\n void Write() {}\r\n}\r\n'
        (original / 'A.cs').write_bytes(self.text.encode('utf-8'))
        (original / 'same-line.txt').write_text('class A {\r\n', encoding='utf-8', newline='')
        (original / 'oversized.txt').write_text(('x' * 40_000 + '\n') * 3, encoding='utf-8')
        (original / 'metadata.txt').write_text('A distinct acquired material.\n', encoding='utf-8')
        self.source = SourceAccess.create(original, self.root / 'snapshot',
                                         project_id='dialog-test', allowed_paths=['.'], excluded_paths=[])
        self.store = ArtifactStore(self.root / 'work')
        self.index = FactIndex.open(self.source, self.store, parser=index_source)
        self.task = {'id': 'author-task', 'contextId': 'author-context', 'operation': 'extract',
                     'stage': 'discovery', 'origin': 'host-executed', 'requirements': ['catalog'],
                     'goalRequirementIds': ['catalog'], 'snapshotId': self.source.snapshot_id,
                     'goalRequirements': [{'id': 'catalog', 'stage': 'discovery', 'scope': 'all',
                                           'question': 'List the system.', 'requires': []}],
                     'authorizedSourcePaths': ['A.cs'], 'evidencePolicy': VERSION,
                     'evidenceIndexSha256': self.index.sha256,
                     'evidenceWindowPolicy': deepcopy(WINDOW_POLICY)}
        self.ref = self.source.evidence('A.cs', 1, 2)
        self.context = {'task': self.task, 'request': {'question': 'List the system.'},
                        'inventory': self.source.manifest, 'structure': {'availability': 'host-query'},
                        'currentRecords': {}, 'currentUnknowns': {}}
        self.calls, self.jobs = [], []

    def tearDown(self):
        self.temporary.cleanup()

    def read(self, start=1, end=2):
        return {'operation': 'read', 'path': 'A.cs', 'startLine': start, 'endLine': end}

    def answer(self):
        return {'taskId': self.task['id'], 'records': [
            {'key': 'system', 'ownerRequirement': 'catalog', 'kind': 'system',
             'name': 'Synthetic system', 'statement': 'An observed system.',
             'basis': 'observed-source', 'evidence': [self.ref], 'dependsOn': []}],
            'coverage': [{'requirement': 'catalog', 'status': 'supported', 'recordKeys': ['system'],
                          'evidence': [self.ref]}], 'unknowns': [], 'followups': []}

    def wrapper(self, requests=None, answer=None, notes=''):
        return {'protocol': VERSION, 'taskId': self.task['id'],
                'action': 'finish' if answer is not None else 'requests',
                'requests': [] if answer is not None else requests,
                'answer': answer, 'workingNotes': notes}

    def provider(self, steps):
        iterator = iter(steps)

        def invoke(workspace, job, prompt, schema, timeout):
            self.assertEqual(self.source.root, workspace)
            self.assertEqual(13, timeout)
            context = json.loads(prompt.rsplit('\n', 1)[1])
            self.calls.append(context)
            self.jobs.append(job)
            value = next(iterator)
            if callable(value):
                value = value(context)
            return {'exit_code': 0, 'metadata': {'status': 'passed'},
                    'answer': value, 'usage': {'input_tokens': 10, 'output_tokens': 2}}

        return invoke

    def execute(self, steps, check_current=None):
        return run(self.source, self.index, self.store, self.task, self.context, 'Inspect source.',
                   contracts.transport_schema(self.task), self.provider(steps), 13,
                   check_current=check_current)

    def test_source_requests_then_canonical_finish_and_exact_replay(self):
        result = self.execute([self.wrapper([self.read()], notes='Inspect declared source.'),
                               self.wrapper(answer=self.answer())])
        self.assertEqual(self.answer(), result['answer'])
        self.assertEqual('host-assembled-evidence-dialog', result['metadata']['responseOrigin'])
        self.assertEqual(2, result['metadata']['rounds'])
        self.assertEqual({'input_tokens': 20, 'output_tokens': 4}, result['usage'])
        self.assertEqual(2, len(set(self.jobs)))
        self.assertEqual([], self.calls[0]['evidenceDialog']['latestEvidence'])
        self.assertEqual(self.source.read('A.cs', 1, 2),
                         self.calls[1]['evidenceDialog']['latestEvidence'][0]['reply']['result']['sourceText'])
        reopened_store = ArtifactStore(self.store.root)
        reopened_source = SourceAccess.open(self.source.root)
        reopened_index = FactIndex.open(reopened_source, reopened_store, parser=index_source)
        replay(reopened_source, reopened_index, reopened_store, deepcopy(self.task), result['answer'],
               result['metadata']['evidenceTranscriptSha256'])

    def test_prior_source_is_retained_once_for_joint_review(self):
        result = self.execute([self.wrapper([self.read(1, 1)], notes='First row checked.'),
                               self.wrapper([self.read(2, 2)], notes='Need second row.'),
                               self.wrapper(answer=self.answer())])
        last = self.calls[-1]['evidenceDialog']
        self.assertEqual(1, len(last['latestEvidence']))
        self.assertEqual(' void Save() { Write(); }\r\n',
                         last['latestEvidence'][0]['reply']['result']['sourceText'])
        self.assertEqual(2, len(last['deliveryLedger']))
        self.assertEqual(1, len(last['retainedEvidence']))
        retained = last['retainedEvidence'][0]
        self.assertEqual(self.source.evidence('A.cs', 1, 1), retained['evidence'])
        self.assertEqual('class A {\r\n', retained['sourceText'])
        self.assertEqual(1, json.dumps(last, ensure_ascii=False).count('class A {'))
        self.assertLessEqual(last['evidenceWindow']['retainedChars'], WINDOW_POLICY['maxChars'])
        self.assertEqual([], last['evidenceWindow']['evictedMaterials'])
        self.assertEqual('Need second row.', last['workingNotes'])
        replay(self.source, self.index, self.store, self.task, result['answer'],
               result['metadata']['evidenceTranscriptSha256'])

    def test_window_deduplicates_overlapping_source_ranges_against_latest(self):
        result = self.execute([self.wrapper([self.read(1, 3)]), self.wrapper([self.read(2, 4)]),
                               self.wrapper(answer=self.answer())])
        last = self.calls[-1]['evidenceDialog']
        self.assertEqual(1, len(last['retainedEvidence']))
        retained = last['retainedEvidence'][0]
        self.assertEqual(self.source.evidence('A.cs', 1, 1), retained['evidence'])
        self.assertEqual(self.source.read('A.cs', 1, 1), retained['sourceText'])
        self.assertNotEqual(last['latestEvidence'][0]['reply']['replySha256'], retained['replySha256'])
        replay(self.source, self.index, self.store, self.task, result['answer'],
               result['metadata']['evidenceTranscriptSha256'])

    def test_retained_fact_ids_are_deduplicated_across_different_queries(self):
        result = self.execute([self.wrapper([query(kind='symbol', limit=50)]),
                               self.wrapper([query(kind='symbol', path='A.cs', limit=100)]),
                               self.wrapper([self.read()]), self.wrapper(answer=self.answer())])
        retained = self.calls[-1]['evidenceDialog']['retainedEvidence']
        identifiers = [item['fact']['id'] for item in retained if item['kind'] == 'fact']
        self.assertTrue(identifiers)
        self.assertEqual(len(identifiers), len(set(identifiers)))
        replay(self.source, self.index, self.store, self.task, result['answer'],
               result['metadata']['evidenceTranscriptSha256'])

    def test_equal_text_at_different_origins_is_not_deduplicated(self):
        same_read = {'operation': 'read', 'path': 'same-line.txt', 'startLine': 1, 'endLine': 1}
        metadata_read = {'operation': 'read', 'path': 'metadata.txt', 'startLine': 1, 'endLine': 1}
        result = self.execute([self.wrapper([self.read(1, 1)]), self.wrapper([same_read]),
                               self.wrapper([metadata_read]), self.wrapper([self.read(2, 2)]),
                               self.wrapper(answer=self.answer())])
        retained = self.calls[-1]['evidenceDialog']['retainedEvidence']
        equal_sources = [item for item in retained if item['kind'] == 'source'
                         and item['sourceText'] == 'class A {\r\n']
        self.assertEqual({'A.cs', 'same-line.txt'}, {item['evidence']['path'] for item in equal_sources})
        replay(self.source, self.index, self.store, self.task, result['answer'],
               result['metadata']['evidenceTranscriptSha256'])

    def test_capacity_evicts_prior_pages_explicitly_and_replays_deterministically(self):
        steps = lambda: [self.wrapper([self.read(1, 1)]), self.wrapper([self.read(2, 2)]),
                         self.wrapper([self.read(3, 3)]), self.wrapper(answer=self.answer())]
        self.execute(steps())
        full_context = self.calls[-1]
        full_cache = full_context['evidenceDialog']['retainedEvidence']
        self.assertEqual(2, len(full_cache))
        schema = contracts.transport_schema(self.task)
        from contextbase_runtime.evidence_dialog import response_schema
        transport = contracts.transport_schema(self.task, response_schema(self.task, schema))
        limit = (_input_size('Inspect source.', full_context, transport)
                 - len(json.dumps(full_cache, ensure_ascii=False, sort_keys=True, separators=(',', ':'))) + 128)
        self.task = {**self.task, 'id': 'tight-taskx', 'contextId': 'tight-contextx'}
        self.context['task'] = self.task
        self.calls = []
        with patch('contextbase_runtime.evidence_dialog.MAX_INPUT_CHARS', limit):
            result = self.execute(steps())
            last = self.calls[-1]['evidenceDialog']
            self.assertEqual([], last['retainedEvidence'])
            self.assertEqual(2, len(last['evidenceWindow']['evictedMaterials']))
            self.assertEqual(1, len(last['latestEvidence']))
            self.assertEqual(self.source.evidence('A.cs', 3, 3),
                             last['latestEvidence'][0]['reply']['result']['evidence'])
            self.assertLessEqual(last['evidenceWindow']['retainedChars'],
                                 last['evidenceWindow']['effectiveMaxChars'])
            replay(self.source, self.index, self.store, self.task, result['answer'],
                   result['metadata']['evidenceTranscriptSha256'])

    def test_window_policy_is_explicit_and_cannot_be_silently_changed(self):
        self.task['evidenceWindowPolicy']['maxChars'] += 1
        with self.assertRaisesRegex(ValueError, 'exact supported evidence-window policy'):
            self.execute([])
        self.assertEqual([], self.calls)

    def test_two_source_review_finishes_when_both_small_pages_are_visible_together(self):
        """A receipt for A cannot replace its source when jointly checking A+B."""
        self.task['authorizedSourcePaths'].append('metadata.txt')
        second_read = {'operation': 'read', 'path': 'metadata.txt', 'startLine': 1, 'endLine': 1}
        second_ref = self.source.evidence('metadata.txt', 1, 1)
        answer = self.answer()
        answer['records'][0]['evidence'].append(second_ref)
        answer['coverage'][0]['evidence'].append(second_ref)
        expected_texts = {'A.cs': self.source.read('A.cs', 1, 2),
                          'metadata.txt': self.source.read('metadata.txt', 1, 1)}

        def visible_originals(value):
            if isinstance(value, dict):
                ref = value.get('evidence')
                if isinstance(ref, dict) and 'sourceText' in value:
                    yield ref['path'], value['sourceText']
                for child in value.values():
                    yield from visible_originals(child)
            elif isinstance(value, list):
                for child in value:
                    yield from visible_originals(child)

        def review(context):
            visible = dict(visible_originals(context['evidenceDialog']))
            if all(visible.get(path) == text for path, text in expected_texts.items()):
                return self.wrapper(answer=answer)
            missing = next(path for path, text in expected_texts.items() if visible.get(path) != text)
            return self.wrapper([self.read() if missing == 'A.cs' else second_read],
                                notes='Need both exact sources visible to compare them.')

        result = self.execute([review] * 8)
        self.assertEqual('passed', result['metadata']['status'])
        self.assertEqual(3, result['metadata']['rounds'])
        replay(self.source, self.index, self.store, self.task, result['answer'],
               result['metadata']['evidenceTranscriptSha256'])

    def test_query_pointers_do_not_substitute_for_reading_original_source(self):
        with self.assertRaisesRegex(ValueError, 'not supplied as original text'):
            self.execute([self.wrapper([query()]), self.wrapper(answer=self.answer())])

    def test_final_fact_ids_must_have_been_supplied_by_query(self):
        self.task['sourceFactsSha256'] = self.index.sha256
        answer = self.answer()
        answer.update(sourceFactsSha256=self.index.sha256,
                      factUsage=[{'recordKey': 'system', 'factIds': [next(iter(self.index.by_id))],
                                  'reason': 'Synthetic fact reference.'}])
        with self.assertRaisesRegex(ValueError, 'facts not supplied'):
            self.execute([self.wrapper([self.read()]), self.wrapper(answer=answer)])

    def test_fact_query_and_original_read_allow_canonical_fact_usage(self):
        self.task['sourceFactsSha256'] = self.index.sha256
        answer = self.answer()
        fact = next(iter(self.index.by_id))
        answer.update(sourceFactsSha256=self.index.sha256,
                      factUsage=[{'recordKey': 'system', 'factIds': [fact], 'reason': 'Observed declaration.'}])
        result = self.execute([self.wrapper([query(), self.read()]), self.wrapper(answer=answer)])
        replay(self.source, self.index, self.store, self.task, result['answer'],
               result['metadata']['evidenceTranscriptSha256'])

    def test_a_reasonable_reread_is_allowed_but_repetition_without_progress_stops(self):
        result = self.execute([self.wrapper([self.read()]), self.wrapper([self.read()]),
                               self.wrapper(answer=self.answer())])
        self.assertEqual(3, result['metadata']['rounds'])
        other_task = {**self.task, 'id': 'repeat-task', 'contextId': 'repeat-context'}
        self.task = other_task
        self.context['task'] = self.task
        with self.assertRaisesRegex(ValueError, 'without progress'):
            self.execute([self.wrapper([self.read()])] * 4)
        self.assertTrue(self.store.path('tasks/repeat-task/evidence/failure.json').exists())
        self.assertFalse(self.store.path('tasks/repeat-task/evidence/transcript.json').exists())

    def test_outside_source_request_is_rejected_before_finish(self):
        with self.assertRaisesRegex(ValueError, 'outside the sealed'):
            self.execute([self.wrapper([{**self.read(), 'path': '../expected-answer.md'}])])
        self.assertEqual(1, len(self.calls))

    def test_different_empty_searches_stop_without_new_deliveries(self):
        requests = [{'operation': 'search', 'text': 'never-present-' + str(n), 'path': 'A.cs',
                     'offset': 0, 'limit': 10, 'caseSensitive': True} for n in range(3)]
        with self.assertRaisesRegex(ValueError, 'without progress'):
            self.execute([self.wrapper([request]) for request in requests])
        self.assertEqual(3, len(self.calls))

    def test_increasing_out_of_range_offsets_do_not_create_progress(self):
        with self.assertRaisesRegex(ValueError, 'without progress'):
            self.execute([self.wrapper([query(offset=offset)]) for offset in (1000, 2000, 3000)])
        self.assertEqual(3, len(self.calls))

    def test_same_facts_via_different_filters_do_not_reset_progress(self):
        requests = [query(kind='symbol', limit=10), query(kind='symbol', path='A.cs', limit=20),
                    query(kind='symbol', text='A', limit=30),
                    query(kind='symbol', path='A.cs', text='A', limit=40)]
        with self.assertRaisesRegex(ValueError, 'without progress'):
            self.execute([self.wrapper([request]) for request in requests])
        self.assertEqual(4, len(self.calls))

    def test_oversized_rows_never_count_as_new_original_source(self):
        requests = [{'operation': 'read', 'path': 'oversized.txt', 'startLine': n, 'endLine': n}
                    for n in range(1, 4)]
        with self.assertRaisesRegex(ValueError, 'without progress'):
            self.execute([self.wrapper([request]) for request in requests])
        self.assertEqual(3, len(self.calls))

    def test_search_and_read_of_the_same_line_share_delivery_progress(self):
        search = {'operation': 'search', 'text': 'class A', 'path': 'A.cs',
                  'offset': 0, 'limit': 10, 'caseSensitive': True}
        requests = [self.read(1, 1), search, self.read(1, 1), {**search, 'text': 'class'}]
        with self.assertRaisesRegex(ValueError, 'without progress'):
            self.execute([self.wrapper([request]) for request in requests])
        self.assertEqual(4, len(self.calls))

    def test_new_line_extensions_are_progress_without_a_total_round_cap(self):
        result = self.execute([self.wrapper([self.read(1, end)]) for end in range(1, 5)] +
                              [self.wrapper(answer=self.answer())])
        self.assertEqual(5, result['metadata']['rounds'])
        replay(self.source, self.index, self.store, self.task, result['answer'],
               result['metadata']['evidenceTranscriptSha256'])

    def test_new_inventory_materials_are_progress_across_pages(self):
        requests = [{'operation': 'inventory', 'offset': offset, 'limit': 1} for offset in range(3)]
        result = self.execute([self.wrapper([request]) for request in requests] +
                              [self.wrapper([self.read()]), self.wrapper(answer=self.answer())])
        self.assertEqual(5, result['metadata']['rounds'])
        replay(self.source, self.index, self.store, self.task, result['answer'],
               result['metadata']['evidenceTranscriptSha256'])

    def test_already_delivered_inventory_materials_do_not_reset_progress(self):
        requests = [{'operation': 'inventory', 'offset': 0, 'limit': 100},
                    *[{'operation': 'inventory', 'offset': offset, 'limit': 1} for offset in range(3)]]
        with self.assertRaisesRegex(ValueError, 'without progress'):
            self.execute([self.wrapper([request]) for request in requests])
        self.assertEqual(4, len(self.calls))

    def test_capacity_failure_is_detected_before_model_call(self):
        with patch('contextbase_runtime.evidence_dialog.MAX_INPUT_CHARS', 100):
            with self.assertRaisesRegex(ValueError, 'single-call capacity'):
                self.execute([])
        self.assertEqual([], self.calls)
        self.assertTrue(self.store.path('tasks/author-task/evidence/failure.json').exists())

    def test_stale_return_is_not_followed_by_evidence_access_or_finish(self):
        current = True

        def late(context):
            nonlocal current
            current = False
            return self.wrapper([self.read()])

        with self.assertRaisesRegex(ValueError, 'no longer current'):
            self.execute([late], check_current=lambda: current)
        self.assertFalse(self.store.path('tasks/author-task/evidence/round-0001.json').exists())
        self.assertFalse(self.store.path('tasks/author-task/evidence/transcript.json').exists())

    def test_independent_verifier_cannot_reuse_author_deliveries(self):
        self.execute([self.wrapper([self.read(1, 1)]), self.wrapper([self.read(2, 2)]),
                      self.wrapper(answer=self.answer())])
        authored_window = deepcopy(self.calls[-1]['evidenceDialog'])
        self.assertTrue(authored_window['retainedEvidence'])
        self.task = {**self.task, 'id': 'verification-task', 'contextId': 'independent-context',
                     'operation': 'verify', 'candidate': '1' * 64, 'viewSha256': '2' * 64,
                     'unknownBindings': []}
        self.context['task'] = self.task
        self.context['evidenceDialog'] = authored_window
        answer = {'taskId': self.task['id'], 'candidateSha256': self.task['candidate'],
                  'viewSha256': self.task['viewSha256'],
                  'checks': [{'requirement': 'catalog', 'status': 'pass',
                              'reason': 'Claimed independent reading.', 'evidence': [self.ref]}],
                  'unknownChecks': [], 'findings': [], 'unknowns': []}
        def cannot_inherit(context):
            self.assertEqual([], context['evidenceDialog']['latestEvidence'])
            self.assertEqual([], context['evidenceDialog']['retainedEvidence'])
            return self.wrapper(answer=answer)

        with self.assertRaisesRegex(ValueError, 'not supplied as original text'):
            self.execute([cannot_inherit])

    def test_replay_rejects_another_context_or_changed_canonical_answer(self):
        result = self.execute([self.wrapper([self.read()]), self.wrapper(answer=self.answer())])
        stamp = result['metadata']['evidenceTranscriptSha256']
        with self.assertRaisesRegex(ValueError, 'binding changed'):
            replay(self.source, self.index, self.store, {**self.task, 'contextId': 'another-context'},
                   result['answer'], stamp)
        changed = deepcopy(result['answer'])
        changed['records'][0]['statement'] = 'A changed claim.'
        with self.assertRaisesRegex(ValueError, 'binding changed'):
            replay(self.source, self.index, self.store, self.task, changed, stamp)

    def test_replay_rechecks_original_receipt_even_with_resealed_chain(self):
        result = self.execute([self.wrapper([self.read()]), self.wrapper(answer=self.answer())])
        prefix = 'tasks/author-task/evidence'

        def replace(name, payload):
            self.store.path(name).write_text(json.dumps({'sha256': contracts.digest(payload), 'payload': payload}),
                                              encoding='utf-8')

        record = self.store.get(prefix + '/round-0001.json')
        receipt = record['pairs'][0]['reply']
        receipt['result']['sourceText'] = 'forged original source\n'
        receipt['resultSha256'] = contracts.digest(receipt['result'])
        receipt['replySha256'] = contracts.digest({k: v for k, v in receipt.items() if k != 'replySha256'})
        replace(prefix + '/round-0001.json', record)
        # A locally resealed chain still cannot make fake bytes replay as source.
        transcript = self.store.get(prefix + '/transcript.json')
        transcript['rounds'][0]['sha256'] = contracts.digest(record)
        replace(prefix + '/transcript.json', transcript)
        with self.assertRaisesRegex(ValueError, 'source replay'):
            replay(self.source, self.index, self.store, self.task, result['answer'], contracts.digest(transcript))

    def test_cross_index_task_is_rejected(self):
        self.task['evidenceIndexSha256'] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'another fact index'):
            self.execute([])
        self.assertEqual([], self.calls)

    def test_finish_cannot_mix_queries_and_canonical_answer(self):
        wrapper = self.wrapper(answer=self.answer())
        wrapper['requests'] = [self.read()]
        with self.assertRaisesRegex(ValueError, 'empty request list'):
            self.execute([wrapper])


if __name__ == '__main__':
    unittest.main()

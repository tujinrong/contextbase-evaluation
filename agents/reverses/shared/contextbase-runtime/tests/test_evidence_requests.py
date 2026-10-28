"""Manifest-only directory selectors and replayable, correctable request errors."""
from collections import Counter
from copy import deepcopy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from contextbase_runtime import contracts
from contextbase_runtime.adapters import index_source
from contextbase_runtime.evidence import EvidenceAccess, EvidenceRequestError
from contextbase_runtime.evidence_dialog import _DeliveryProgress
from contextbase_runtime.facts import FactIndex
from contextbase_runtime.sources import SourceAccess
from contextbase_runtime.storage import ArtifactStore
from test_evidence_access import query, search


class EvidenceRequestTests(unittest.TestCase):
    def setUp(self):
        home = Path(__file__).resolve().parents[1] / '.tmp'
        home.mkdir(exist_ok=True)
        self.temporary = tempfile.TemporaryDirectory(prefix='evidence-requests-', dir=home)
        self.root = Path(self.temporary.name)
        original = self.root / 'original'
        for directory in ('deployment/nested', 'deployment/private', 'deployment-old', 'empty-dir'):
            (original / directory).mkdir(parents=True, exist_ok=True)
        sources = {
            'deployment/First.cs': 'class First { void Save() { Write(); } void Write() {} }\n',
            'deployment/nested/Second.cs': 'class Second { void Save() { Write(); } void Write() {} }\n',
            'deployment/schema.sql': 'CREATE TABLE item(id int);\nSELECT id FROM item;\n',
            'deployment/private/hidden.cs': 'class Hidden {}\n',
            'deployment-old/Other.cs': 'class Other { void Save() { Write(); } void Write() {} }\n',
            'Root.cs': 'class Root {}\n',
        }
        for name, text in sources.items():
            (original / name).write_text(text, encoding='utf-8')
        self.source = SourceAccess.create(original, self.root / 'snapshot', project_id='directory-fixture',
                                          allowed_paths=['.'], excluded_paths=['deployment/private'])
        self.index = FactIndex.open(self.source, ArtifactStore(self.root / 'work'), parser=index_source)
        self.task = {'id': 'query-task', 'contextId': 'query-context',
                     'snapshotId': self.source.snapshot_id, 'sourceFactsSha256': self.index.sha256}
        self.access = EvidenceAccess(self.source, self.index, self.task)

    def tearDown(self):
        self.temporary.cleanup()

    def respond(self, request):
        try:
            return self.access.handle(request)
        except EvidenceRequestError as exc:
            return self.access.error_reply(request, exc)

    def test_real_deployment_directory_query_pages_exact_manifest_subtree(self):
        request = query(path='deployment/', kind='call', limit=1)
        rows, offset, coverage = [], 0, []
        while True:
            current = {**request, 'offset': offset}
            reply = self.access.handle(current)
            self.assertEqual('ok', reply['status'])
            self.access.verify_reply(current, reply)
            result = reply['result']
            coverage.append(result['coverage'])
            rows.extend(result['facts'])
            if not result['truncated']:
                break
            self.assertGreater(result['nextOffset'], offset)
            offset = result['nextOffset']
        expected = [fact for fact in self.index.query(kind='call')['facts']
                    if fact['path'].startswith('deployment/')]
        self.assertEqual(expected, rows)
        self.assertEqual(2, len(rows))
        self.assertTrue(all(row['path'] != 'deployment-old/Other.cs' for row in rows))
        self.assertTrue(all(item == coverage[0] for item in coverage))
        self.assertEqual(3, coverage[0]['fileCount'])
        self.assertEqual(1, coverage[0]['selector']['omittedMaterialCount'])
        self.assertTrue(coverage[0]['selector']['observed'])

    def test_directory_search_pages_original_unsupported_text_and_keeps_coverage(self):
        first_request = search('item', path='deployment/', limit=1)
        first = self.access.handle(first_request)['result']
        second_request = {**first_request, 'offset': first['nextOffset']}
        second = self.access.handle(second_request)['result']
        self.assertEqual(2, first['matchedCount'])
        self.assertEqual(first['coverage'], second['coverage'])
        self.assertEqual(['deployment/schema.sql'] * 2,
                         [item['evidence']['path'] for item in first['matches'] + second['matches']])
        expected_statuses = Counter(row['status'] for row in self.index.document['files']
                                    if row['path'].startswith('deployment/'))
        self.assertEqual(dict(expected_statuses), first['coverage']['parserStatusCounts'])

    def test_nested_prefix_does_not_include_parent_siblings(self):
        result = self.access.handle(query(path='deployment/nested/'))['result']
        self.assertEqual(1, result['coverage']['fileCount'])
        self.assertTrue(all(row['path'] == 'deployment/nested/Second.cs' for row in result['facts']))

    def test_empty_and_unobserved_prefixes_do_not_claim_directory_existence(self):
        for selector in ('empty-dir/', 'missing-dir/'):
            with self.subTest(selector=selector):
                result = self.access.handle(query(path=selector))['result']
                self.assertEqual([], result['facts'])
                self.assertEqual(0, result['matchedCount'])
                self.assertFalse(result['truncated'])
                self.assertEqual(0, result['coverage']['fileCount'])
                self.assertFalse(result['coverage']['selector']['observed'])

    def test_omitted_prefix_and_ancestor_remain_metadata_only(self):
        for selector in ('deployment/private/', 'deployment/private/deeper/'):
            with self.subTest(selector=selector):
                result = self.access.handle(search('Hidden', path=selector))['result']
                self.assertEqual([], result['matches'])
                self.assertEqual(0, result['coverage']['fileCount'])
                self.assertEqual(1, result['coverage']['selector']['omittedMaterialCount'])
                self.assertTrue(result['coverage']['selector']['observed'])

    def test_read_still_requires_an_exact_acquired_file(self):
        for path in ('deployment/', 'deployment/private/hidden.cs', 'missing.cs'):
            with self.subTest(path=path), self.assertRaises(EvidenceRequestError):
                self.access.handle({'operation': 'read', 'path': path, 'startLine': 1, 'endLine': None})
        reply = self.access.handle({'operation': 'read', 'path': 'deployment/First.cs',
                                    'startLine': 1, 'endLine': None})
        self.assertEqual('ok', reply['status'])
        self.assertEqual('deployment/First.cs', reply['result']['evidence']['path'])

    def test_noncanonical_directory_requests_do_not_reach_fact_lookup(self):
        selectors = ('../', '/deployment/', 'C:/deployment/', 'C:deployment/',
                     'deployment//', 'deployment/../', './deployment/', 'deployment\\')
        with patch.object(self.index, 'query', side_effect=AssertionError('Invalid selectors must not be queried')):
            for selector in selectors:
                with self.subTest(selector=selector), self.assertRaises(EvidenceRequestError):
                    self.access.handle(query(path=selector))

    def test_correctable_request_receipt_binds_task_context_snapshot_index_and_replays(self):
        request = query(path='../deployment/')
        reply = self.respond(request)
        self.assertEqual('invalid-request', reply['status'])
        self.assertEqual(contracts.digest(request), reply['requestSha256'])
        for field in ('taskId', 'contextId', 'snapshotId', 'indexSha256'):
            self.assertEqual(self.access.binding[field], reply[field])
        self.assertEqual({'error'}, set(reply['result']))
        self.assertEqual({'code', 'message', 'correction'}, set(reply['result']['error']))
        self.assertTrue(all(reply['result']['error'].values()))
        self.access.verify_reply(request, reply)
        other = EvidenceAccess(self.source, self.index, {**self.task, 'contextId': 'other-context'})
        with self.assertRaises(ValueError):
            other.verify_reply(request, reply)

    def test_bad_range_and_numeric_parameters_are_request_errors(self):
        requests = [query(offset=1.0), query(limit=0),
                    {'operation': 'read', 'path': 'Root.cs', 'startLine': 4, 'endLine': 2}]
        for request in requests:
            with self.subTest(request=request), self.assertRaises(EvidenceRequestError):
                self.access.handle(request)

    def test_invalid_error_receipt_does_not_become_new_data_or_override_valid_request(self):
        request = query(path='../deployment/')
        reply = self.respond(request)
        progress = _DeliveryProgress()
        pair = {'request': request, 'reply': reply}
        self.assertFalse(progress.consume([pair]))
        self.assertFalse(progress.consume([pair]))
        self.assertFalse(progress.consume([pair]))
        fabricated = self.access.error_reply(query(path=None),
            EvidenceRequestError('bad-path', 'Untrue failure', 'Try something else'))
        with self.assertRaises(ValueError):
            self.access.verify_reply(query(path=None), fabricated)

    def test_mixed_batch_replays_valid_invalid_and_repaired_requests(self):
        requests = [query(path='deployment/', kind='call'), query(path='deployment//'),
                    search('item', path='deployment/schema.sql')]
        pairs = [(request, self.respond(request)) for request in requests]
        self.assertEqual(['ok', 'invalid-request', 'ok'], [reply['status'] for _, reply in pairs])
        self.access.verify_replies(pairs)
        changed = deepcopy(pairs[1][1])
        changed['result']['error']['code'] = 'forged-error'
        changed['resultSha256'] = contracts.digest(changed['result'])
        changed['replySha256'] = contracts.digest({key: value for key, value in changed.items()
                                                  if key != 'replySha256'})
        with self.assertRaises(ValueError):
            self.access.verify_reply(requests[1], changed)

    def test_source_integrity_failure_is_never_a_correctable_request_error(self):
        (self.source.root / 'sources/Root.cs').write_bytes(b'changed sealed source\n')
        with self.assertRaises(ValueError) as raised:
            self.respond(query(path='deployment/'))
        self.assertNotIsInstance(raised.exception, EvidenceRequestError)

    def test_index_integrity_failure_is_never_a_correctable_request_error(self):
        self.index.document['facts'][0]['data']['name'] = 'changed indexed observation'
        with self.assertRaises(ValueError) as raised:
            self.respond(query(path='deployment/'))
        self.assertNotIsInstance(raised.exception, EvidenceRequestError)

    def test_error_reply_itself_does_not_hide_source_integrity_failure(self):
        error = EvidenceRequestError('bad-path', 'Bad request', 'Use a manifest path')
        (self.source.root / 'sources/Root.cs').write_bytes(b'changed sealed source\n')
        with self.assertRaises(ValueError) as raised:
            self.access.error_reply(query(path='../'), error)
        self.assertNotIsInstance(raised.exception, EvidenceRequestError)

    def test_exact_file_and_null_query_reply_keep_previous_shape_and_values(self):
        for selector in ('deployment/First.cs', None):
            with self.subTest(selector=selector):
                request = query(path=selector)
                found = self.index.query(**({'path': selector} if selector is not None else {}))
                files = [row for row in self.index.document['files'] if selector is None or row['path'] == selector]
                coverage = {'fileCount': len(files), 'parserStatusCounts': dict(Counter(row['status'] for row in files)),
                            'meaning': 'Syntax observations only; unsupported or partial files are not evidence of absence.'}
                expected = self.access._page(request, found['facts'], 'facts', {
                    'matchBasis': found['matchBasis'], 'coverage': coverage})
                actual = self.access.handle(request)
                self.assertEqual(expected, actual)
                self.assertEqual(contracts.digest(expected), contracts.digest(actual))


if __name__ == '__main__':
    unittest.main()

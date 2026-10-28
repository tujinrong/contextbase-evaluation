"""Host evidence pages preserve source data, authority, and replay identity."""
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from contextbase_runtime import contracts
from contextbase_runtime.adapters import index_source
from contextbase_runtime.evidence import EvidenceAccess, MAX_REPLY_CHARS, REQUEST_SCHEMA
from contextbase_runtime.facts import FactIndex
from contextbase_runtime.sources import SourceAccess
from contextbase_runtime.storage import ArtifactStore


def query(**changes):
    return {'operation': 'query', 'offset': 0, 'limit': 20, 'path': None,
            'kind': None, 'text': None, 'caller': None, 'callee': None, 'route': None, **changes}


def search(text, **changes):
    return {'operation': 'search', 'text': text, 'path': None, 'offset': 0,
            'limit': 20, 'caseSensitive': True, **changes}


class EvidenceAccessTests(unittest.TestCase):
    def setUp(self):
        home = Path(__file__).resolve().parents[1] / '.tmp'
        home.mkdir(exist_ok=True)
        self.temporary = tempfile.TemporaryDirectory(prefix='evidence-access-', dir=home)
        self.root = Path(self.temporary.name)
        original = self.root / 'original'
        original.mkdir()
        self.cs = 'class A {\r\n void Save() { Write(); Write(); }\r\n void Write() {}\r\n}\r\n'
        (original / 'A.cs').write_bytes(self.cs.encode('utf-8'))
        self.sql = "-- 名前\u2028は同じ行\r\nCREATE TABLE item(id int);\r\nSELECT id FROM item;\r\n"
        (original / 'schema.sql').write_bytes(self.sql.encode('utf-8'))
        (original / 'empty.txt').write_bytes(b'')
        (original / 'page.txt').write_bytes(('一' * 80 + '\r\n').encode('utf-8') * 20)
        (original / 'large.txt').write_bytes(('x' * (MAX_REPLY_CHARS + 1) + '\n').encode('utf-8'))
        (original / '.env').write_bytes(b'not an acquired source')
        self.source = SourceAccess.create(original, self.root / 'snapshot', project_id='synthetic-evidence',
                                          allowed_paths=['.'], excluded_paths=[])
        self.index = FactIndex.open(self.source, ArtifactStore(self.root / 'work'), parser=index_source)
        self.task = {'id': 'author-task', 'contextId': 'independent-context',
                     'snapshotId': self.source.snapshot_id, 'sourceFactsSha256': self.index.sha256}
        self.access = EvidenceAccess(self.source, self.index, self.task)

    def tearDown(self):
        self.temporary.cleanup()

    def test_read_preserves_crlf_unicode_and_exact_full_line_evidence(self):
        request = {'operation': 'read', 'path': 'schema.sql', 'startLine': 1, 'endLine': None}
        reply = self.access.handle(request)
        result = reply['result']
        self.assertEqual(self.sql, result['sourceText'])
        self.assertEqual(3, result['returnedCount'])
        self.assertEqual(self.source.evidence('schema.sql', 1, 3), result['evidence'])
        self.assertFalse(result['truncated'])
        self.assertIsNone(result['nextLine'])
        self.assertEqual(self.task['id'], reply['taskId'])
        self.assertEqual(self.task['contextId'], reply['contextId'])
        self.assertEqual(contracts.digest(request), reply['requestSha256'])
        self.assertEqual(contracts.digest(result), reply['resultSha256'])
        self.access.verify_reply(request, reply)

    def test_read_pages_whole_rows_and_can_reconstruct_original_bytes(self):
        request = {'operation': 'read', 'path': 'page.txt', 'startLine': 1, 'endLine': None}
        pages = []
        with patch('contextbase_runtime.evidence.MAX_REPLY_CHARS', 1400):
            while True:
                reply = self.access.handle(request)
                self.assertEqual('ok', reply['status'])
                self.assertLessEqual(self.access._size(reply), 1400)
                result = reply['result']
                self.assertTrue(result['sourceText'].endswith('\r\n'))
                self.source.verify_evidence(result['evidence'])
                pages.append(result['sourceText'])
                if not result['truncated']:
                    break
                self.assertGreater(result['nextLine'], request['startLine'])
                request = {**request, 'startLine': result['nextLine']}
        self.assertGreater(len(pages), 1)
        self.assertEqual(self.source.read('page.txt'), ''.join(pages))

    def test_oversized_row_is_explicit_and_does_not_claim_read_evidence(self):
        reply = self.access.handle({'operation': 'read', 'path': 'large.txt',
                                    'startLine': 1, 'endLine': 1})
        self.assertEqual('oversized-item', reply['status'])
        self.assertEqual('', reply['result']['sourceText'])
        self.assertEqual(0, reply['result']['returnedCount'])
        self.assertIsNone(reply['result']['evidence'])
        self.assertTrue(reply['result']['truncated'])
        self.assertLessEqual(self.access._size(reply), MAX_REPLY_CHARS)

    def test_empty_source_is_observed_without_fabricating_nonempty_evidence(self):
        reply = self.access.handle({'operation': 'read', 'path': 'empty.txt',
                                    'startLine': 1, 'endLine': None})
        self.assertEqual('ok', reply['status'])
        self.assertEqual(0, reply['result']['matchedCount'])
        self.assertFalse(reply['result']['truncated'])
        self.assertIsNone(reply['result']['evidence'])

    def test_query_pagination_keeps_ids_and_syntax_resolution_limits(self):
        request = query(kind='call', callee='Write', limit=1)
        first = self.access.handle(request)['result']
        second = self.access.handle({**request, 'offset': first['nextOffset']})['result']
        expected = self.index.query(kind='call', callee='Write')['facts']
        self.assertEqual(expected, first['facts'] + second['facts'])
        self.assertEqual(2, first['matchedCount'])
        self.assertEqual(1, first['returnedCount'])
        self.assertTrue(first['truncated'])
        self.assertFalse(second['truncated'])
        self.assertTrue(all(item['data']['resolution'] == 'unresolved' for item in expected))
        self.assertNotIn('files', first, 'Do not resend the full index file table per lookup')

    def test_literal_search_reads_unsupported_material_and_reports_partial_pages(self):
        first = self.access.handle(search('item', path='schema.sql', limit=1))['result']
        second = self.access.handle(search('item', path='schema.sql', limit=1,
                                           offset=first['nextOffset']))['result']
        self.assertEqual(2, first['matchedCount'])
        self.assertEqual({'unsupported': 1}, first['coverage']['parserStatusCounts'])
        self.assertEqual('CREATE TABLE item(id int);\r\n', first['matches'][0]['sourceText'])
        self.assertEqual('SELECT id FROM item;\r\n', second['matches'][0]['sourceText'])
        for result in [first, second]:
            self.source.verify_evidence_many(row['evidence'] for row in result['matches'])
        no_match = self.access.handle(search('ITEM', path='schema.sql'))['result']
        insensitive = self.access.handle(search('ITEM', path='schema.sql', caseSensitive=False))['result']
        self.assertEqual(0, no_match['matchedCount'])
        self.assertEqual(2, insensitive['matchedCount'])

    def test_inventory_includes_omission_and_parser_limitations_with_exact_paging(self):
        all_rows, offset = [], 0
        while True:
            result = self.access.handle({'operation': 'inventory', 'offset': offset, 'limit': 1})['result']
            all_rows.extend(result['materials'])
            if not result['truncated']:
                break
            offset = result['nextOffset']
        self.assertEqual(len(self.source.paths) + 1, len(all_rows))
        self.assertTrue(any(row['materialKind'] == 'omitted' and row['path'] == '.env' for row in all_rows))
        self.assertTrue(any(row.get('parserStatus') == 'unsupported' for row in all_rows))
        self.assertNotIn('sourceRoot', json.dumps(all_rows))

    def test_unacquired_or_noncanonical_paths_are_rejected_for_every_operation(self):
        for path in ['../A.cs', '/A.cs', 'C:/A.cs', 'sub\\A.cs', '.env', 'missing.cs']:
            for request in [query(path=path), search('class', path=path),
                            {'operation': 'read', 'path': path, 'startLine': 1, 'endLine': 1}]:
                with self.subTest(path=path, operation=request['operation']), self.assertRaises(ValueError):
                    self.access.handle(request)

    def test_invalid_types_fields_and_ranges_are_rejected(self):
        invalid = [query(offset=True), query(offset=1.0), query(offset=-1), query(limit=0), query(limit=101),
                   query(kind='resolved-call'), query(text=''), query(text='x' * 257),
                   {**query(), 'unknown': 'not allowed'}, {'operation': 'query'},
                   search('x', caseSensitive='false'), search('x', limit=False),
                   {'operation': 'read', 'path': 'A.cs', 'startLine': True, 'endLine': 1},
                   {'operation': 'read', 'path': 'A.cs', 'startLine': 1, 'endLine': 1.0},
                   {'operation': 'read', 'path': 'A.cs', 'startLine': 2, 'endLine': 1},
                   {'operation': 'read', 'path': 'A.cs', 'startLine': 1, 'endLine': 999}]
        for request in invalid:
            with self.subTest(request=request), self.assertRaises(ValueError):
                self.access.handle(request)

    def test_replay_rejects_wrong_context_request_and_rehashed_fabricated_text(self):
        request = {'operation': 'read', 'path': 'A.cs', 'startLine': 1, 'endLine': 2}
        reply = self.access.handle(request)
        other = EvidenceAccess(self.source, self.index, {**self.task, 'contextId': 'reviewer-context'})
        with self.assertRaises(ValueError):
            other.verify_reply(request, reply)
        with self.assertRaises(ValueError):
            self.access.verify_reply({**request, 'endLine': 3}, reply)
        tampered = deepcopy(reply)
        tampered['result']['sourceText'] = 'invented source\n'
        tampered['resultSha256'] = contracts.digest(tampered['result'])
        tampered['replySha256'] = contracts.digest({k:v for k,v in tampered.items() if k != 'replySha256'})
        with self.assertRaises(ValueError):
            self.access.verify_reply(request, tampered)

    def test_constructor_rejects_stale_snapshot_or_index_bindings(self):
        for field in ['snapshotId', 'sourceFactsSha256', 'evidenceIndexSha256']:
            with self.subTest(field=field), self.assertRaises(ValueError):
                EvidenceAccess(self.source, self.index, {**self.task, field: '0' * 64})

    def test_later_stage_index_binding_is_checked_without_discovery_fact_policy(self):
        task = {key: value for key, value in self.task.items() if key != 'sourceFactsSha256'}
        with self.assertRaisesRegex(ValueError, 'another source-fact index'):
            EvidenceAccess(self.source, self.index, {**task, 'evidenceIndexSha256': '0' * 64})
        accepted = EvidenceAccess(self.source, self.index, {**task, 'evidenceIndexSha256': self.index.sha256})
        self.assertEqual(self.index.sha256, accepted.handle(query())['indexSha256'])

    def test_transcript_replay_batches_raw_reads_and_keeps_global_integrity_checks(self):
        requests = [{'operation': 'read', 'path': 'A.cs', 'startLine': 1, 'endLine': 2},
                    search('item', path='schema.sql'), query(kind='call')]
        pairs = [(request, self.access.handle(request)) for request in requests]
        with patch.object(self.source, 'read', side_effect=AssertionError('No repeated source read')):
            self.access.verify_replies(pairs)
        def changing():
            yield pairs[0]
            (self.source.root / 'sources/empty.txt').write_bytes(b'new unreferenced material')
            yield from pairs[1:]
        with self.assertRaises(ValueError):
            self.access.verify_replies(changing())

    def test_unreferenced_source_mutation_during_lookup_invalidates_reply(self):
        real = self.index.query
        def changing(**kwargs):
            result = real(**kwargs)
            (self.source.root / 'sources/schema.sql').write_bytes(b'changed unreferenced material\n')
            return result
        with patch.object(self.index, 'query', side_effect=changing), self.assertRaises(ValueError):
            self.access.handle(query(path='A.cs'))

    def test_mutable_fact_document_or_by_id_cannot_bypass_replay(self):
        self.index.document['facts'][0]['data']['name'] = 'forged'
        with self.assertRaises(ValueError):
            self.access.handle(query())

    def test_request_schema_all_branches_have_explicit_fields_for_strict_transport(self):
        for branch in REQUEST_SCHEMA['anyOf']:
            self.assertEqual(set(branch['properties']), set(branch['required']))
            self.assertFalse(branch['additionalProperties'])


if __name__ == '__main__':
    unittest.main()

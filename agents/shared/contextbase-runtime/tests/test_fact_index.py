"""Exercise the source-fact interface against sealed, artificial source."""
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest

from contextbase_runtime import contracts
from contextbase_runtime.adapters import index_source
from contextbase_runtime.facts import FactIndex
from contextbase_runtime.sources import SourceAccess
from contextbase_runtime.storage import ArtifactStore


class FactIndexTests(unittest.TestCase):
    def setUp(self):
        home = Path(__file__).resolve().parents[1] / '.tmp'
        home.mkdir(exist_ok=True)
        self.temporary = tempfile.TemporaryDirectory(prefix='source-facts-', dir=home)
        self.root = Path(self.temporary.name)
        source = self.root / 'source'
        source.mkdir()
        (source / 'A.cs').write_text('class A {\n void Save() { Write(); }\n void Write() {}\n}\n', encoding='utf-8')
        (source / 'B.cs').write_text('class B { void Write() {} }\n', encoding='utf-8')
        (source / 'data.sql').write_text('CREATE TABLE example (id int);\n', encoding='utf-8')
        self.source = SourceAccess.create(source, self.root / 'snapshot', project_id='synthetic',
                                          allowed_paths=['.'], excluded_paths=[])
        self.store = ArtifactStore(self.root / 'cache')
        self.calls = []

    def tearDown(self):
        self.temporary.cleanup()

    def parser(self, path, text, **kwargs):
        self.calls.append(path)
        return index_source(path, text, **kwargs)

    def open(self, **kwargs):
        return FactIndex.open(self.source, self.store, parser=self.parser, **kwargs)

    def test_cache_hit_skips_parsing_but_keeps_same_validated_index(self):
        first = self.open()
        self.assertEqual(3, len(self.calls))
        again = self.open()
        self.assertEqual(first.document, again.document)
        self.assertEqual(3, len(self.calls))
        self.assertEqual('pass', again.validate()['status'])

    def test_changed_extractor_uses_another_cache(self):
        first = self.open(extractor_sha256=contracts.digest('extractor1'))
        second = self.open(extractor_sha256=contracts.digest('extractor2'))
        self.assertNotEqual(first.sha256, second.sha256)
        self.assertEqual(6, len(self.calls))

    def test_changed_source_has_another_snapshot_and_fact_binding(self):
        first = self.open()
        path = self.root / 'source/A.cs'
        path.write_text(path.read_text(encoding='utf-8').replace('Write();', 'Write(); Write();'), encoding='utf-8')
        source = SourceAccess.create(self.root / 'source', self.root / 'snapshot2', project_id='synthetic',
                                     allowed_paths=['.'], excluded_paths=[])
        second = FactIndex.open(source, self.store, parser=self.parser)
        self.assertNotEqual(first.sha256, second.sha256)
        self.assertNotEqual(first.source.snapshot_id, second.source.snapshot_id)
        self.assertEqual(2, second.query(callee='Write')['matchedCount'])

    def test_damaged_cache_is_rejected_instead_of_becoming_empty_or_rebuilt(self):
        self.open()
        path = next((self.root / 'cache/source-facts').glob('*.json'))
        envelope = json.loads(path.read_text(encoding='utf-8'))
        envelope['payload']['facts'] = []
        path.write_text(json.dumps(envelope), encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'integrity mismatch'):
            self.open()
        self.assertEqual(3, len(self.calls))

    def test_call_queries_preserve_caller_and_do_not_resolve_same_named_targets(self):
        index = self.open()
        result = index.query(caller='Save', callee='Write')
        self.assertEqual(1, result['matchedCount'])
        call = result['facts'][0]
        self.assertEqual('unresolved', call['data']['resolution'])
        self.assertEqual('Save', index.by_id[call['data']['callerId']]['data']['name'])
        self.assertEqual(index.sha256, result['indexSha256'])
        self.assertEqual(2, index.query(kind='symbol', text='Write')['matchedCount'])

    def test_empty_query_distinguishes_unsupported_file_from_no_match(self):
        index = self.open()
        unsupported = index.query(path='data.sql')
        self.assertEqual([], unsupported['facts'])
        self.assertEqual('unsupported', unsupported['files'][0]['status'])
        no_match = index.query(path='A.cs', text='does-not-exist')
        self.assertEqual([], no_match['facts'])
        self.assertEqual('complete', no_match['files'][0]['status'])

    def test_explicit_limit_reports_truncation_without_changing_ids(self):
        index = self.open()
        full = index.query()
        result = index.query(limit=1)
        self.assertTrue(result['truncated'])
        self.assertEqual(1, result['returnedCount'])
        self.assertEqual(full['matchedCount'], result['matchedCount'])
        self.assertEqual(full['facts'][0], result['facts'][0])

    def test_complete_context_includes_all_facts_once(self):
        index = self.open()
        context = index.context()
        ids = []
        for table in ('symbols', 'calls', 'entries', 'imports'):
            value = context[table]
            ids.extend(row[value['columns'].index('id')] for row in value['rows'])
        self.assertEqual(set(index.by_id), set(ids))
        self.assertEqual(len(index.by_id), len(ids))
        self.assertGreater(len(context['calls']['rows']), 0)

    def test_cross_file_caller_and_duplicate_fact_ids_are_rejected(self):
        index = self.open()
        document = deepcopy(index.document)
        call = next(f for f in document['facts'] if f['kind'] == 'call')
        other = next(f for f in document['facts'] if f['kind'] == 'symbol' and f['path'] == 'B.cs')
        call['data']['callerId'] = other['id']
        with self.assertRaisesRegex(ValueError, 'caller'):
            FactIndex(document, self.source).validate()
        document = deepcopy(index.document)
        document['facts'].append(deepcopy(document['facts'][0]))
        with self.assertRaisesRegex(ValueError, 'Duplicate'):
            FactIndex(document, self.source).validate()

    def test_usage_is_bound_to_snapshot_and_actual_record_evidence(self):
        index = self.open()
        call = index.query(callee='Write')['facts'][0]
        record = {'key': 'business', 'evidence': call['data']['evidence']}
        answer = {'sourceFactsSha256': index.sha256, 'records': [record],
                  'factUsage': [{'recordKey': 'business', 'factIds': [call['id']], 'reason': 'Uses observed call'}]}
        index.validate_usage(answer, index.sha256)
        with self.assertRaisesRegex(ValueError, 'another index'):
            index.validate_usage(answer, contracts.digest('another snapshot'))
        answer['factUsage'][0]['factIds'] = []
        with self.assertRaisesRegex(ValueError, 'cannot be bypassed'):
            index.validate_usage(answer, index.sha256)
        sql = next(f for f in self.source.manifest['files'] if f['path'] == 'data.sql')
        record['evidence'] = [{'path': sql['path'], 'sha256': sql['sha256'], 'startLine': 1, 'endLine': 1}]
        index.validate_usage(answer, index.sha256)


if __name__ == '__main__':
    unittest.main()

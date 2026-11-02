"""Completed-child replay retains source receipts and operation-local integrity fences."""
from copy import deepcopy
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from contextbase_runtime import incremental, contracts as c
from contextbase_runtime.evidence import EvidenceAccess
import test_incremental_requests as fixtures

class CachedReplayBatchTests(fixtures.IncrementalRequestRecoveryTests):
    @staticmethod
    def no_provider(*args, **kwargs):
        raise AssertionError('Completed cached replay must not invoke provider')

    def batches(self, count=2):
        return [[self.read(), {'operation': 'inventory', 'offset': 0, 'limit': 10},
                 {'operation': 'search', 'text': 'class', 'path': None, 'offset': 0,
                  'limit': 10, 'caseSensitive': False},
                 {'operation': 'query', 'offset': 0, 'limit': 10, 'path': None,
                  'kind': None, 'text': None, 'caller': None, 'callee': None, 'route': None}]
                 * count]

    def test_fresh_and_cached_replay_have_exact_answers_receipts_and_artifact_bytes(self):
        expected = self.dialog(self.provider(self.batches()))
        retained = {str(p.relative_to(self.store.root)): p.read_bytes()
                    for p in self.store.root.rglob('*.json')}
        self.assertEqual(expected, self.dialog(self.no_provider, cached=expected[1]))
        self.assertEqual(retained, {str(p.relative_to(self.store.root)): p.read_bytes()
                                   for p in self.store.root.rglob('*.json')})

    def test_outer_binding_fences_scale_with_batches_not_request_count(self):
        counts = []
        for count in (1, 2):
            expected = self.dialog(self.provider(self.batches(count)))
            binding = EvidenceAccess._assert_binding
            batch = EvidenceAccess.verify_replies
            with patch.object(EvidenceAccess, '_assert_binding', autospec=True, side_effect=binding) as fence, \
                 patch.object(EvidenceAccess, 'verify_replies', autospec=True, side_effect=batch) as verify_batch, \
                 patch.object(self.source, '_verify', wraps=self.source._verify) as source_verify:
                self.assertEqual(expected, self.dialog(self.no_provider, cached=expected[1]))
                self.assertEqual(1, verify_batch.call_count)
                # Construction, pre/post batch, and final replay integrity fence.
                self.assertEqual(4, fence.call_count)
                counts.append(source_verify.call_count)
        # FactIndex.query still validates source once per query. This bounded
        # change deliberately does not remove those residual getter checks.
        self.assertEqual(1, counts[1] - counts[0])

    def test_tampered_historical_reply_rejected_even_with_resealed_store(self):
        _, pointer = self.dialog(self.provider([[self.read()]]))
        name = 'calls/' + pointer + '/round-0001.json'
        row = self.store.get(name)
        row['pairs'][0]['reply']['result']['sourceText'] = 'forged source'
        reply = row['pairs'][0]['reply']
        reply['resultSha256'] = c.digest(reply['result'])
        reply['replySha256'] = c.digest({k: v for k, v in reply.items() if k != 'replySha256'})
        self.store.path(name).write_text(json.dumps({'payload': row, 'sha256': c.digest(row)}))
        with self.assertRaisesRegex(ValueError, 'task-bound source replay'):
            self.dialog(self.no_provider, cached=pointer)

    def test_recoverable_bad_source_request_replays(self):
        expected = self.dialog(self.provider([[self.read('missing.cs'), self.read(start=99), self.read()]]))
        self.assertEqual(expected, self.dialog(self.no_provider, cached=expected[1]))

    def test_final_fence_rejects_source_changed_after_batch(self):
        expected = self.dialog(self.provider([[self.read()]]))
        original_batch = EvidenceAccess.verify_replies
        path = self.source.root / 'sources/A.cs'
        old = path.read_bytes()
        def mutate(access, pairs):
            original_batch(access, pairs)
            path.write_bytes(old + b'\n')
        try:
            with patch.object(EvidenceAccess, 'verify_replies', mutate), self.assertRaises(ValueError):
                self.dialog(self.no_provider, cached=expected[1])
        finally:
            path.write_bytes(old)

    def test_semantic_metadata_mutation_during_batch_rejected_using_local_fixture(self):
        import hashlib
        from contextbase_runtime.semantic_calls import SemanticCallIndex, VERSION, _implementation
        from contextbase_runtime.dotnet_host import semantic_host_fingerprint
        metadata = self.root / 'fixture-metadata.dll'
        metadata.write_bytes(b'local metadata fixture only')
        document = {'schema': VERSION, 'binding': {'schema': VERSION,
            'snapshotId': self.source.snapshot_id, 'sourceFactsSha256': self.index.sha256,
            'implementation': _implementation(), 'host': semantic_host_fingerprint(),
            'context': {'references': [{'path': str(metadata),
                'sha256': hashlib.sha256(metadata.read_bytes()).hexdigest()}]}},
            'projects': [], 'results': [], 'symbols': {}, 'registrations': [],
            'unjoinedCompilerCalls': []}
        self.index.semantic_index = SemanticCallIndex(document, self.index)
        self.task.update(semanticPolicy='contextbase-semantic-evidence/1',
                         semanticIndexSha256=self.index.semantic_index.sha256)
        self.context['semanticAnalysis'] = {'fixture': 'local metadata binding'}
        expected = self.dialog(self.provider([[self.read()]]))
        response = EvidenceAccess._response
        def mutate(access, request, texts=None):
            result = response(access, request, texts=texts)
            if texts is not None:
                metadata.write_bytes(b'changed local metadata fixture')
            return result
        with patch.object(EvidenceAccess, '_response', mutate), \
             self.assertRaisesRegex(ValueError, 'metadata reference changed'):
            self.dialog(self.no_provider, cached=expected[1])

    def test_source_or_metadata_mutation_during_batch_is_rejected(self):
        # inventory does not read A.cs; changing that unrelated source must still
        # invalidate the full snapshot in the post-batch fence.
        for change in ('unrelated-source', 'manifest'):
            with self.subTest(change=change):
                expected = self.dialog(self.provider([[{'operation': 'inventory', 'offset': 0, 'limit': 10}]]))
                path = self.source.root / ('sources/A.cs' if change == 'unrelated-source' else 'manifest.json')
                old = path.read_bytes()
                response = EvidenceAccess._response
                def mutate(access, request, texts=None):
                    result = response(access, request, texts=texts)
                    if texts is not None:
                        path.write_bytes(old + b'\n')
                    return result
                try:
                    with patch.object(EvidenceAccess, '_response', mutate), self.assertRaises(ValueError):
                        self.dialog(self.no_provider, cached=expected[1])
                finally:
                    path.write_bytes(old)


if __name__ == '__main__':
    unittest.main()

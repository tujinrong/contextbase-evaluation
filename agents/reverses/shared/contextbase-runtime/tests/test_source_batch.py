"""Operation-local evidence batching retains complete snapshot integrity checks."""
from copy import deepcopy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from contextbase_runtime.sources import SourceAccess


class SourceBatchTests(unittest.TestCase):
    def setUp(self):
        home = Path(__file__).resolve().parents[1] / '.tmp'
        home.mkdir(exist_ok=True)
        self.temporary = tempfile.TemporaryDirectory(prefix='source-batch-', dir=home)
        self.root = Path(self.temporary.name)
        original = self.root / 'original'
        original.mkdir()
        (original / 'alpha.cs').write_bytes(b'first\nsecond\nthird\n')
        (original / 'beta.cs').write_bytes(b'other\nsource\n')
        self.source = SourceAccess.create(original, self.root / 'snapshot', project_id='synthetic-batch',
                                          allowed_paths=['.'], excluded_paths=[])
        self.alpha = self.source.root / 'sources/alpha.cs'
        self.beta = self.source.root / 'sources/beta.cs'
        self.ref = self.source.evidence('alpha.cs', 1, 2)

    def tearDown(self):
        self.temporary.cleanup()

    def test_repeated_refs_use_two_full_checks_and_one_additional_read_per_referenced_file(self):
        reads = {}
        original = Path.read_bytes
        def counted(path):
            reads[path] = reads.get(path, 0) + 1
            return original(path)
        refs = [deepcopy(self.ref) for _ in range(30)]
        with patch.object(self.source, '_verify', wraps=self.source._verify) as verify, \
             patch.object(Path, 'read_bytes', counted):
            self.assertIsNone(self.source.verify_evidence_many(refs))
        self.assertEqual(2, verify.call_count)
        self.assertEqual(3, reads[self.alpha], 'Two whole snapshots plus one batch-local raw file read')
        self.assertEqual(2, reads[self.beta], 'Unreferenced files still participate in both full checks')

    def test_mixed_files_and_distinct_ranges_all_validate(self):
        refs = [self.ref, self.source.evidence('beta.cs', 1, 1),
                self.source.evidence('alpha.cs', 3, 3), self.ref]
        self.source.verify_evidence_many(refs)

    def test_duplicate_good_refs_cannot_hide_a_bad_ref_in_the_middle(self):
        changes = [dict(sha256='0' * 64), dict(endLine=4), dict(startLine=True),
                   dict(endLine=False), dict(path='missing.cs'), dict(path='../alpha.cs')]
        for change in changes:
            with self.subTest(change=change), self.assertRaises(ValueError):
                self.source.verify_evidence_many([self.ref, {**self.ref, **change}, self.ref])

    def test_evidence_requires_exact_fields_and_integer_nonempty_ranges(self):
        invalid = [None, [], {**self.ref, 'extra': 'not allowed'},
                   {key: value for key, value in self.ref.items() if key != 'sha256'},
                   {**self.ref, 'startLine': 0}, {**self.ref, 'startLine': 2, 'endLine': 1},
                   {**self.ref, 'startLine': 1.0}, {**self.ref, 'endLine': None}]
        for ref in invalid:
            with self.subTest(ref=ref), self.assertRaises(ValueError):
                self.source.verify_evidence_many([ref])

    def test_unreferenced_source_mutation_during_batch_is_rejected(self):
        def changing():
            yield self.ref
            self.beta.write_bytes(b'modified unrelated source\n')
            yield self.ref
        with self.assertRaises(ValueError):
            self.source.verify_evidence_many(changing())

    def test_referenced_source_mutation_during_batch_cannot_hide_behind_the_local_cache(self):
        def changing():
            yield self.ref
            self.alpha.write_bytes(b'modified referenced source\n')
            yield self.ref
        with self.assertRaises(ValueError):
            self.source.verify_evidence_many(changing())

    def test_manifest_or_extra_snapshot_material_changes_are_detected_at_end(self):
        for change in ('manifest', 'extra-file', 'extra-directory'):
            # A distinct sealed snapshot keeps each mutation independent.
            original = self.root / ('original-' + change)
            original.mkdir()
            (original / 'alpha.cs').write_bytes(b'first\nsecond\n')
            source = SourceAccess.create(original, self.root / ('snapshot-' + change),
                                         project_id='synthetic-batch', allowed_paths=['.'], excluded_paths=[])
            ref = source.evidence('alpha.cs', 1, 1)
            def changing():
                yield ref
                if change == 'manifest':
                    manifest = source.root / 'manifest.json'
                    manifest.write_bytes(manifest.read_bytes() + b'\n')
                elif change == 'extra-file':
                    (source.root / 'unlisted.txt').write_bytes(b'extra')
                else:
                    (source.root / 'unlisted-directory').mkdir()
                yield ref
            with self.subTest(change=change), self.assertRaises(ValueError):
                source.verify_evidence_many(changing())

    def test_second_full_verification_failure_never_returns_success(self):
        original = self.source._verify
        calls = []
        def fail_at_end():
            calls.append(True)
            if len(calls) == 2:
                raise ValueError('Synthetic end-of-operation seal failure')
            original()
        with patch.object(self.source, '_verify', side_effect=fail_at_end), self.assertRaises(ValueError):
            self.source.verify_evidence_many([self.ref, self.ref])
        self.assertEqual(2, len(calls))

    def test_empty_batch_still_checks_the_whole_snapshot_twice(self):
        with patch.object(self.source, '_verify', wraps=self.source._verify) as verify:
            self.source.verify_evidence_many([])
        self.assertEqual(2, verify.call_count)

    def test_successful_batch_does_not_cache_integrity_across_later_calls(self):
        self.source.verify_evidence_many([self.ref])
        self.beta.write_bytes(b'changed between independent operations\n')
        with self.assertRaises(ValueError):
            self.source.verify_evidence_many([self.ref])
        with self.assertRaises(ValueError):
            self.source.verify_evidence(self.ref)


if __name__ == '__main__':
    unittest.main()

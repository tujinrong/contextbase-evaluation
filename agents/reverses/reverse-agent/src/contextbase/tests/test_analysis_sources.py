"""Source-only acquisition, immutable evidence and scope boundary regression tests."""
from pathlib import Path
import json
import tempfile
import unittest
from unittest.mock import patch

from contextbase.analysis.sources import SourceAccess


class SourceAccessTests(unittest.TestCase):
    def setUp(self):
        home = Path(__file__).resolve().parents[3] / '.tmp'
        home.mkdir(exist_ok=True)
        self.temporary = tempfile.TemporaryDirectory(prefix='analysis-source-', dir=home)
        self.root = Path(self.temporary.name)
        self.source = self.root / 'source'
        self.source.mkdir()
        self.destination = self.root / 'snapshot'

    def tearDown(self):
        self.temporary.cleanup()

    def material(self, path='app/Logic.cs', data=b'first\r\nsecond\r\n'):
        target = self.source / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        return target

    def create(self, allowed=None, excluded=None):
        return SourceAccess.create(self.source, self.destination, project_id='synthetic',
                                   allowed_paths=['.'] if allowed is None else allowed,
                                   excluded_paths=[] if excluded is None else excluded)

    def test_lossless_original_bytes_encoding_and_lines(self):
        data = ('const string 長文="' + '長' * 9000 + '";\r\nnext\n').encode('utf-8-sig')
        original = self.material(data=data)
        access = self.create()
        self.assertEqual(data, original.read_bytes())
        self.assertEqual(data, (self.destination / 'sources/app/Logic.cs').read_bytes())
        self.assertEqual('next\n', access.read('app/Logic.cs', 2, 2))
        self.assertEqual(2, access.manifest['files'][0]['lines'])
        self.assertEqual('utf-8-sig', access.manifest['files'][0]['encoding'])
        self.assertTrue(access.root.is_absolute())
        self.assertEqual(access.snapshot_id, SourceAccess.open(self.destination).snapshot_id)

    def test_scope_and_default_exclusions_applied_before_content_reads(self):
        self.material()
        blocked = [self.material(path, b'\x00\xff') for path in (
            'spec/answer.cs', 'spec-eval/answer.json', 'spec-analysis/answer.cs',
            'QA/answer.cs', 'tests/answer.cs', 'output/answer.cs', 'report/answer.cs',
            'app/AGENTS.md', 'app/.env.local', 'app/hidden.cs',
            'other/非選択.cs', 'other/blob.bin')]
        read = Path.read_bytes
        def checked_read(path):
            self.assertNotIn(path, blocked)
            return read(path)
        with patch.object(Path, 'read_bytes', checked_read):
            access = self.create(['app'], ['app/hidden.cs'])
        self.assertEqual(['app/Logic.cs'], access.paths)
        reasons = {item['reason'] for item in access.manifest['omitted']}
        self.assertTrue({'excluded-directory', 'excluded-path',
                         'outside-allowed-paths', 'instructions-or-local-secret'} <= reasons)

    def test_unicode_literal_separator_does_not_shift_tree_sitter_evidence_rows(self):
        text = 'class Logic {\r\n string Value = "a\u2028b";\r\n void Run() {}\r\n}\r\n'
        self.material(data=text.encode('utf-8'))
        access = self.create()
        self.assertEqual(text, access.read('app/Logic.cs'))
        self.assertEqual(4, access.manifest['files'][0]['lines'])
        self.assertEqual(' void Run() {}\r\n', access.read('app/Logic.cs', 3, 3))
        from contextbase.analysis.adapters import index_source
        result = index_source('app/Logic.cs', text, source_sha256=access.evidence('app/Logic.cs')['sha256'])
        method = next(item for item in result['symbols'] if item['name'] == 'Run')
        self.assertEqual(3, method['startLine'])
        for evidence in method['evidence']:
            access.verify_evidence(evidence)

    def test_nonselected_file_with_shared_parent_is_not_read(self):
        self.material()
        blocked = self.material('app/Other.cs', b'\x00\x00')
        read = Path.read_bytes
        def checked_read(path):
            self.assertNotEqual(path, blocked)
            return read(path)
        with patch.object(Path, 'read_bytes', checked_read):
            access = self.create(['app/Logic.cs'])
        self.assertEqual(['app/Logic.cs'], access.paths)

    def test_unsupported_and_empty_files_are_explicit(self):
        self.material()
        self.material('app/binary.cs', b'\x00\x00')
        self.material('app/empty.cs', b'')
        self.material('app/image.png', b'not read')
        access = self.create()
        self.assertEqual(['app/Logic.cs', 'app/empty.cs'], access.paths)
        self.assertEqual(2, len(access.manifest['omitted']))
        self.assertEqual('', access.read('app/empty.cs'))
        with self.assertRaises(ValueError):
            access.evidence('app/empty.cs')

    def test_reference_requires_actual_hash_and_exact_valid_range(self):
        self.material()
        access = self.create()
        ref = access.evidence('app/Logic.cs', 1, 2)
        access.verify_evidence(ref)
        for changes in ({'sha256': '0' * 64}, {'startLine': True}, {'endLine': 3},
                        {'startLine': 0}, {'startLine': 2, 'endLine': 1},
                        {'path': 'app/logic.cs'}, {'path': '../foreign.cs'},
                        {'path': 'app\\Logic.cs'}, {'extra': 'untrusted'}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                access.verify_evidence({**ref, **changes})
        with self.assertRaises(ValueError):
            access.read('app/Logic.cs', end_line=False)

    def test_every_read_refuses_tampered_raw_source(self):
        self.material()
        access = self.create()
        ref = access.evidence('app/Logic.cs')
        (self.destination / 'sources/app/Logic.cs').write_bytes(b'forged\n')
        for operation in (access.verify, lambda: access.read('app/Logic.cs'),
                          lambda: access.evidence('app/Logic.cs'),
                          lambda: access.verify_evidence(ref), lambda: access.paths):
            with self.subTest(operation=operation), self.assertRaises(ValueError):
                operation()

    def test_manifest_is_defensive_and_seal_binds_scope(self):
        self.material()
        access = self.create(['app'])
        manifest = access.manifest
        manifest['allowedPaths'].append('other')
        self.assertEqual(['app'], access.manifest['allowedPaths'])
        (self.destination / 'manifest.json').write_text(json.dumps(manifest), encoding='utf-8')
        with self.assertRaises(ValueError):
            access.verify()
        with self.assertRaises(ValueError):
            SourceAccess.open(self.destination)

    def test_unlisted_material_refused(self):
        self.material()
        access = self.create()
        (self.destination / 'extra.cs').write_bytes(b'extra')
        with self.assertRaises(ValueError):
            access.verify()

    def test_unlisted_empty_directory_refused(self):
        self.material()
        access = self.create()
        (self.destination / 'unexpected').mkdir()
        with self.assertRaises(ValueError):
            access.verify()

    def test_input_programs_are_never_executed_or_imported(self):
        self.material('danger.py', b'raise RuntimeError("must not execute input")\n')
        access = self.create()
        self.assertIn('raise RuntimeError', access.read('danger.py'))

    def test_individual_file_case_alias_is_rejected(self):
        self.material()
        access = self.create()
        with self.assertRaises(ValueError):
            access.read('APP/Logic.cs')

    def test_original_change_during_capture_refuses_seal(self):
        original = self.material()
        read = Path.read_bytes
        source_reads = 0
        def changing_read(path):
            nonlocal source_reads
            if path == original:
                source_reads += 1
                if source_reads == 3:
                    return b'changed during copying\n'
            return read(path)
        with patch.object(Path, 'read_bytes', changing_read), self.assertRaises(ValueError):
            self.create()
        self.assertFalse((self.destination / 'seal.json').exists())

    def test_original_changes_do_not_rewrite_the_frozen_snapshot(self):
        original = self.material()
        access = self.create()
        original.write_bytes(b'new source version\n')
        access.verify()
        self.assertEqual('first\r\nsecond\r\n', access.read('app/Logic.cs'))

    def test_invalid_scopes_are_rejected(self):
        self.material()
        for path in ('../source', '/source', 'C:/source', 'app\\Logic.cs',
                     './app', 'app//Logic.cs', 'app/', 'app/Logic.cs.', ''):
            with self.subTest(path=path), self.assertRaises(ValueError):
                self.create([path])
        with self.assertRaises(ValueError):
            self.create(['app', 'APP'])

    def test_empty_selection_and_overlapping_destinations_refused(self):
        self.material()
        for allowed in ([], ['absent'], ['spec']):
            with self.subTest(allowed=allowed), self.assertRaises(ValueError):
                self.create(allowed)
        self.assertFalse(self.destination.exists())
        for destination in (self.source, self.source / 'snapshot', self.root):
            with self.subTest(destination=destination), self.assertRaises(ValueError):
                SourceAccess.create(self.source, destination, project_id='synthetic',
                                    allowed_paths=['.'], excluded_paths=[])

    def test_forbidden_source_root_is_rejected_without_reading(self):
        self.material('spec-eval/answer.cs')
        with patch.object(Path, 'read_bytes', side_effect=AssertionError('must not read')):
            with self.assertRaises(ValueError):
                SourceAccess.create(self.source / 'spec-eval', self.destination,
                                    project_id='synthetic', allowed_paths=['.'], excluded_paths=[])

    def test_case_collision_refused_when_filesystem_supports_it(self):
        self.material('app/Logic.cs')
        self.material('app/logic.cs')
        if len(list((self.source / 'app').iterdir())) < 2:
            self.skipTest('Case-insensitive filesystem prevents fixture collision')
        with self.assertRaises(ValueError):
            self.create()

    def test_symlink_source_refused_when_available(self):
        outside = self.root / 'outside.cs'
        outside.write_bytes(b'untrusted\n')
        try:
            (self.source / 'linked.cs').symlink_to(outside)
        except (OSError, NotImplementedError):
            self.skipTest('Symlink creation is unavailable')
        with self.assertRaises(ValueError):
            self.create()


if __name__ == '__main__':
    unittest.main()

"""Independent fixtures for evidence isolation and unchanged source text."""
from pathlib import Path
import json
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from contextbase.ai import capsule


class CapsuleTests(unittest.TestCase):
    def setUp(self):
        home = Path(__file__).resolve().parents[3] / '.tmp'
        home.mkdir(exist_ok=True)
        self.temporary = tempfile.TemporaryDirectory(prefix='capsule-unit-', dir=home)
        self.root = Path(self.temporary.name)
        self.source = self.root / 'source'
        self.source.mkdir()

    def tearDown(self):
        self.temporary.cleanup()

    def material(self, relative, data=b'class Plain { string Value="  001 | & "; }\r\n'):
        file = self.source / relative
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_bytes(data)
        return file

    def test_original_bytes_and_long_literal_survive(self):
        data = ('const string value="  001  ' + '長' * 9000 + '  ";\r\n').encode('utf-8')
        self.material('logic.cs', data)
        target = self.root / 'snapshot'
        value = capsule.create(self.source, target, project_id='arbitrary')
        self.assertEqual(data, (target / 'sources/logic.cs').read_bytes())
        self.assertIn('  001  ' + '長' * 9000 + '  ', (target / 'indexed/logic.cs.txt').read_text(encoding='utf-8'))
        self.assertEqual(value['files'][0]['sha256'], capsule.sha256(data))

    def test_reference_labels_and_test_expectations_excluded(self):
        self.material('logic.cs')
        for name in ('spec/answer.cs', 'spec-eval/expected.json', 'Tests/expectation.cs', 'metadata/expectation.json', 'bin/fake.cs', 'obj/fake.json'):
            self.material(name)
        target = self.root / 'snapshot'
        value = capsule.create(self.source, target, project_id='unknown-business')
        self.assertEqual(['logic.cs'], [file['path'] for file in value['files']])
        self.assertFalse(value['referenceSpecificationIncluded'])
        self.assertEqual('source-only', value['mode'])

    def test_mutated_raw_source_rejected(self):
        self.material('logic.cs')
        target = self.root / 'snapshot'
        capsule.create(self.source, target, project_id='project')
        (target / 'sources/logic.cs').write_text('changed')
        with self.assertRaises(ValueError):
            capsule.verify(target)

    def test_mutated_indexed_evidence_rejected(self):
        self.material('logic.cs')
        target = self.root / 'snapshot'
        capsule.create(self.source, target, project_id='project')
        (target / 'indexed/logic.cs.txt').write_text('000001 | fabricated fact\n', encoding='utf-8')
        with self.assertRaises(ValueError):
            capsule.verify(target)

    def test_manifest_escape_rejected(self):
        self.material('logic.cs')
        target = self.root / 'snapshot'
        value = capsule.create(self.source, target, project_id='project')
        value['files'][0]['path'] = '../../foreign.cs'
        (target / 'manifest.json').write_text(json.dumps(value), encoding='utf-8')
        with self.assertRaises(ValueError):
            capsule.verify(target)

    def test_snapshot_cannot_be_inside_source_or_overwrite(self):
        self.material('logic.cs')
        with self.assertRaises(ValueError):
            capsule.create(self.source, self.source / 'snapshot', project_id='project')
        target = self.root / 'snapshot'
        capsule.create(self.source, target, project_id='project')
        with self.assertRaises(ValueError):
            capsule.create(self.source, target, project_id='project')

    def test_explicit_training_designs_kept_separate(self):
        self.material('logic.cs')
        reference = self.root / 'design'
        reference.mkdir()
        text = '# 未知業務の参考設計\n\nコードの実行証拠ではない。\n'
        (reference / 'feature.md').write_text(text, encoding='utf-8')
        target = self.root / 'snapshot'
        value = capsule.create(self.source, target, project_id='project', authorized_reference_directories=(reference,))
        self.assertTrue(value['trainingReferenceAuthorizedByUser'])
        self.assertEqual('training-assisted', value['mode'])
        self.assertEqual('reference-designs/design/feature.md', value['referenceFiles'][0]['path'])
        self.assertEqual(1, len(value['files']))
        capsule.verify(target)

    def test_reference_authorization_and_hash_are_verified(self):
        self.material('logic.cs')
        reference = self.root / 'design'
        reference.mkdir()
        (reference / 'feature.md').write_text('# Test', encoding='utf-8')
        target = self.root / 'snapshot'
        value = capsule.create(self.source, target, project_id='project', authorized_reference_directories=(reference,))
        value['trainingReferenceAuthorizedByUser'] = False
        (target / 'manifest.json').write_text(json.dumps(value), encoding='utf-8')
        with self.assertRaises(ValueError):
            capsule.verify(target)

    def test_binary_source_is_reported_as_omitted(self):
        self.material('logic.cs')
        self.material('opaque.txt', b'\x00\x01\x02')
        value = capsule.create(self.source, self.root / 'snapshot', project_id='project')
        self.assertEqual(1, len(value['files']))
        self.assertTrue(any(item['path'] == 'opaque.txt' for item in value['omitted']))

    def test_source_root_under_evaluator_directory_is_forbidden_before_output(self):
        source=self.root/'Spec-Eval'/'nested';source.mkdir(parents=True)
        (source/'expected.json').write_text('{"expectation":true}')
        target=self.root/'snapshot'
        with self.assertRaisesRegex(ValueError,'Evaluator-only'):
            capsule.create(source,target,project_id='synthetic')
        self.assertFalse(target.exists())

    def test_authorized_reference_root_cannot_point_to_evaluator_material(self):
        self.material('logic.cs');reference=self.root/'spec-eval'/'design';reference.mkdir(parents=True)
        (reference/'expected.md').write_text('# Expected')
        target=self.root/'snapshot'
        with self.assertRaisesRegex(ValueError,'Evaluator-only'):
            capsule.create(self.source,target,project_id='synthetic',authorized_reference_directories=(reference,))
        self.assertFalse(target.exists())

    def test_reference_tree_does_not_hide_nested_evaluator_directory(self):
        self.material('logic.cs');reference=self.root/'design';reference.mkdir()
        protected=reference/'spec-eval';protected.mkdir();(protected/'expected.md').write_text('# Expected')
        with self.assertRaisesRegex(ValueError,'Evaluator-only'):
            capsule.create(self.source,self.root/'snapshot',project_id='synthetic',authorized_reference_directories=(reference,))

    def link(self,path,target,directory=False):
        try:path.symlink_to(target,target_is_directory=directory)
        except OSError:self.skipTest('Host does not permit symlinks')

    def test_authorized_reference_symlink_root_is_rejected_before_resolve(self):
        self.material('logic.cs');reference=self.root/'design';reference.mkdir()
        (reference/'intent.md').write_text('# Intent');alias=self.root/'alias'
        self.link(alias,reference,True)
        with self.assertRaisesRegex(ValueError,'Linked'):
            capsule.create(self.source,self.root/'snapshot',project_id='synthetic',authorized_reference_directories=(alias,))

    def test_nested_reference_directory_symlink_is_not_silently_ignored(self):
        self.material('logic.cs');reference=self.root/'design';reference.mkdir()
        outside=self.root/'outside';outside.mkdir();(outside/'secret.md').write_text('# Not permitted')
        self.link(reference/'nested',outside,True)
        with self.assertRaisesRegex(ValueError,'Linked'):
            capsule.create(self.source,self.root/'snapshot',project_id='synthetic',authorized_reference_directories=(reference,))

    def test_nested_reference_file_symlink_is_rejected(self):
        self.material('logic.cs');reference=self.root/'design';reference.mkdir()
        outside=self.root/'outside.md';outside.write_text('# Not permitted')
        self.link(reference/'intent.md',outside)
        with self.assertRaisesRegex(ValueError,'Linked'):
            capsule.create(self.source,self.root/'snapshot',project_id='synthetic',authorized_reference_directories=(reference,))

    def test_plain_directory_with_reparse_attribute_is_rejected(self):
        self.material('logic.cs');reference=self.root/'design';reference.mkdir();nested=reference/'nested';nested.mkdir()
        original_lstat=Path.lstat
        def reparse(path,*args,**kwargs):
            actual=original_lstat(path,*args,**kwargs)
            if path==nested:
                return SimpleNamespace(st_mode=actual.st_mode,st_file_attributes=0x400)
            return actual
        with patch.object(Path,'lstat',reparse):
            with self.assertRaisesRegex(ValueError,'Reparse'):
                capsule.create(self.source,self.root/'snapshot',project_id='synthetic',authorized_reference_directories=(reference,))

    def test_source_children_keep_existing_exclusion_scope(self):
        self.material('logic.cs');self.material('spec-eval/expected.json',b'{"expected":true}')
        manifest=capsule.create(self.source,self.root/'snapshot',project_id='synthetic')
        self.assertEqual(['logic.cs'],[entry['path'] for entry in manifest['files']])
        self.assertTrue(any(entry['path']=='spec-eval' for entry in manifest['omitted']))


if __name__ == '__main__':
    unittest.main()

"""Integrity regressions with clearly synthetic documents and review data."""
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import grader
import combine_batches as combine

def criterion(row_id, category='属性', penalty=1):
    return {'evaluationId': row_id, 'maximumPenalty': penalty, 'category': category}

def grade(row_id):
    return {'evaluationId': row_id, 'judgement': '一致', 'actualDeduction': 0,
        'defectId': None, 'reason': 'Synthetic fixture only', 'generatedEvidence': [],
        'critical': False, 'mandatoryMissing': False,
        'sourceFidelity': {'judgement': '一致', 'reason': 'Synthetic fixture only', 'sourceEvidence': []}}

def safe_checks(document_id):
    return [{'documentId': document_id, 'topic': topic, 'judgement': 'CLEAR',
        'reason': 'Synthetic fixture only', 'generatedEvidence': [], 'sourceEvidence': []} for topic in combine.SAFETY_TOPICS]

def mini_rubric():
    return {'documents': [{'documentId': 'SYNTHETIC-A', 'rows': [criterion('ROW-A')]},
        {'documentId': 'SYNTHETIC-B', 'rows': [criterion('ROW-B', '画面設計', 3)]}]}

class SelectionIntegrity(unittest.TestCase):
    def test_reference_modes_cannot_mix_in_one_document_union(self):
        for mode, other in (('source-only', 'training-assisted'), ('training-assisted', 'source-only')):
            selection = {'schema': combine.SELECTION_SCHEMA, 'projectId': 'test-project1', 'profile': 'CSharp_ASPNET',
                'rubricSha256': 'fixture-rubric', 'sourceSnapshotSha256': 'fixture-source', 'referenceMode': mode,
                'documents': [{'documentId': 'SYNTHETIC-A'}, {'documentId': 'SYNTHETIC-B'}]}
            def loader(entry, selection, document):
                selected_mode = mode if document['documentId'] == 'SYNTHETIC-A' else other
                return [grade(r['evaluationId']) for r in document['rows']], safe_checks(document['documentId']), {
                    'documentId': document['documentId'], 'referenceMode': selected_mode, 'sourceSnapshotSha256': 'fixture-source'}
            with self.subTest(mode=mode), self.assertRaisesRegex(ValueError, 'mix evaluation reference modes'):
                combine.combine_selection(selection, mini_rubric(), {'effectiveItemsSha256': 'fixture-rubric'}, loader=loader)

    def test_document_audits_cannot_mix_snapshot_hashes(self):
        selection = {'schema': combine.SELECTION_SCHEMA, 'projectId': 'test-project1', 'profile': 'CSharp_ASPNET',
            'rubricSha256': 'fixture-rubric', 'sourceSnapshotSha256': 'fixture-source',
            'documents': [{'documentId': 'SYNTHETIC-A'}]}
        with self.assertRaisesRegex(ValueError, 'mix source snapshots'):
            combine.combine_selection(selection, mini_rubric(), {'effectiveItemsSha256': 'fixture-rubric'},
                loader=lambda *args: ([grade('ROW-A')], safe_checks('SYNTHETIC-A'), {'sourceSnapshotSha256': 'other-source'}))

    def test_separate_results_explicitly_record_each_reference_mode(self):
        outputs = []
        for mode in ('source-only', 'training-assisted'):
            selection = {'schema': combine.SELECTION_SCHEMA, 'projectId': 'test-project1', 'profile': 'CSharp_ASPNET',
                'rubricSha256': 'fixture-rubric', 'sourceSnapshotSha256': mode + '-fixture-source',
                'referenceMode': mode, 'documents': [{'documentId': 'SYNTHETIC-A'}]}
            outputs.append(combine.combine_selection(selection, mini_rubric(), {'effectiveItemsSha256': 'fixture-rubric'},
                loader=lambda *args: ([grade('ROW-A')], safe_checks('SYNTHETIC-A'), {'referenceMode': mode})))
        self.assertEqual([o['referenceMode'] for o in outputs], ['source-only', 'training-assisted'])
        self.assertNotEqual(outputs[0]['sourceSnapshotSha256'], outputs[1]['sourceSnapshotSha256'])
        self.assertTrue(all(o['total']['maximumPoints'] == 4 and o['total']['score'] is None for o in outputs))

    def test_duplicate_document_selection_is_rejected_before_loading(self):
        selection = {'schema': combine.SELECTION_SCHEMA, 'projectId': 'test-project1', 'profile': 'CSharp_ASPNET',
            'rubricSha256': 'fixture-rubric', 'documents': [{'documentId': 'SYNTHETIC-A'}, {'documentId': 'SYNTHETIC-A'}]}
        with self.assertRaisesRegex(ValueError, 'selected more than once'):
            combine.combine_selection(selection, mini_rubric(), {'effectiveItemsSha256': 'fixture-rubric'},
                loader=lambda *args: self.fail('Duplicate selection must never load a batch'))

    def test_duplicate_evaluation_id_cannot_inflate_score(self):
        with self.assertRaisesRegex(ValueError, 'appears more than once'):
            combine.compute_summary(mini_rubric(), [grade('ROW-A'), grade('ROW-A')], [], [], ['SYNTHETIC-A'])

    def test_partial_document_union_keeps_full_denominator_and_null_score(self):
        summary = combine.compute_summary(mini_rubric(), [grade('ROW-A')], safe_checks('SYNTHETIC-A'), [], ['SYNTHETIC-A'])
        self.assertEqual(summary['total']['maximumPoints'], 4)
        self.assertEqual(summary['gradedRows'], 1)
        self.assertIsNone(summary['total']['score'])
        self.assertIsNone(summary['total']['percentage'])
        self.assertFalse(summary['fullSetComplete'])
        self.assertFalse(summary['finalQualified'])

    def test_held_row_prevents_formal_combined_score_even_with_full_coverage(self):
        a = grade('ROW-A')
        a.update(judgement='保留', actualDeduction=None)
        summary = combine.compute_summary(mini_rubric(), [a, grade('ROW-B')],
            safe_checks('SYNTHETIC-A') + safe_checks('SYNTHETIC-B'), [], ['SYNTHETIC-A', 'SYNTHETIC-B'])
        self.assertTrue(summary['fullSetCoverageComplete'])
        self.assertFalse(summary['allRowsAssessed'])
        self.assertIsNone(summary['total']['score'])

    def test_source_contradiction_is_separate_from_design_score(self):
        a = grade('ROW-A')
        a['sourceFidelity']['judgement'] = '矛盾'
        summary = combine.compute_summary(mini_rubric(), [a, grade('ROW-B')],
            safe_checks('SYNTHETIC-A') + safe_checks('SYNTHETIC-B'), [], ['SYNTHETIC-A', 'SYNTHETIC-B'])
        self.assertEqual(summary['total']['percentage'], 100)
        self.assertEqual(summary['status'], 'TEXT_PASSED_SOURCE_GATE_FAILED')
        self.assertFalse(summary['sourceObservationGatePassed'])
        self.assertFalse(summary['finalQualified'])

    def test_static_qualified_status_requires_matching_visual_gate(self):
        audits = [{'documentId': 'SYNTHETIC-B', 'visualReview': {'approvedAndBound': True}}]
        summary = combine.compute_summary(mini_rubric(), [grade('ROW-A'), grade('ROW-B')],
            safe_checks('SYNTHETIC-A') + safe_checks('SYNTHETIC-B'), audits, ['SYNTHETIC-A', 'SYNTHETIC-B'])
        self.assertTrue(summary['finalQualified'])
        self.assertEqual(summary['status'], 'QUALIFIED_STATIC_SCOPE')
        self.assertFalse(summary['originalApplicationExecuted'])

    def test_duplicate_safety_topic_is_rejected(self):
        checks = safe_checks('SYNTHETIC-A')
        with self.assertRaisesRegex(ValueError, 'repeats a document/topic'):
            combine.compute_summary(mini_rubric(), [grade('ROW-A')], checks + [checks[0]], [], ['SYNTHETIC-A'])

class ArtifactBinding(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(dir=grader.HERE)
        self.root = Path(self.temporary.name).resolve()
        self.root.relative_to(grader.HERE.resolve())
        self.batch = self.root / 'batch'
        self.capsule = self.batch / 'capsule'
        self.canonical = self.root / 'canonical/基本設計書/01_example.md'
        self.canonical.parent.mkdir(parents=True)
        self.canonical.write_text('Synthetic fixture limit 12\n', encoding='utf-8')
        self.draft = self.capsule / 'generated/基本設計書/01_example.md'
        self.draft.parent.mkdir(parents=True)
        self.draft.write_bytes(self.canonical.read_bytes())
        self.document = {'documentId': 'SYNTHETIC-A', 'sourcePath': 'spec/基本設計書/01_example.md', 'rows': [criterion('ROW-A')]}
        self.selection = {'rubricSha256': 'fixture-rubric', 'sourceSnapshotSha256': 'fixture-source'}
        self.entry = {'documentId': 'SYNTHETIC-A', 'batchPath': str(self.batch),
            'canonicalPath': str(self.canonical), 'canonicalSha256': grader.digest(self.canonical),
            'normalizationPath': 'normalization.json'}
        self.seal = {'documentIds': ['SYNTHETIC-A'], 'graderSha256': 'fixture-code', 'jobs': []}
        self.manifest = {'rubricSha256': 'fixture-rubric', 'sourceSnapshotSha256': 'fixture-source', 'sourceMode': 'source-only',
            'files': [{'path': 'generated/基本設計書/01_example.md', 'sha256': grader.digest(self.draft), 'role': 'generated'}]}
        self.write_manifest()

    def write_manifest(self):
        grader.save(self.capsule / 'manifest.json', self.manifest, exclusive=False)

    def tearDown(self):
        self.temporary.cleanup()

    def test_old_draft_cannot_be_combined_with_new_canonical(self):
        self.canonical.write_text('Synthetic fixture limit 14\n', encoding='utf-8')
        self.entry['canonicalSha256'] = grader.digest(self.canonical)
        with patch.object(grader, 'check_capsule', return_value=(self.seal, self.capsule)):
            with self.assertRaisesRegex(ValueError, 'different or older draft'):
                combine.load_document(self.entry, self.selection, self.document)

    def test_another_source_snapshot_is_rejected_before_grades_are_loaded(self):
        self.manifest['sourceSnapshotSha256'] = 'different-fixture-source'
        self.write_manifest()
        with patch.object(grader, 'check_capsule', return_value=(self.seal, self.capsule)):
            with self.assertRaisesRegex(ValueError, 'another source snapshot'):
                combine.load_document(self.entry, self.selection, self.document)

    def test_failed_partial_batch_is_rejected(self):
        self.seal['jobs'] = [{'shardId': 'FIXTURE-S001', 'documentId': 'SYNTHETIC-A'}]
        grader.save(self.batch / 'jobs/FIXTURE-S001/result.json', {'status': 'TIMEOUT'})
        with patch.object(grader, 'check_capsule', return_value=(self.seal, self.capsule)), \
                patch.object(grader, 'rubric', return_value=({'documents': [self.document]}, {})):
            with self.assertRaisesRegex(ValueError, 'incomplete or failed grading shard'):
                combine.load_document(self.entry, self.selection, self.document)

    def test_training_assisted_batch_cannot_enter_source_only_combination(self):
        self.manifest['sourceMode'] = 'training-assisted'
        self.write_manifest()
        with patch.object(grader, 'check_capsule', return_value=(self.seal, self.capsule)):
            with self.assertRaisesRegex(ValueError, 'Training-assisted'):
                combine.load_document(self.entry, self.selection, self.document)

    def test_source_only_batch_cannot_enter_training_assisted_combination(self):
        self.selection['referenceMode'] = 'training-assisted'
        with patch.object(grader, 'check_capsule', return_value=(self.seal, self.capsule)):
            with self.assertRaisesRegex(ValueError, 'reference mode differs'):
                combine.load_document(self.entry, self.selection, self.document)

    def test_unmarked_legacy_capsule_remains_source_only(self):
        self.manifest.pop('sourceMode')
        self.write_manifest()
        self.selection['referenceMode'] = 'training-assisted'
        with patch.object(grader, 'check_capsule', return_value=(self.seal, self.capsule)):
            with self.assertRaisesRegex(ValueError, 'reference mode differs'):
                combine.load_document(self.entry, self.selection, self.document)

class SnapshotAndVisualBinding(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(dir=grader.HERE)
        self.root = Path(self.temporary.name).resolve()
        self.root.relative_to(grader.HERE.resolve())
        self.registry = {}
        self.snapshots = {}
        for mode in ('source-only', 'training-assisted'):
            root = self.root / mode
            source = root / 'sources/view.css'
            source.parent.mkdir(parents=True)
            source.write_text('Synthetic raw view resource\n', encoding='utf-8')
            references = []
            if mode == 'training-assisted':
                reference = root / 'reference-designs/example.md'
                reference.parent.mkdir()
                reference.write_text('Synthetic explicitly authorized reference\n', encoding='utf-8')
                references = [{'path': 'reference-designs/example.md', 'sha256': grader.digest(reference)}]
            manifest = {'mode': mode, 'projectId': 'test-project1',
                'files': [{'path': 'view.css', 'sha256': grader.digest(source)}], 'referenceFiles': references,
                'referenceSpecificationIncluded': bool(references), 'trainingReferenceAuthorizedByUser': bool(references)}
            grader.save(root / 'manifest.json', manifest)
            self.registry[mode] = {'relativePath': root.relative_to(grader.AGENT).as_posix(),
                'manifestSha256': grader.digest(root / 'manifest.json')}
            self.snapshots[mode] = root
        self.patch_registry = patch.object(combine, 'FIXED_SNAPSHOTS', self.registry)
        self.patch_registry.start()
        self.canonical = self.root / 'canonical/基本設計書/01_example.md'
        self.canonical.parent.mkdir(parents=True)
        self.canonical.write_text('Synthetic canonical artifact\n', encoding='utf-8')
        self.image = self.root / 'fixture.png'
        self.image.write_bytes(b'Synthetic fixture bytes; not a real reviewed screenshot')
        self.review_path = self.root / 'visual-review.json'
        self.entry = {'documentId': 'SYNTHETIC-A', 'canonicalSha256': grader.digest(self.canonical),
            'visualReviewPath': str(self.review_path), 'requiredVisualModes': ['synthetic-initial']}
        self.selection = self.selection_for('source-only')
        self.review = {'schema': 'reverse-agent-native-visual-review/1', 'documentId': 'SYNTHETIC-A',
            'reviewScope': combine.VISUAL_SCOPE, 'originalApplicationExecuted': False,
            'documentSha256': grader.digest(self.canonical), 'canonicalDocumentPath': str(self.canonical),
            'sourceSnapshotSha256': self.selection['sourceSnapshotSha256'], 'referenceMode': 'source-only',
            'reviewer': 'Synthetic fixture only', 'reviewedAt': '2026-10-13T00:00:00Z', 'approved': True,
            'reviewedImages': [{'path': str(self.image), 'sha256': grader.digest(self.image)}],
            'reviewedSourceResources': [{'path': str(self.snapshots['source-only'] / 'sources/view.css'),
                'sha256': grader.digest(self.snapshots['source-only'] / 'sources/view.css')}],
            'modesReviewed': ['synthetic-initial']}
        self.write_review()

    def selection_for(self, mode):
        return {'referenceMode': mode, 'sourceSnapshotSha256': self.registry[mode]['manifestSha256']}

    def write_review(self):
        grader.save(self.review_path, self.review, exclusive=False)

    def tearDown(self):
        self.patch_registry.stop()
        self.temporary.cleanup()

    def test_fixed_snapshot_hash_cannot_be_used_with_another_reference_mode(self):
        for mode, other in (('source-only', 'training-assisted'), ('training-assisted', 'source-only')):
            with self.subTest(mode=mode), self.assertRaisesRegex(ValueError, 'another fixed snapshot'):
                combine.fixed_snapshot({'referenceMode': mode, 'sourceSnapshotSha256': self.registry[other]['manifestSha256']})

    def test_legacy_selection_defaults_to_fixed_source_only_snapshot(self):
        root, manifest = combine.fixed_snapshot({'sourceSnapshotSha256': self.registry['source-only']['manifestSha256']})
        self.assertEqual(root, self.snapshots['source-only'])
        self.assertEqual(manifest['mode'], 'source-only')

    def test_conflicting_capsule_mode_fields_are_rejected(self):
        with self.assertRaisesRegex(ValueError, 'Conflicting'):
            combine.reference_mode({'referenceMode': 'source-only', 'sourceMode': 'training-assisted'}, source_mode_alias=True)

    def test_snapshot_manifest_drift_is_rejected(self):
        path = self.snapshots['source-only'] / 'manifest.json'
        path.write_text(path.read_text(encoding='utf-8') + '\n', encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'manifest changed'):
            combine.fixed_snapshot(self.selection)

    def test_raw_source_bytes_drift_is_rejected(self):
        (self.snapshots['source-only'] / 'sources/view.css').write_text('Changed synthetic raw resource\n', encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'raw source resource changed'):
            combine.fixed_snapshot(self.selection)

    def test_authorized_reference_bytes_drift_is_rejected(self):
        (self.snapshots['training-assisted'] / 'reference-designs/example.md').write_text('Changed synthetic reference\n', encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'authorized reference changed'):
            combine.fixed_snapshot(self.selection_for('training-assisted'))

    def test_visual_reference_modes_cannot_cross(self):
        for mode, other in (('source-only', 'training-assisted'), ('training-assisted', 'source-only')):
            self.review.update(referenceMode=other, sourceSnapshotSha256=self.registry[mode]['manifestSha256'])
            self.write_review()
            with self.subTest(mode=mode), self.assertRaisesRegex(ValueError, 'Visual review reference mode differs'):
                combine.visual_binding(self.entry, self.selection_for(mode), self.canonical)

    def test_same_mode_snapshot_and_visual_pins_are_accepted(self):
        for mode in ('source-only', 'training-assisted'):
            source = self.snapshots[mode] / 'sources/view.css'
            self.review.update(referenceMode=mode, sourceSnapshotSha256=self.registry[mode]['manifestSha256'],
                reviewedSourceResources=[{'path': str(source), 'sha256': grader.digest(source)}])
            self.write_review()
            result = combine.visual_binding(self.entry, self.selection_for(mode), self.canonical)
            self.assertTrue(result['approvedAndBound'])
            self.assertEqual(result['referenceMode'], mode)

    def test_legacy_visual_review_is_source_only(self):
        self.review.pop('referenceMode')
        self.write_review()
        self.assertTrue(combine.visual_binding(self.entry, self.selection, self.canonical)['approvedAndBound'])

    def test_changed_visual_raw_resource_hash_is_rejected(self):
        self.review['reviewedSourceResources'][0]['sha256'] = '0' * 64
        self.write_review()
        with self.assertRaisesRegex(ValueError, 'Reviewed source resource changed'):
            combine.visual_binding(self.entry, self.selection, self.canonical)

    def test_reference_design_hash_cannot_supply_visual_raw_resource(self):
        source = self.snapshots['training-assisted'] / 'reference-designs/example.md'
        self.review.update(referenceMode='training-assisted', sourceSnapshotSha256=self.registry['training-assisted']['manifestSha256'],
            reviewedSourceResources=[{'path': str(source), 'sha256': grader.digest(source)}])
        self.write_review()
        with self.assertRaisesRegex(ValueError, 'does not belong to the fixed source snapshot'):
            combine.visual_binding(self.entry, self.selection_for('training-assisted'), self.canonical)

    def test_changed_visual_image_bytes_are_rejected(self):
        self.image.write_bytes(b'Changed synthetic raster fixture')
        with self.assertRaisesRegex(ValueError, 'Reviewed visual image changed'):
            combine.visual_binding(self.entry, self.selection, self.canonical)

    def test_visual_snapshot_hash_must_match_selection(self):
        self.review['sourceSnapshotSha256'] = '0' * 64
        self.write_review()
        with self.assertRaisesRegex(ValueError, 'another draft or snapshot'):
            combine.visual_binding(self.entry, self.selection, self.canonical)

if __name__ == '__main__':
    unittest.main()

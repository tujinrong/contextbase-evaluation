"""Scoring integrity checks with synthetic data, no application execution."""
from pathlib import Path
import json
import tempfile
import unittest
from unittest.mock import patch
from types import SimpleNamespace
import grader

class EvidenceIntegrity(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.capsule = Path(self.temporary.name)
        records = []
        for name in ('generated/example.md', 'source/example.cs', 'reference/example.md'):
            target = self.capsule / name
            target.parent.mkdir()
            target.write_text('first\nlimit 12\nlast\n', encoding='utf-8')
            records.append({'path': name, 'sha256': grader.digest(target)})
        (self.capsule / 'manifest.json').write_text(json.dumps({'files': records}), encoding='utf-8')
        self.request = {'documentId': 'DOC', 'shardId': 'SHARD', 'requireSafetyReview': False,
            'rows': [{'evaluationId': 'ROW', 'maximumPenalty': 1, 'allowedDeductions': [0, -1]}]}
        self.row = {'evaluationId': 'ROW', 'judgement': '一致', 'actualDeduction': 0, 'defectId': None,
            'reason': '文書の上限と単位を確認した。', 'generatedEvidence': [self.evidence('generated/example.md')],
            'critical': False, 'mandatoryMissing': False, 'sourceFidelity': {'judgement': '一致',
                'reason': '実装の上限を確認した。', 'sourceEvidence': [self.evidence('source/example.cs')]}}
        self.answer = {'schema': 'independent-semantic-grades/1', 'documentId': 'DOC', 'shardId': 'SHARD',
            'rows': [self.row], 'safetyChecks': [], 'limitations': []}

    @staticmethod
    def evidence(path):
        return {'path': path, 'startLine': 2, 'endLine': 2, 'quote': 'limit 12'}

    def tearDown(self):
        self.temporary.cleanup()

    def test_valid_evidence_and_complete_rows(self):
        grader.validate_answer(self.answer, self.request, self.capsule)

    def test_schema_rejects_empty_quotes_before_provider_output_is_saved_as_passed(self):
        from jsonschema import Draft202012Validator
        self.row['generatedEvidence'][0]['quote'] = ''
        self.assertTrue(list(Draft202012Validator(grader.SCHEMA).iter_errors(self.answer)))

    def test_schema_binds_evidence_roles_in_rows_and_safety_checks(self):
        from jsonschema import Draft202012Validator
        schema = Draft202012Validator(grader.SCHEMA)
        self.row['sourceFidelity']['sourceEvidence'] = [self.evidence('reference/example.md')]
        self.assertTrue(list(schema.iter_errors(self.answer)))
        self.row['sourceFidelity']['sourceEvidence'] = [self.evidence('source/example.cs')]
        check = {'topic': 'synthetic', 'judgement': 'CLEAR', 'reason': '人工の根拠確認。',
                 'generatedEvidence': [self.evidence('generated/example.md')],
                 'sourceEvidence': [self.evidence('reference/example.md')]}
        self.answer['safetyChecks'] = [check]
        self.assertTrue(list(schema.iter_errors(self.answer)))
        check['sourceEvidence'] = [self.evidence('source/example.cs')]
        self.assertEqual([], list(schema.iter_errors(self.answer)))
        grader.validate_answer(self.answer, self.request, self.capsule)
        check['generatedEvidence'] = [self.evidence('source/example.cs')]
        self.assertTrue(list(schema.iter_errors(self.answer)))

    def test_source_cannot_fill_missing_document_evidence(self):
        self.row['generatedEvidence'] = []
        with self.assertRaises(ValueError):
            grader.validate_answer(self.answer, self.request, self.capsule)

    def test_assessed_safety_needs_document_evidence_even_when_absent_or_outside_scope(self):
        for judgement in ('CLEAR', 'CONTRADICTION', 'MISSING', 'NOT_APPLICABLE'):
            with self.subTest(judgement=judgement):
                self.answer['safetyChecks'] = [{'topic': 'synthetic', 'judgement': judgement,
                    'reason': '範囲と根拠を独立確認。', 'generatedEvidence': [],
                    'sourceEvidence': [self.evidence('source/example.cs')]}]
                with self.assertRaises(ValueError):
                    grader.validate_answer(self.answer, self.request, self.capsule)

    def test_safety_clearance_and_contradiction_require_raw_observed_evidence(self):
        for judgement in ('CLEAR', 'CONTRADICTION'):
            with self.subTest(judgement=judgement):
                self.answer['safetyChecks'] = [{'topic': 'synthetic', 'judgement': judgement,
                    'reason': '確認した。', 'generatedEvidence': [self.evidence('generated/example.md')],
                    'sourceEvidence': []}]
                with self.assertRaises(ValueError):
                    grader.validate_answer(self.answer, self.request, self.capsule)

    def test_missing_nonapplicable_or_unassessed_safety_does_not_fabricate_source(self):
        for judgement in ('MISSING', 'NOT_APPLICABLE', 'UNASSESSED'):
            with self.subTest(judgement=judgement):
                self.answer['safetyChecks'] = [{'topic': 'synthetic', 'judgement': judgement,
                    'reason': '範囲又は未観測の設計意図を区別。',
                    'generatedEvidence': [] if judgement == 'UNASSESSED' else [self.evidence('generated/example.md')],
                    'sourceEvidence': []}]
                grader.validate_answer(self.answer, self.request, self.capsule)

    def test_observed_match_requires_raw_source_evidence(self):
        self.row['sourceFidelity']['sourceEvidence'] = []
        with self.assertRaises(ValueError):
            grader.validate_answer(self.answer, self.request, self.capsule)

    def test_quoted_claim_must_exist_in_pinned_range(self):
        self.row['generatedEvidence'][0]['quote'] = 'limit 95'
        with self.assertRaises(ValueError):
            grader.validate_answer(self.answer, self.request, self.capsule)

    def test_reference_cannot_supply_generated_or_observed_source_evidence(self):
        for prefix in ('generated/', 'source/'):
            with self.subTest(prefix=prefix):
                escaped = prefix + '../reference/example.md'
                manifest = grader.load(self.capsule / 'manifest.json')
                manifest['files'].append({'path': escaped})
                (self.capsule / 'manifest.json').write_text(json.dumps(manifest), encoding='utf-8')
                self.assertFalse(grader.evidence_valid([self.evidence(escaped)], self.capsule, prefix))

    def test_generated_and_source_evidence_cannot_exchange_roles(self):
        self.row['generatedEvidence'] = [self.evidence('generated/../source/example.cs')]
        with self.assertRaises(ValueError):
            grader.validate_answer(self.answer, self.request, self.capsule)
        self.row['generatedEvidence'] = [self.evidence('generated/example.md')]
        self.row['sourceFidelity']['sourceEvidence'] = [self.evidence('source/../generated/example.md')]
        with self.assertRaises(ValueError):
            grader.validate_answer(self.answer, self.request, self.capsule)

    def test_existing_unlisted_file_cannot_supply_evidence(self):
        for prefix in ('generated/', 'source/'):
            with self.subTest(prefix=prefix):
                relative = prefix + 'unlisted.md'
                (self.capsule / relative).write_text('first\nlimit 12\nlast\n', encoding='utf-8')
                self.assertFalse(grader.evidence_valid([self.evidence(relative)], self.capsule, prefix))

    def test_path_must_match_manifest_spelling_exactly(self):
        for prefix, filename in (('generated/', 'example.md'), ('source/', 'example.cs')):
            with self.subTest(prefix=prefix):
                self.assertFalse(grader.evidence_valid([self.evidence(prefix + './' + filename)], self.capsule, prefix))

    def test_quote_cannot_be_found_outside_pinned_lines(self):
        self.row['generatedEvidence'][0].update(startLine=1, endLine=1)
        with self.assertRaises(ValueError):
            grader.validate_answer(self.answer, self.request, self.capsule)

    def test_no_silent_missing_rows(self):
        self.answer['rows'] = []
        with self.assertRaises(ValueError):
            grader.validate_answer(self.answer, self.request, self.capsule)

    def test_duplicate_rows_cannot_replace_complete_coverage(self):
        self.answer['rows'].append(self.row.copy())
        with self.assertRaises(ValueError):
            grader.validate_answer(self.answer, self.request, self.capsule)

    def test_unassessed_is_not_zero_penalty_match(self):
        self.row['judgement'] = '未評価'
        with self.assertRaises(ValueError):
            grader.validate_answer(self.answer, self.request, self.capsule)

    def test_applicability_cannot_shrink_denominator_without_approval(self):
        self.row['judgement'] = '非適用'
        with self.assertRaises(ValueError):
            grader.validate_answer(self.answer, self.request, self.capsule)

    def test_attribute_error_cannot_use_diagram_deduction(self):
        self.row.update(judgement='属性誤り', actualDeduction=-3, defectId='LIMIT')
        with self.assertRaises(ValueError):
            grader.validate_answer(self.answer, self.request, self.capsule)

    def test_raw_defects_cannot_be_zero_before_identity_review(self):
        for state, maximum in (('属性誤り', 1), ('粒度不足', 2), ('内容誤り', 3), ('欠落', 3)):
            with self.subTest(state=state):
                self.request['rows'][0].update(maximumPenalty=maximum, allowedDeductions=[0, -maximum])
                self.row.update(judgement=state, actualDeduction=0, defectId='CAUSE')
                with self.assertRaisesRegex(ValueError, 'permitted negative'):
                    grader.validate_answer(self.answer, self.request, self.capsule)

    def test_repeated_raw_defect_retains_negative_deductions(self):
        import copy
        second_request = copy.deepcopy(self.request['rows'][0])
        second_request['evaluationId'] = 'ROW2'
        self.request['rows'].append(second_request)
        self.row.update(judgement='属性誤り', actualDeduction=-1, defectId='CAUSE')
        second = copy.deepcopy(self.row)
        second['evaluationId'] = 'ROW2'
        self.answer['rows'].append(second)
        grader.validate_answer(self.answer, self.request, self.capsule)
        self.assertEqual([row['actualDeduction'] for row in self.answer['rows']], [-1, -1])

class DeductionIntegrity(unittest.TestCase):
    def test_attribute_group_is_not_split_across_shards(self):
        rows = [{'evaluationId': str(i), 'subject': 'item-' + str(i // 3),
            'source': {'path': 'example.md', 'startLine': i // 3 + 1, 'endLine': i // 3 + 1}} for i in range(9)]
        shards = list(grader.grouped_shards(rows, 5))
        self.assertEqual([len(shard) for shard in shards], [3, 3, 3])
        self.assertEqual([r['evaluationId'] for s in shards for r in s], [str(i) for i in range(9)])

    def test_same_cause_maximum_once_per_document(self):
        original = {'A': {'maximumPenalty': 1, 'documentId': 'DOC', 'category': '属性'},
            'B': {'maximumPenalty': 3, 'documentId': 'DOC', 'category': '説明'}}
        rows = [{'evaluationId': 'A', 'judgement': '属性誤り', 'actualDeduction': -1, 'defectId': 'LIMIT'},
            {'evaluationId': 'B', 'judgement': '内容誤り', 'actualDeduction': -3, 'defectId': 'LIMIT'}]
        result = grader.totals(rows, original)
        self.assertEqual(result['maximumPoints'], 4)
        self.assertEqual(result['deduplicatedPenalty'], 3)
        self.assertEqual(result['score'], 1)

    def test_same_defect_in_distinct_documents_counts_twice(self):
        original = {'A': {'maximumPenalty': 1, 'documentId': 'BASIC', 'category': '属性'},
            'B': {'maximumPenalty': 1, 'documentId': 'DETAIL', 'category': '属性'}}
        rows = [{'evaluationId': key, 'judgement': '属性誤り', 'actualDeduction': -1, 'defectId': 'LIMIT'} for key in original]
        self.assertEqual(grader.totals(rows, original)['deduplicatedPenalty'], 2)

    def test_held_row_prevents_formal_score(self):
        original = {'A': {'maximumPenalty': 3, 'documentId': 'DOC', 'category': 'ER'}}
        row = {'evaluationId': 'A', 'judgement': '保留', 'actualDeduction': None, 'defectId': None}
        result = grader.totals([row], original)
        self.assertIsNone(result['score'])
        self.assertIsNone(result['percentage'])

    def test_zero_maximum_is_not_100_percent(self):
        self.assertIsNone(grader.totals([], {})['percentage'])

class RunExitIntegrity(unittest.TestCase):
    def run_with_result(self, status):
        args = SimpleNamespace(batch=grader.HERE / 'synthetic-batch', max_jobs=1, workers=1,
            deadline='2099-01-01T00:00:00Z', timeout_seconds=1)
        seal = {'jobs': [{'shardId': 'SYNTHETIC'}]}
        with patch.object(grader, 'check_capsule', return_value=(seal, grader.HERE)), \
                patch.object(grader, 'one_job', return_value={'shardId': 'SYNTHETIC', 'status': status}), \
                patch('builtins.print'):
            grader.run(args)

    def test_failed_shard_propagates_nonzero_exit(self):
        for status in ('TIMEOUT', 'CLI_FAILED', 'VALIDATION_OR_PROVIDER_FAILED', 'DEADLINE_EXPIRED'):
            with self.subTest(status=status), self.assertRaises(SystemExit) as raised:
                self.run_with_result(status)
            self.assertEqual(raised.exception.code, 1)

    def test_passed_shard_completes_normally(self):
        self.run_with_result('PASSED')

    def test_one_failed_parallel_shard_cannot_be_hidden_by_later_successes(self):
        args = SimpleNamespace(batch=grader.HERE / 'synthetic-batch', max_jobs=None, workers=4,
            deadline='2099-01-01T00:00:00Z', timeout_seconds=1)
        seal = {'jobs': [{'shardId': str(index)} for index in range(8)]}
        def result(_batch, _capsule, job, _deadline, _timeout):
            return {**job, 'status': 'CLI_FAILED' if job['shardId'] == '0' else 'PASSED'}
        with patch.object(grader, 'check_capsule', return_value=(seal, grader.HERE)), \
                patch.object(grader, 'one_job', side_effect=result) as calls, patch('builtins.print'), \
                self.assertRaises(SystemExit) as raised:
            grader.run(args)
        self.assertEqual(1, raised.exception.code)
        self.assertEqual(8, calls.call_count)

if __name__ == '__main__':
    unittest.main()

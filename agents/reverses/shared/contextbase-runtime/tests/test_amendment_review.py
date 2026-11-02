"""Synthetic amendment review contracts; no source execution or model calls."""
from copy import deepcopy
from pathlib import Path
import tempfile
import unittest

from contextbase_runtime import contracts as c, review_set
from contextbase_runtime.sources import SourceAccess
from test_review_set import fixture, answer, EVIDENCE


POLICY = 'contextbase-candidate-amendment/1'


def amended():
    task, view = fixture(records=2, unknowns=1, modern=False, facts=False)
    task.update(amendmentPolicy=POLICY, amendmentIssueBindings=[
        {'id': 'original:finding', 'sha256': 'a' * 64,
         'dispositionSha256': 'b' * 64, 'requirement': 'catalog'}])
    return task, view


def response(task, view, unit):
    result = answer(task, view, unit)
    bindings = {row['id']: row for row in task['amendmentIssueBindings']}
    result['amendmentIssueChecks'] = [
        {'issueId': key, 'issueSha256': bindings[key]['sha256'],
         'dispositionSha256': bindings[key]['dispositionSha256'], 'status': 'pass',
         'reason': 'Independently checked the author disposition against original source',
         'evidence': [deepcopy(EVIDENCE)]} for key in unit['issueIds']]
    return result


class AmendmentReviewTests(unittest.TestCase):
    def prepared(self):
        task, view = amended()
        units = review_set.make_units(task, view, max_records=1)
        return task, view, units, [response(task, view, unit) for unit in units]

    def test_issue_review_is_separate_and_keeps_full_review_coverage(self):
        task, view = amended()
        units = review_set.make_units(task, view, max_records=1)
        self.assertEqual('issues', units[0]['kind'])
        self.assertEqual(['original:finding'], units[0]['issueIds'])
        for field in ('recordKeys', 'unknownIds', 'requirements', 'scopes'):
            self.assertEqual([], units[0][field])
        self.assertEqual(sorted(view['records']), sorted(key for u in units for key in u['recordKeys']))
        self.assertEqual(sorted(view['unknowns']), sorted(key for u in units for key in u['unknownIds']))
        self.assertEqual(task['requirements'], [key for u in units for key in u['requirements']])
        results = [response(task, view, unit) for unit in units]
        merged = review_set.aggregate(task, view, units, results)
        self.assertEqual(['original:finding'], [row['issueId'] for row in merged['amendmentIssueChecks']])

    def test_independent_reviewer_can_reject_author_refutation(self):
        for status in ('fail', 'unknown'):
            with self.subTest(status=status):
                task, view, units, results = self.prepared()
                results[0]['amendmentIssueChecks'][0].update(
                    status=status, reason='Original source does not support author refutation')
                merged = review_set.aggregate(task, view, units, results)
                self.assertEqual(status, merged['checks'][0]['status'])
                self.assertEqual('pass', merged['checks'][1]['status'])

    def test_issue_checks_reject_missing_duplicate_extra_stale_and_unsupported_positive_claims(self):
        for change in ('missing-field', 'missing', 'duplicate', 'extra', 'issueSha256',
                       'dispositionSha256', 'issueId', 'evidence'):
            with self.subTest(change=change):
                task, view, units, results = self.prepared()
                checks = results[0]['amendmentIssueChecks']
                if change == 'missing-field':
                    del results[0]['amendmentIssueChecks']
                elif change == 'missing':
                    checks.clear()
                elif change in ('duplicate', 'extra'):
                    checks.append({**checks[0], **({'issueId': 'outside'} if change == 'extra' else {})})
                else:
                    checks[0][change] = [] if change == 'evidence' else 'e' * 64
                with self.assertRaises(ValueError):
                    review_set.aggregate(task, view, units, results)

    def test_exact_set_checks_catch_duplicates_even_when_array_length_matches(self):
        task, view = amended()
        task['amendmentIssueBindings'].append({**task['amendmentIssueBindings'][0], 'id': 'other'})
        units = review_set.make_units(task, view)
        results = [response(task, view, unit) for unit in units]
        results[0]['amendmentIssueChecks'][1] = deepcopy(results[0]['amendmentIssueChecks'][0])
        with self.assertRaisesRegex(ValueError, 'Duplicate'):
            review_set.aggregate(task, view, units, results)

    def test_issue_only_review_cannot_replace_any_record_or_global_coverage(self):
        for removed in ('records', 'global', 'issues'):
            with self.subTest(removed=removed):
                task, view, units, results = self.prepared()
                index = next(i for i, unit in enumerate(units) if unit['kind'] == removed)
                units.pop(index)
                results.pop(index)
                with self.assertRaisesRegex(ValueError, 'partition'):
                    review_set.aggregate(task, view, units, results)

    def test_issue_unit_cannot_expand_into_records_or_ordinary_units(self):
        task, view, units, _ = self.prepared()
        units[0]['recordKeys'] = ['object-0']
        with self.assertRaises(ValueError):
            review_set.unit_schema(task, view, units[0])
        task, view, units, _ = self.prepared()
        units[1]['issueIds'] = ['original:finding']
        with self.assertRaises(ValueError):
            review_set.unit_schema(task, view, units[1])

    def test_amendment_policy_requires_nonempty_valid_unique_owned_bindings(self):
        for change in ('unknown-policy', 'missing-policy', 'missing-bindings', 'empty',
                       'duplicate', 'owner', 'hash', 'extra-field'):
            with self.subTest(change=change):
                task, view = amended()
                if change == 'unknown-policy':
                    task['amendmentPolicy'] = 'future/2'
                elif change == 'missing-policy':
                    del task['amendmentPolicy']
                elif change == 'missing-bindings':
                    del task['amendmentIssueBindings']
                elif change == 'empty':
                    task['amendmentIssueBindings'] = []
                elif change == 'duplicate':
                    task['amendmentIssueBindings'] *= 2
                else:
                    task['amendmentIssueBindings'][0][
                        {'owner': 'requirement', 'hash': 'sha256', 'extra-field': 'extra'}[change]] = 'outside'
                with self.assertRaises(ValueError):
                    c.result_schema(task)
                with self.assertRaises(ValueError):
                    review_set.make_units(task, view)

    def test_ordinary_contract_and_extract_schema_do_not_gain_amendment_fields(self):
        task, view = fixture()
        baseline = c.result_schema(task)
        units = review_set.make_units(task, view)
        self.assertNotIn('amendmentIssueChecks', baseline['properties'])
        self.assertTrue(all('issueIds' not in unit for unit in units))
        self.assertTrue(all('amendmentIssueChecks' not in review_set.unit_schema(task, view, unit)['properties']
                            for unit in units))
        result = review_set.aggregate(task, view, units, [answer(task, view, unit) for unit in units])
        self.assertNotIn('amendmentIssueChecks', result)
        task['operation'] = 'extract'
        baseline_extract = c.result_schema(task)
        task.update(amendmentPolicy=POLICY, amendmentIssueBindings=[])
        self.assertEqual(baseline_extract, c.result_schema(task))

    def test_final_contract_checks_exact_binding_source_evidence_and_owner_verdict(self):
        home = Path(__file__).resolve().parents[1] / '.tmp'
        home.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(prefix='amendment-review-', dir=home) as temporary:
            root = Path(temporary)
            original = root / 'original'
            original.mkdir()
            (original / 'source.cs').write_text('Synthetic original source\n', encoding='utf-8')
            source = SourceAccess.create(original, root / 'snapshot', project_id='amendment-review',
                                         allowed_paths=['.'], excluded_paths=[])
            task, view = amended()
            task['amendmentIssueBindings'].append({**task['amendmentIssueBindings'][0], 'id': 'second'})
            units = review_set.make_units(task, view)
            results = [response(task, view, unit) for unit in units]
            merged = review_set.aggregate(task, view, units, results)
            for row in merged['checks'] + merged['unknownChecks'] + merged['amendmentIssueChecks']:
                row['evidence'] = [source.evidence('source.cs', 1, 1)]
            c.validate_result(merged, task, source)
            for change in ('missing', 'duplicate', 'extra', 'hash', 'disposition', 'source',
                           'empty-evidence', 'hidden-fail', 'hidden-unknown'):
                with self.subTest(change=change):
                    invalid = deepcopy(merged)
                    issue = invalid['amendmentIssueChecks'][0]
                    if change == 'missing':
                        del invalid['amendmentIssueChecks']
                    elif change == 'duplicate':
                        invalid['amendmentIssueChecks'][1] = deepcopy(issue)
                    elif change == 'extra':
                        issue['issueId'] = 'outside'
                    elif change == 'hash':
                        issue['issueSha256'] = 'e' * 64
                    elif change == 'disposition':
                        issue['dispositionSha256'] = 'e' * 64
                    elif change == 'source':
                        issue['evidence'][0]['sha256'] = 'e' * 64
                    elif change == 'empty-evidence':
                        issue['evidence'] = []
                    else:
                        issue['status'] = 'fail' if change == 'hidden-fail' else 'unknown'
                    with self.assertRaises(ValueError):
                        c.validate_result(invalid, task, source)


if __name__ == '__main__':
    unittest.main()

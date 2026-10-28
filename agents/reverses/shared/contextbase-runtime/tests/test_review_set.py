"""Review assignment and conservative aggregation, without a model or input execution."""
from copy import deepcopy
import unittest

from contextbase_runtime import catalog, contracts
from contextbase_runtime import review_set


EVIDENCE = {'path': 'source.cs', 'startLine': 1, 'endLine': 1, 'sha256': '1' * 64}


def fixture(*, records=9, unknowns=2, modern=True, facts=True):
    requirements = [
        {'id': 'catalog', 'stage': 'discovery', 'scope': 'system', 'question': 'Catalog', 'requires': []},
        {'id': 'empty', 'stage': 'discovery', 'scope': 'empty-system', 'question': 'Empty', 'requires': []},
    ]
    rows = {}
    for number in range(records):
        key = f'object-{number}'
        classification = ({'category': 'common', 'scope': 'system', 'responsibility': 'shared',
                           'rationale': 'source', 'alternative': 'not independent',
                           'consumers': ['object-0']} if number == 1 else None)
        row = {'key': key, 'kind': 'common' if number == 1 else 'support',
               'ownerRequirement': 'catalog', 'name': key, 'statement': 'fixture',
               'basis': 'observed-source', 'evidence': [deepcopy(EVIDENCE)], 'dependsOn': [],
               'dependencies': [], 'classification': classification}
        rows[key] = {**row, 'id': contracts.record_id('fixture', row['kind'], key),
                     'version': contracts.digest(row)}
    questions = {f'u-{number}': {'id': f'u-{number}', 'sha256': str(number + 2) * 64,
                 'content': {'id': f'u-{number}', 'question': 'Check',
                             'relatedRequirements': ['catalog'], 'blocksRequirements': ['catalog'],
                             'scopeReason': 'fixture'}, 'owners': ['catalog']}
                 for number in range(unknowns)}
    view = {'records': rows, 'unknowns': questions, 'acceptedRequirements': ['catalog', 'empty'],
            'invalidatedRequirements': [], 'contentHashes': {'catalog': 'a' * 64, 'empty': 'b' * 64}}
    task = {'id': 'root-review', 'operation': 'verify', 'stage': 'discovery',
            'candidate': 'c' * 64, 'viewSha256': contracts.digest(view),
            'requirements': ['catalog', 'empty'], 'goalRequirements': requirements,
            'goalRequirementIds': ['catalog', 'empty'],
            'unknownBindings': [{'id': key, 'sha256': item['sha256']} for key, item in questions.items()]}
    if modern:
        task.update(catalogPolicy=catalog.VERSION, classificationBindings=catalog.bindings(rows))
    if facts:
        task['sourceFactsSha256'] = 'd' * 64
    return task, view


def answer(task, view, unit):
    verdict = lambda **fields: {**fields, 'status': 'pass', 'reason': 'Read original',
                                'evidence': [deepcopy(EVIDENCE)]}
    classifications = {item['key']: item for item in task.get('classificationBindings', [])}
    return {'unitId': unit['id'], 'candidateSha256': task['candidate'],
            'viewSha256': task['viewSha256'],
            'recordChecks': [verdict(key=key, recordSha256=view['records'][key]['version'])
                             for key in unit['recordKeys']],
            'classificationChecks': [verdict(key=key, recordSha256=classifications[key]['sha256'])
                                     for key in unit['recordKeys'] if key in classifications],
            'unknownChecks': [{'unknownId': key, 'unknownSha256': view['unknowns'][key]['sha256'],
                               'status': 'resolved', 'blocksRequirements': [], 'reason': 'Read original',
                               'evidence': [deepcopy(EVIDENCE)]} for key in unit['unknownIds']],
            'checks': [verdict(requirement=key) for key in unit['requirements']],
            'scopeChecks': [verdict(scope=scope) for scope in unit['scopes']],
            'findings': [], 'unknowns': [],
            'factUsageCheck': verdict() if task.get('sourceFactsSha256') else None}


class ReviewSetTests(unittest.TestCase):
    def prepared(self, **kwargs):
        task, view = fixture(**kwargs)
        units = review_set.make_units(task, view, max_records=3)
        return task, view, units, [answer(task, view, unit) for unit in units]

    def test_assignment_covers_all_records_unknowns_and_zero_record_scopes(self):
        task, view, units, answers = self.prepared()
        self.assertEqual(sorted(view['records']), sorted(key for u in units for key in u['recordKeys']))
        self.assertEqual(sorted(view['unknowns']), sorted(key for u in units for key in u['unknownIds']))
        self.assertEqual(['empty-system', 'system'], sorted(scope for u in units for scope in u['scopes']))
        self.assertEqual(['catalog', 'empty'], sorted(key for u in units for key in u['requirements']))
        self.assertTrue(all(len(u['recordKeys']) <= 3 for u in units))
        for unit, response in zip(units, answers):
            review_set.validate_unit(task, view, unit, response)
        merged = review_set.aggregate(task, view, units, answers)
        contracts.validate(merged, contracts.result_schema(task))
        self.assertTrue(all(row['status'] == 'pass' for row in merged['checks']))
        self.assertEqual(1, len(merged['classificationChecks']))

    def test_record_failure_and_unknown_cannot_be_hidden_by_global_pass(self):
        for status in ('fail', 'unknown'):
            with self.subTest(status=status):
                task, view, units, answers = self.prepared()
                answers[0]['recordChecks'][0]['status'] = status
                merged = review_set.aggregate(task, view, units, answers)
                self.assertEqual(status, next(row for row in merged['checks']
                                              if row['requirement'] == 'catalog')['status'])

    def test_all_records_including_support_are_checked(self):
        task, view, units, answers = self.prepared()
        answers[0]['recordChecks'].pop()
        with self.assertRaises(ValueError):
            review_set.aggregate(task, view, units, answers)

    def test_missing_or_duplicate_assignments_are_rejected(self):
        for change in ('missing-record', 'duplicate-unit', 'missing-global', 'missing-unknown', 'extra-record'):
            with self.subTest(change=change):
                task, view, units, answers = self.prepared()
                if change == 'missing-record':
                    units[0]['recordKeys'].pop()
                    answers[0]['recordChecks'].pop()
                elif change == 'duplicate-unit':
                    units.append(deepcopy(units[0]))
                    answers.append(deepcopy(answers[0]))
                elif change == 'missing-global':
                    units.pop()
                    answers.pop()
                elif change == 'missing-unknown':
                    unit = next(u for u in units if u['unknownIds'])
                    position = units.index(unit)
                    unit['unknownIds'].pop()
                    answers[position]['unknownChecks'].pop()
                else:
                    units[0]['recordKeys'].append('outside')
                with self.assertRaises(ValueError):
                    review_set.aggregate(task, view, units, answers)

    def test_exact_bindings_reject_old_view_record_unknown_and_classification(self):
        for field in ('viewSha256', 'recordSha256', 'unknownSha256', 'classificationSha256'):
            with self.subTest(field=field):
                task, view, units, answers = self.prepared()
                if field == 'viewSha256':
                    answers[0][field] = 'e' * 64
                elif field == 'recordSha256':
                    answers[0]['recordChecks'][0][field] = 'e' * 64
                elif field == 'unknownSha256':
                    target = next(a for a in answers if a['unknownChecks'])
                    target['unknownChecks'][0][field] = 'e' * 64
                else:
                    target = next(a for a in answers if a['classificationChecks'])
                    target['classificationChecks'][0]['recordSha256'] = 'e' * 64
                with self.assertRaises(ValueError):
                    review_set.aggregate(task, view, units, answers)

    def test_changed_view_and_task_bindings_are_rejected(self):
        task, view, _, _ = self.prepared()
        view['records']['object-0']['statement'] = 'new candidate'
        with self.assertRaises(ValueError):
            review_set.make_units(task, view)
        task['viewSha256'] = contracts.digest(view)
        task['unknownBindings'].pop()
        with self.assertRaises(ValueError):
            review_set.make_units(task, view)

    def test_positive_claims_and_resolutions_need_evidence(self):
        for field in ('recordChecks', 'classificationChecks', 'unknownChecks', 'checks', 'scopeChecks', 'factUsageCheck'):
            with self.subTest(field=field):
                task, view, units, answers = self.prepared()
                target = next(a for a in answers if a[field])
                (target[field] if field == 'factUsageCheck' else target[field][0])['evidence'] = []
                with self.assertRaises(ValueError):
                    review_set.aggregate(task, view, units, answers)

    def test_unknown_resolution_cannot_keep_blockers(self):
        task, view, units, answers = self.prepared()
        target = next(a for a in answers if a['unknownChecks'])
        target['unknownChecks'][0]['blocksRequirements'] = ['catalog']
        with self.assertRaises(ValueError):
            review_set.aggregate(task, view, units, answers)

    def test_local_fact_usage_failure_cannot_be_hidden(self):
        task, view, units, answers = self.prepared()
        answers[0]['factUsageCheck']['status'] = 'fail'
        merged = review_set.aggregate(task, view, units, answers)
        self.assertEqual('fail', merged['factUsageCheck']['status'])

    def test_findings_and_new_unknowns_are_namespaced_without_rewriting_old_questions(self):
        task, view, units, answers = self.prepared()
        for response in answers[:2]:
            response['findings'] = [{'id': 'same', 'severity': 'minor', 'requirement': 'catalog',
                                     'detail': 'Check', 'evidence': [deepcopy(EVIDENCE)]}]
            response['unknowns'] = [{'id': 'same', 'question': 'Question',
                                    'relatedRequirements': ['catalog'], 'blocksRequirements': [],
                                    'scopeReason': 'scope'}]
        merged = review_set.aggregate(task, view, units, answers)
        self.assertEqual(2, len(set(row['id'] for row in merged['findings'])))
        self.assertEqual(2, len(set(row['id'] for row in merged['unknowns'])))
        self.assertEqual(sorted(view['unknowns']), sorted(row['unknownId'] for row in merged['unknownChecks']))

    def test_large_single_record_is_assigned_not_discarded(self):
        task, view = fixture(records=1, unknowns=0)
        view['records']['object-0']['statement'] = 'x' * 50_000
        view['records']['object-0']['version'] = contracts.digest({
            key: value for key, value in view['records']['object-0'].items() if key not in {'id', 'version'}})
        task['viewSha256'] = contracts.digest(view)
        units = review_set.make_units(task, view, max_chars=100)
        self.assertEqual(['object-0'], [key for u in units for key in u['recordKeys']])

    def test_minimal_legacy_shape_has_no_catalog_or_fact_fields_in_aggregate(self):
        task, view, units, answers = self.prepared(modern=False, facts=False, unknowns=0)
        result = review_set.aggregate(task, view, units, answers)
        self.assertNotIn('classificationChecks', result)
        self.assertNotIn('sourceFactsSha256', result)
        contracts.validate(result, contracts.result_schema(task))

    def test_retained_catalog_and_new_relationship_get_distinct_global_checks(self):
        task, view = fixture(records=3, unknowns=0)
        task['stage'] = 'relationship'
        task['goalRequirements'].append({'id': 'links', 'stage': 'relationship', 'scope': 'system',
                                         'question': 'Connections', 'requires': ['catalog']})
        task['goalRequirementIds'].append('links')
        task['requirements'].append('links')
        view['acceptedRequirements'].append('links')
        view['records']['object-2']['ownerRequirement'] = 'links'
        view['records']['object-2']['kind'] = 'relation'
        view['records']['object-2']['version'] = contracts.digest({
            key: value for key, value in view['records']['object-2'].items() if key not in {'id', 'version'}})
        task['viewSha256'] = contracts.digest(view)
        units = review_set.make_units(task, view)
        self.assertEqual(['empty-system', 'system'], sorted(s for u in units for s in u['scopes']))
        merged = review_set.aggregate(task, view, units, [answer(task, view, unit) for unit in units])
        self.assertEqual(task['requirements'], [row['requirement'] for row in merged['checks']])

    def test_multiple_original_catalog_obligations_in_same_scope_get_one_scope_check(self):
        task, view = fixture(records=1, unknowns=0)
        task['goalRequirements'][1]['scope'] = 'system'
        units = review_set.make_units(task, view)
        self.assertEqual(['system'], [scope for unit in units for scope in unit['scopes']])
        self.assertEqual(2, len([unit for unit in units if unit['kind'] == 'global']))
        review_set.aggregate(task, view, units, [answer(task, view, unit) for unit in units])

    def test_global_may_report_cross_obligation_findings_but_not_extra_check_verdicts(self):
        task, view, units, answers = self.prepared()
        position = next(i for i, unit in enumerate(units) if unit['requirements'] == ['empty'])
        answers[position]['findings'] = [{'id': 'outside-plan-entry', 'severity': 'blocking',
                                          'requirement': 'catalog', 'detail': 'Missed original entry',
                                          'evidence': [deepcopy(EVIDENCE)]}]
        result = review_set.aggregate(task, view, units, answers)
        self.assertEqual('catalog', result['findings'][0]['requirement'])
        answers[position]['checks'].append(deepcopy(answers[position]['checks'][0]))
        with self.assertRaises(ValueError):
            review_set.aggregate(task, view, units, answers)

    def test_grouping_limits_are_positive_integers(self):
        task, view = fixture()
        for kwargs in ({'max_records': 0}, {'max_records': True}, {'max_chars': -1}, {'max_chars': 2.5}):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                review_set.make_units(task, view, **kwargs)

    def test_view_rehash_does_not_hide_stale_record_version(self):
        task, view = fixture()
        view['records']['object-0']['statement'] = 'different meaning'
        task['viewSha256'] = contracts.digest(view)
        with self.assertRaisesRegex(ValueError, 'content and version'):
            review_set.make_units(task, view)


if __name__ == '__main__':
    unittest.main()

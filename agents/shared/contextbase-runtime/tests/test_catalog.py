"""Mechanical catalog constraints, independent of source language or names."""
from copy import deepcopy
import unittest

from contextbase_runtime import catalog, contracts


SHA = 'a' * 64
EVIDENCE = {'path': 'sample.cs', 'startLine': 1, 'endLine': 2, 'sha256': SHA}


class Source:
    def __init__(self):
        self.seen = []

    def verify_evidence(self, evidence):
        if evidence != EVIDENCE:
            raise ValueError('Evidence is outside the sealed synthetic source')
        self.seen.append(evidence)

    def verify_evidence_many(self, refs):
        for evidence in refs:
            self.verify_evidence(evidence)


def classification(category, **changes):
    base = {'category': category, 'scope': 'scope-one'}
    if category == 'main':
        base.update(area='Registration', actors=['Operator'], businessObject='Record',
                    purpose='Register', trigger='Submit', outcome='Stored',
                    rationale='Source role', alternative='Considered operation', entryRefs=['entry'])
    elif category == 'operation':
        base.update(parent='main', purpose='Validate', useContext='During registration',
                    outcome='Valid', rationale='Internal step', alternative='Considered main', entryRefs=['entry'])
    elif category == 'common':
        base.update(responsibility='Normalize', consumers=['main', 'operation'],
                    rationale='Shared processing', alternative='Considered operation')
    else:
        base.update(tentativeKind='function', impact='count-or-coverage',
                    reason='Role remains uncertain', unknownIds=['question'])
    return {**base, **changes}


def record(key, kind, owner='first', category=None):
    result = {'key': key, 'kind': kind, 'ownerRequirement': owner, 'version': SHA}
    if category:
        result['classification'] = classification(category)
    return result


class CatalogTests(unittest.TestCase):
    def setUp(self):
        self.obligations = {
            'first': {'id': 'first', 'stage': 'discovery', 'scope': 'scope-one'},
            'second': {'id': 'second', 'stage': 'discovery', 'scope': 'scope-one'},
            'other': {'id': 'other', 'stage': 'discovery', 'scope': 'scope-two'}}
        self.records = {
            'entry': record('entry', 'entry'), 'main': record('main', 'function', category='main'),
            'operation': record('operation', 'operation', 'second', 'operation'),
            'common': record('common', 'common', category='common')}

    def validate(self, records=None, **kwargs):
        catalog.validate_records(self.records if records is None else records, self.obligations, **kwargs)

    def task(self, records=None):
        return {'requirements': ['first', 'second', 'other'],
                'goalRequirements': list(self.obligations.values()),
                'classificationBindings': catalog.bindings(self.records if records is None else records)}

    def answer(self, task):
        return {'classificationChecks': [
                    {'key': item['key'], 'recordSha256': item['sha256'], 'status': 'pass',
                     'reason': 'Independently checked role', 'evidence': [EVIDENCE]}
                    for item in task['classificationBindings']],
                'scopeChecks': [{'scope': scope, 'status': 'pass', 'reason': 'Checked scope coverage',
                                 'evidence': [EVIDENCE]} for scope in catalog.scopes(task)]}

    def test_schema_requires_every_typed_field_and_rejects_extra_fields(self):
        for category in ('main', 'operation', 'common', 'pending'):
            value = classification(category)
            contracts.validate(value, catalog.CLASSIFICATION)
            for key in value:
                with self.subTest(category=category, missing=key), self.assertRaises(ValueError):
                    contracts.validate({k: v for k, v in value.items() if k != key}, catalog.CLASSIFICATION)
            with self.assertRaises(ValueError):
                contracts.validate({**value, 'unapproved': True}, catalog.CLASSIFICATION)

    def test_nonempty_fields_and_unique_refs_are_mechanical(self):
        for field in ('scope', 'purpose', 'rationale', 'alternative'):
            with self.subTest(field=field), self.assertRaises(ValueError):
                contracts.validate(classification('main', **{field: ''}), catalog.CLASSIFICATION)
        for field in ('actors', 'entryRefs'):
            for values in ([], ['entry', 'entry'], ['']):
                with self.subTest(field=field, values=values), self.assertRaises(ValueError):
                    contracts.validate(classification('main', **{field: values}), catalog.CLASSIFICATION)

    def test_strict_semantic_kinds_cannot_bypass_typing_with_null_or_missing(self):
        for kind in ('function', 'operation', 'common', 'unclassified'):
            for null in (False, True):
                value = record('candidate', kind)
                if null:
                    value['classification'] = None
                self.validate({'candidate': value})
                with self.subTest(kind=kind, null=null), self.assertRaises(ValueError):
                    self.validate({'candidate': value}, strict=True)

    def test_kind_and_category_must_match_and_nonsemantic_kinds_stay_untyped(self):
        for kind in ('function', 'operation', 'common', 'unclassified', 'entry', 'support', 'material', 'dependency'):
            value = record('candidate', kind, category='main')
            if kind == 'function':
                continue
            with self.subTest(kind=kind), self.assertRaises(ValueError):
                self.validate({'candidate': value})
        for kind in ('entry', 'support', 'material', 'dependency', 'data', 'system'):
            value = record('candidate', kind)
            value['classification'] = None
            self.validate({'candidate': value}, strict=True)

    def test_parent_can_cross_owner_and_share_entries_without_predefined_counts(self):
        self.validate(strict=True)
        self.assertEqual(['main', 'entry'], catalog.semantic_references(self.records['operation']))
        for index in range(3):
            key = 'another-operation-' + str(index)
            self.records[key] = record(key, 'operation', 'second', 'operation')
        self.validate(strict=True)
        del self.records['operation']
        self.records['common']['classification']['consumers'] = ['main']
        self.validate(strict=True)

    def test_operation_parent_missing_or_changed_kind_is_rejected(self):
        for change in ('missing', 'kind', 'classification'):
            with self.subTest(change=change):
                records = deepcopy(self.records)
                if change == 'missing':
                    del records['main']
                elif change == 'kind':
                    records['main'] = record('main', 'entry')
                else:
                    records['main']['classification'] = None
                with self.assertRaises(ValueError):
                    self.validate(records)

    def test_entry_refs_must_exist_and_be_entries(self):
        for target in ('missing', 'main'):
            records = deepcopy(self.records)
            records['main']['classification']['entryRefs'] = [target]
            with self.subTest(target=target), self.assertRaises(ValueError):
                self.validate(records)

    def test_semantic_references_and_own_classification_cannot_cross_scope(self):
        for target in ('entry', 'main', 'operation'):
            records = deepcopy(self.records)
            records[target]['ownerRequirement'] = 'other'
            if records[target].get('classification'):
                records[target]['classification']['scope'] = 'scope-two'
            with self.subTest(target=target), self.assertRaises(ValueError):
                self.validate(records)
        self.records['main']['classification']['scope'] = 'scope-two'
        with self.assertRaises(ValueError):
            self.validate()

    def test_common_consumers_cannot_be_self_missing_or_nonsemantic_material(self):
        self.records['material'] = record('material', 'material')
        for target in ('common', 'missing', 'material'):
            self.records['common']['classification']['consumers'] = [target]
            with self.subTest(target=target), self.assertRaises(ValueError):
                self.validate()
        self.records['common']['classification']['consumers'] = ['entry']
        self.validate()

    def test_pending_requires_existing_unknown_but_is_saved_before_acceptance(self):
        self.records['pending'] = record('pending', 'unclassified', category='pending')
        self.validate(strict=True)
        self.validate(strict=True, unknown_ids={'question'})
        with self.assertRaises(ValueError):
            self.validate(unknown_ids=set())
        task = self.task()
        answer = self.answer(task)
        catalog.validate_checks(answer, task, Source())
        with self.assertRaises(ValueError):
            catalog.require_resolved({'records': self.records}, answer)
        self.records['pending']['classification']['impact'] = 'outside-obligation'
        catalog.require_resolved({'records': self.records}, answer)

    def test_bindings_only_include_typed_semantic_records_with_exact_versions(self):
        result = catalog.bindings(self.records)
        self.assertEqual(['main', 'operation', 'common'], [item['key'] for item in result])
        self.assertEqual({'key': 'main', 'sha256': SHA, 'category': 'main', 'scope': 'scope-one'}, result[0])
        self.assertEqual([], catalog.semantic_references(self.records['entry']))

    def test_scopes_preserve_goal_order_and_include_zero_record_obligations(self):
        task = self.task({})
        self.assertEqual(['scope-one', 'scope-two'], catalog.scopes(task))
        answer = self.answer(task)
        self.assertEqual([], answer['classificationChecks'])
        catalog.validate_checks(answer, task, Source())
        answer['scopeChecks'].pop()
        with self.assertRaises(ValueError):
            catalog.validate_checks(answer, task, Source())

    def test_checks_bind_every_hash_and_scope_once_and_verify_all_evidence(self):
        task = self.task()
        source = Source()
        catalog.validate_checks(self.answer(task), task, source)
        self.assertEqual(5, len(source.seen))
        for mutation in ('hash', 'key', 'duplicate-record', 'scope', 'duplicate-scope',
                         'missing-checks', 'no-evidence', 'bad-evidence'):
            answer = self.answer(task)
            if mutation == 'hash':
                answer['classificationChecks'][0]['recordSha256'] = 'b' * 64
            elif mutation == 'key':
                answer['classificationChecks'][0]['key'] = 'invented'
            elif mutation == 'duplicate-record':
                answer['classificationChecks'][1] = deepcopy(answer['classificationChecks'][0])
            elif mutation == 'scope':
                answer['scopeChecks'][0]['scope'] = 'invented'
            elif mutation == 'duplicate-scope':
                answer['scopeChecks'][1] = deepcopy(answer['scopeChecks'][0])
            elif mutation == 'missing-checks':
                del answer['scopeChecks']
            elif mutation == 'no-evidence':
                answer['scopeChecks'][0]['evidence'] = []
            else:
                answer['classificationChecks'][0]['status'] = 'fail'
                answer['classificationChecks'][0]['evidence'] = [{**EVIDENCE, 'path': 'unsealed.cs'}]
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                catalog.validate_checks(answer, task, Source())

    def test_acceptance_requires_all_classification_and_scope_checks_to_pass(self):
        task = self.task()
        answer = self.answer(task)
        catalog.require_resolved({'records': self.records}, answer)
        for field in ('classificationChecks', 'scopeChecks'):
            for status in ('fail', 'unknown'):
                answer = self.answer(task)
                answer[field][0]['status'] = status
                with self.subTest(field=field, status=status), self.assertRaises(ValueError):
                    catalog.require_resolved({'records': self.records}, answer)


if __name__ == '__main__':
    unittest.main()

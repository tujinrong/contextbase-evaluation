"""Review versions are paired identities, distinct from pageable material hashes."""
from copy import deepcopy
import unittest

from jsonschema import Draft202012Validator

from contextbase_runtime import catalog, contracts as c, incremental, review_set
from test_review_set import answer, fixture


def prepared():
    task, view = fixture(records=4, unknowns=2)
    row = view['records']['object-2']
    row['kind'] = 'common'
    row['classification'] = deepcopy(view['records']['object-1']['classification'])
    row['version'] = c.digest({key: value for key, value in row.items() if key not in {'id', 'version'}})
    task['classificationBindings'] = catalog.bindings(view['records'])
    task['viewSha256'] = c.digest(view)
    units = review_set.make_units(task, view)
    return task, view, units


class ReviewVersionBindingTests(unittest.TestCase):
    def test_record_material_hash_is_rejected_by_the_wire_schema_itself(self):
        task, view, units = prepared()
        unit = next(row for row in units if len(row['recordKeys']) >= 2)
        result = answer(task, view, unit)
        schema = review_set.unit_schema(task, view, unit)
        c.validate(result, schema)
        key = result['recordChecks'][0]['key']
        material_sha = c.digest(view['records'][key])
        self.assertNotEqual(view['records'][key]['version'], material_sha)
        result['recordChecks'][0]['recordSha256'] = material_sha
        with self.assertRaises(ValueError):
            c.validate(result, schema)

    def test_other_valid_record_version_cannot_be_paired_with_this_key(self):
        task, view, units = prepared()
        unit = next(row for row in units if len(row['recordKeys']) >= 2)
        result = answer(task, view, unit)
        result['recordChecks'][0]['recordSha256'] = result['recordChecks'][1]['recordSha256']
        with self.assertRaises(ValueError):
            c.validate(result, review_set.unit_schema(task, view, unit))

    def test_record_schema_branches_expose_the_exact_expected_key_version_pairs(self):
        task, view, units = prepared()
        unit = next(row for row in units if row['recordKeys'])
        item_schema = review_set.unit_schema(task, view, unit)['properties']['recordChecks']['items']
        pairs = {(branch['properties']['key']['const'], branch['properties']['recordSha256']['const'])
                 for branch in item_schema['anyOf']}
        self.assertEqual({(key, view['records'][key]['version']) for key in unit['recordKeys']}, pairs)

    def test_classification_material_or_other_record_hash_is_rejected_before_host_validation(self):
        task, view, units = prepared()
        unit = next(row for row in units if len(row['recordKeys']) >= 2)
        for replacement in ('material', 'other-classification'):
            with self.subTest(replacement=replacement):
                result = answer(task, view, unit)
                key = result['classificationChecks'][0]['key']
                result['classificationChecks'][0]['recordSha256'] = (
                    c.digest(view['records'][key]) if replacement == 'material'
                    else result['classificationChecks'][1]['recordSha256'])
                with self.assertRaises(ValueError):
                    c.validate(result, review_set.unit_schema(task, view, unit))

    def test_unknown_material_or_another_question_hash_is_rejected_by_schema(self):
        task, view, units = prepared()
        unit = next(row for row in units if len(row['unknownIds']) >= 2)
        for replacement in ('material', 'other-question'):
            with self.subTest(replacement=replacement):
                result = answer(task, view, unit)
                key = result['unknownChecks'][0]['unknownId']
                result['unknownChecks'][0]['unknownSha256'] = (
                    c.digest(view['unknowns'][key]) if replacement == 'material'
                    else result['unknownChecks'][1]['unknownSha256'])
                with self.assertRaises(ValueError):
                    c.validate(result, review_set.unit_schema(task, view, unit))

    def test_correct_record_classification_unknown_pairs_and_zero_target_global_schema_are_valid(self):
        task, view, units = prepared()
        for unit in units:
            with self.subTest(unit=unit['id']):
                schema = review_set.unit_schema(task, view, unit)
                Draft202012Validator.check_schema(schema)
                c.validate(answer(task, view, unit), schema)
                review_set.validate_unit(task, view, unit, answer(task, view, unit))
                if unit['kind'] == 'global':
                    self.assertEqual([], unit['recordKeys'])
                    self.assertEqual([], unit['unknownIds'])

    def context(self, task, view, unit):
        context = {'request': {'goal': {'requirements': task['goalRequirements']}},
                   'inventory': {'files': [], 'omitted': []}, 'structure': {}}
        child = {**deepcopy(task), 'rootTaskId': task['id']}
        materials = incremental._collections(view['records'], view['unknowns'], (), [unit])
        return incremental._base_context(context, child, 'review', unit, materials)

    def test_small_review_context_has_material_and_expected_record_classification_versions(self):
        task, view, units = prepared()
        unit = next(row for row in units if row['recordKeys'])
        context = self.context(task, view, unit)
        bindings = context['reviewBindings']
        records = {row['key']: row for row in bindings['records']}
        classified = {row['key']: row for row in bindings['classifications']}
        for key in unit['recordKeys']:
            self.assertEqual(c.digest(view['records'][key]), records[key]['materialSha256'])
            self.assertEqual(view['records'][key]['version'], records[key]['recordSha256'])
        for binding in task['classificationBindings']:
            if binding['key'] in unit['recordKeys']:
                self.assertEqual(binding['sha256'], classified[binding['key']]['recordSha256'])
                self.assertEqual(c.digest(view['records'][binding['key']]),
                                 classified[binding['key']]['materialSha256'])

    def test_large_record_reference_and_binding_both_expose_expected_review_version(self):
        task, view, _ = prepared()
        record = view['records']['object-0']
        record['statement'] = 'large candidate claim ' * 2000
        record['version'] = c.digest({key: value for key, value in record.items() if key not in {'id', 'version'}})
        task['viewSha256'] = c.digest(view)
        unit = next(row for row in review_set.make_units(task, view) if 'object-0' in row['recordKeys'])
        context = self.context(task, view, unit)
        reference = context['reviewTargets']['records']['object-0']
        self.assertNotIn('statement', reference)
        self.assertEqual(record['version'], reference['recordSha256'])
        self.assertEqual(c.digest(record), reference['materialSha256'])
        binding = next(row for row in context['reviewBindings']['records'] if row['key'] == 'object-0')
        self.assertEqual(record['version'], binding['recordSha256'])

    def test_small_and_large_unknowns_have_content_version_separate_from_material_digest(self):
        for large in (False, True):
            with self.subTest(large=large):
                task, view, _ = prepared()
                question = view['unknowns']['u-0']
                if large:
                    question['content']['question'] = 'large unresolved question ' * 2000
                    question['sha256'] = c.digest(question['content'])
                    task['unknownBindings'] = [{'id': key, 'sha256': row['sha256']}
                                               for key, row in view['unknowns'].items()]
                    task['viewSha256'] = c.digest(view)
                unit = next(row for row in review_set.make_units(task, view) if 'u-0' in row['unknownIds'])
                context = self.context(task, view, unit)
                binding = next(row for row in context['reviewBindings']['unknowns'] if row['unknownId'] == 'u-0')
                self.assertEqual(question['sha256'], binding['unknownSha256'])
                self.assertEqual(c.digest(question), binding['materialSha256'])
                if large:
                    reference = context['reviewTargets']['unknowns']['u-0']
                    self.assertEqual(question['sha256'], reference['unknownSha256'])
                    self.assertEqual(c.digest(question), reference['materialSha256'])

    def test_author_phases_do_not_acquire_review_binding_metadata(self):
        task, view, units = prepared()
        context = {'request': {'goal': {'requirements': task['goalRequirements']}},
                   'inventory': {'files': [], 'omitted': []}, 'structure': {}}
        materials = incremental._collections()
        for phase in ('plan', 'draft', 'closure'):
            with self.subTest(phase=phase):
                base = incremental._base_context(context, {**task, 'rootTaskId': task['id']}, phase, {}, materials)
                self.assertNotIn('reviewBindings', base)

    def test_pair_const_schema_still_requires_reviewer_status_reason_and_source_evidence(self):
        task, view, units = prepared()
        unit = next(row for row in units if row['recordKeys'])
        result = answer(task, view, unit)
        result['recordChecks'][0].pop('status')
        with self.assertRaises(ValueError):
            c.validate(result, review_set.unit_schema(task, view, unit))
        result = answer(task, view, unit)
        result['recordChecks'][0]['evidence'] = []
        with self.assertRaises(ValueError):
            review_set.validate_unit(task, view, unit, result)


if __name__ == '__main__':
    unittest.main()

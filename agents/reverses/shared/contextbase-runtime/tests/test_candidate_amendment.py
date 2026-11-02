"""Pure amendment seams; fixtures carry no model or store authority."""
from copy import deepcopy
import unittest

from contextbase_runtime import catalog, contracts, candidate_amendment as amendment


def evidence():
    return {'path': 'A.cs', 'startLine': 1, 'endLine': 2, 'sha256': 'a' * 64}


def record(key='entry', kind='entry', owner='catalog'):
    return {'key': key, 'kind': kind, 'ownerRequirement': owner, 'name': key,
            'statement': 'Observed source responsibility.', 'basis': 'observed-source',
            'evidence': [evidence()], 'dependsOn': [], 'classification': None}


def fixture():
    task = {'id': 'new-author', 'operation': 'extract', 'stage': 'discovery',
            'amendmentOperationId': '2' * 64,
            'origin': 'host-executed', 'requirements': ['catalog'],
            'goalRequirementIds': ['catalog', 'relationships'], 'goalRequirements': [
                {'id': 'catalog', 'stage': 'discovery', 'question': 'Catalog?',
                 'scope': 'system', 'requires': []},
                {'id': 'relationships', 'stage': 'relationship', 'question': 'Relations?',
                 'scope': 'system', 'requires': ['catalog']}],
            'snapshotId': 'b' * 64, 'sourceFactsSha256': 'c' * 64,
            'authorizedSourcePaths': ['A.cs'], 'catalogPolicy': catalog.VERSION,
            'recordKinds': ['entry', 'material']}
    base = record()
    body = {**base, 'dependencies': []}
    frozen = {**body, 'id': 'ENTRY-stable', 'version': contracts.digest(body)}
    unknown = {'id': 'q', 'question': 'Which configuration?',
               'relatedRequirements': ['relationships'], 'blocksRequirements': ['relationships'],
               'scopeReason': 'A future relationship question.'}
    followup = {'stage': 'relationship', 'question': 'Check relations.',
                'paths': ['A.cs'], 'requirement': 'relationships'}
    answer = {'taskId': 'old-author', 'records': [base], 'coverage': [],
              'unknowns': [unknown], 'followups': [], 'sourceFactsSha256': 'c' * 64,
              'factUsage': [{'recordKey': 'entry', 'factIds': ['old-fact'], 'reason': 'Source.'}]}
    view = {'records': {'entry': frozen}, 'unknowns': {}, 'acceptedRequirements': ['catalog'],
            'invalidatedRequirements': [], 'contentHashes': {}}
    issue = {'id': 'missing-material', 'sourceCandidateSha256': 'd' * 64,
             'sourceVerificationSha256': 'e' * 64, 'finding': {
                 'id': 'finding-1', 'severity': 'blocking', 'requirement': 'catalog',
                 'detail': 'Inspect source material.', 'evidence': [evidence()]}}
    issue['sha256'] = contracts.digest(issue)
    seed = {'schema': 'contextbase-candidate-amendment-seed/1',
            'requestSha256': 'f' * 64, 'snapshotId': task['snapshotId'],
            'indexSha256': task['sourceFactsSha256'], 'stage': 'discovery',
            'requirements': ['catalog'], 'baseCandidateSha256': '1' * 64,
            'baseViewSha256': contracts.digest(view), 'answer': answer, 'view': view,
            'followups': [followup], 'issues': [issue], 'custody': {'checked': True}}
    spec = {'schema': amendment.VERSION, 'seedSha256': contracts.digest(seed),
            'replaceKeys': ['entry'], 'addKinds': ['material']}
    patch = {'operationId': task['amendmentOperationId'], 'seedSha256': contracts.digest(seed),
             'baseCandidateSha256': seed['baseCandidateSha256'], 'changes': [],
             'unknowns': [], 'followups': [], 'factUsage': [], 'dispositions': [{
                 'issueId': issue['id'], 'issueSha256': issue['sha256'],
                 'status': 'source-refuted', 'recordKeys': ['entry'],
                 'currentRecordRefs': [{'key': 'entry', 'sha256': frozen['version']}],
                 'evidence': [evidence()], 'reason': 'The original source refutes this concern.',
                 'relatedRequirements': ['catalog'], 'blocksRequirements': []}]}
    return seed, task, spec, patch


class CandidateAmendmentTests(unittest.TestCase):
    def test_native_v2_joint_replacement_only_and_v1_isolation(self):
        seed, task, spec, patch = fixture()
        task['requirements'] = [row['id'] for row in task['goalRequirements']]
        task.update(stage=None, jointPolicy=contracts.JOINT_POLICY,
                    nativeToolsPolicy='contextbase-native-tools/1', executionScope=task['requirements'])
        seed.update(schema=amendment.NATIVE_SEED_VERSION, stage=None,
                    jointPolicy=contracts.JOINT_POLICY, nativeToolsPolicy='contextbase-native-tools/1',
                    requirements=list(task['requirements']))
        spec.update(schema=amendment.NATIVE_VERSION, seedSha256=contracts.digest(seed), addKinds=[])
        amendment.validate_spec(seed, task, spec)
        for changes in ({'addKinds': ['material']}, {'replaceKeys': []}, {'schema': amendment.VERSION}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                amendment.validate_spec(seed, task, {**spec, **changes})
        with self.assertRaises(ValueError):
            amendment.validate_spec(seed, {**task, 'nativeToolsPolicy': None}, spec)
        old_seed, _, old_spec, _ = fixture()
        with self.assertRaises(ValueError):
            amendment.validate_spec(old_seed, task, old_spec)

    def test_empty_delta_preserves_base_without_mutating_input(self):
        seed, task, spec, patch = fixture()
        before = deepcopy(seed)
        result = amendment.apply_patch(seed, task, spec, patch)
        self.assertEqual(seed['answer']['records'], result['records'])
        self.assertEqual(seed['answer']['unknowns'], result['unknowns'])
        self.assertEqual(seed['followups'], result['followups'])
        self.assertEqual(seed['answer']['factUsage'], result['factUsage'])
        self.assertEqual(before, seed)

    def test_addition_preserves_unchanged_record_and_fact_usage_versions(self):
        seed, task, spec, patch = fixture()
        original_record = deepcopy(seed['answer']['records'][0])
        original_version = seed['view']['records']['entry']['version']
        patch['changes'] = [{'key': 'readme', 'expectedVersion': None,
                             'record': record('readme', 'material')}]
        patch['factUsage'] = [{'recordKey': 'readme', 'factIds': [],
                               'reason': 'Documentation has no syntax facts.'}]
        patch['dispositions'][0].update(status='changed', recordKeys=['readme'], currentRecordRefs=[])
        result = amendment.apply_patch(seed, task, spec, patch)
        self.assertEqual(original_record, result['records'][0])
        self.assertEqual(seed['answer']['factUsage'][0], result['factUsage'][0])
        self.assertEqual(original_version, seed['view']['records']['entry']['version'])
        result['records'][0]['statement'] = 'Mutated output.'
        self.assertEqual(original_record, seed['answer']['records'][0])

    def test_schema_is_explicit_strict_and_patch_bindings_are_enforced(self):
        seed, task, spec, patch = fixture()
        schema = amendment.response_schema(seed, task, spec)
        contracts.validate(patch, schema)
        for changed in [{**patch, 'operationId': '0' * 64},
                        {**patch, 'taskId': 'old-author'},
                        {**patch, 'seedSha256': '0' * 64},
                        {**patch, 'baseCandidateSha256': '0' * 64},
                        {**patch, 'records': []}]:
            with self.subTest(changed=changed), self.assertRaises(ValueError):
                amendment.apply_patch(seed, task, spec, changed)
        missing = deepcopy(patch)
        del missing['dispositions'][0]['currentRecordRefs']
        with self.assertRaises(ValueError):
            amendment.apply_patch(seed, task, spec, missing)

    def test_pending_base_retains_raw_unknown_ids_for_parent_materialization(self):
        seed, task, spec, patch = fixture()
        pending = {**record(), 'kind': 'unclassified', 'classification': {
            'category': 'pending', 'scope': 'system', 'tentativeKind': 'entry',
            'impact': 'outside-obligation', 'reason': 'Future detail.', 'unknownIds': ['q']}}
        seed['answer']['unknowns'][0].update(relatedRequirements=['catalog'], blocksRequirements=[])
        seed['answer']['records'] = [pending]
        frozen_body = {**deepcopy(pending), 'dependencies': []}
        frozen_body['classification']['unknownIds'] = ['old-author:q']
        seed['view']['records']['entry'] = {**frozen_body, 'id': 'UNCLASSIFIED-stable',
                                            'version': contracts.digest(frozen_body)}
        seed['baseViewSha256'] = contracts.digest(seed['view'])
        spec['seedSha256'] = contracts.digest(seed)
        patch['seedSha256'] = spec['seedSha256']
        patch['dispositions'][0]['currentRecordRefs'][0]['sha256'] = seed['view']['records']['entry']['version']
        task['recordKinds'].append('unclassified')
        result = amendment.apply_patch(seed, task, spec, patch)
        self.assertEqual(['q'], result['records'][0]['classification']['unknownIds'])

    def test_scope_and_content_bindings_cannot_be_substituted(self):
        seed, task, spec, patch = fixture()
        amendment.validate_spec(seed, task, spec)
        variants = [({**spec, 'seedSha256': '0' * 64}, task),
                    ({**spec, 'replaceKeys': ['absent']}, task),
                    ({**spec, 'replaceKeys': ['entry', 'entry']}, task),
                    ({**spec, 'addKinds': ['common']}, task),
                    (spec, {**task, 'requirements': ['relationships']}),
                    (spec, {**task, 'snapshotId': '0' * 64}),
                    (spec, {**task, 'sourceFactsSha256': '0' * 64}),
                    (spec, {**task, 'operation': 'verify'})]
        for changed_spec, changed_task in variants:
            with self.subTest(spec=changed_spec, task=changed_task), self.assertRaises(ValueError):
                amendment.validate_spec(seed, changed_task, changed_spec)
        broken = deepcopy(seed)
        broken['issues'][0]['finding']['detail'] = 'Tampered finding.'
        with self.assertRaises(ValueError):
            amendment.validate_spec(broken, task, {**spec, 'seedSha256': contracts.digest(broken)})

    def test_explicit_replace_and_add_preserve_untouched_usage(self):
        seed, task, spec, patch = fixture()
        revised = {**record(), 'statement': 'Corrected from the source.'}
        patch['changes'] = [{'key': 'entry', 'expectedVersion': seed['view']['records']['entry']['version'],
                             'record': revised},
                            {'key': 'readme', 'expectedVersion': None,
                             'record': record('readme', 'material')}]
        patch['factUsage'] = [{'recordKey': key, 'factIds': ['new-fact'], 'reason': 'Source.'}
                              for key in ['entry', 'readme']]
        patch['dispositions'][0].update(status='changed', recordKeys=['readme'], currentRecordRefs=[])
        result = amendment.apply_patch(seed, task, spec, patch)
        self.assertEqual(['entry', 'readme'], [row['key'] for row in result['records']])
        self.assertEqual('Corrected from the source.', result['records'][0]['statement'])
        self.assertEqual(patch['factUsage'], result['factUsage'])
        for change in [
                {'key': 'entry', 'expectedVersion': '0' * 64, 'record': revised},
                {'key': 'entry', 'expectedVersion': None, 'record': revised},
                {'key': 'entry', 'expectedVersion': seed['view']['records']['entry']['version'],
                 'record': {**revised, 'ownerRequirement': 'relationships'}},
                {'key': 'entry', 'expectedVersion': seed['view']['records']['entry']['version'],
                 'record': {**revised, 'kind': 'material'}},
                {'key': 'readme', 'expectedVersion': None, 'record': record('other', 'material')},
                {'key': 'new-entry', 'expectedVersion': None, 'record': record('new-entry')}]:
            invalid = {**patch, 'changes': [change]}
            with self.subTest(change=change), self.assertRaises(ValueError):
                amendment.apply_patch(seed, task, spec, invalid)
        for field, value in [('changes', [patch['changes'][0], patch['changes'][0]]),
                             ('removals', ['entry']), ('factUsage', [])]:
            with self.subTest(field=field), self.assertRaises(ValueError):
                amendment.apply_patch(seed, task, spec, {**patch, field: value})

    def test_each_frozen_issue_requires_a_bound_supported_disposition(self):
        seed, task, spec, patch = fixture()
        disposition = patch['dispositions'][0]
        bindings = amendment.issue_bindings(seed, patch)
        self.assertEqual([{'id': 'missing-material', 'sha256': seed['issues'][0]['sha256'],
                           'dispositionSha256': contracts.digest(disposition), 'requirement': 'catalog'}],
                         bindings)
        bad_dispositions = [[], [disposition, disposition],
            [{**disposition, 'issueId': 'other'}], [{**disposition, 'issueSha256': '0' * 64}],
            [{**disposition, 'status': 'changed'}], [{**disposition, 'evidence': []}],
            [{**disposition, 'currentRecordRefs': []}],
            [{**disposition, 'currentRecordRefs': [{'key': 'entry', 'sha256': '0' * 64}]}],
            [{**disposition, 'blocksRequirements': ['relationships']}],
            [{**disposition, 'status': 'unresolved', 'blocksRequirements': ['catalog'],
              'relatedRequirements': ['relationships']}]]
        for rows in bad_dispositions:
            with self.subTest(rows=rows), self.assertRaises(ValueError):
                amendment.apply_patch(seed, task, spec, {**patch, 'dispositions': rows})
        future = {**disposition, 'status': 'unresolved', 'recordKeys': [], 'currentRecordRefs': [],
                  'evidence': [], 'relatedRequirements': ['relationships'], 'blocksRequirements': []}
        amendment.apply_patch(seed, task, spec, {**patch, 'dispositions': [future]})

    def test_unknowns_and_followups_are_append_only_with_conflicts_rejected(self):
        seed, task, spec, patch = fixture()
        extra = {**seed['answer']['unknowns'][0], 'id': 'new-question',
                 'question': 'Additional source question.'}
        followup = {**seed['followups'][0], 'question': 'Additional investigation.'}
        patch['unknowns'] = [seed['answer']['unknowns'][0], extra]
        patch['followups'] = [seed['followups'][0], followup]
        result = amendment.apply_patch(seed, task, spec, patch)
        self.assertEqual(['q', 'new-question'], [row['id'] for row in result['unknowns']])
        self.assertEqual(['Check relations.', 'Additional investigation.'],
                         [row['question'] for row in result['followups']])
        for rows in [[{**extra, 'id': 'q'}], [extra, extra],
                     [{**extra, 'relatedRequirements': ['relationships'], 'blocksRequirements': ['catalog']}]]:
            with self.subTest(rows=rows), self.assertRaises(ValueError):
                amendment.apply_patch(seed, task, spec, {**patch, 'unknowns': rows})

    def test_full_answer_requires_new_explicit_closures_and_rebinds_coverage(self):
        seed, task, spec, patch = fixture()
        closure = {'requirement': 'catalog', 'status': 'unresolved',
                   'reason': 'Further independent review is required.', 'evidence': []}
        for closures in [[], [closure, closure], [{**closure, 'requirement': 'relationships'}],
                         [{**closure, 'status': 'supported'}]]:
            with self.subTest(closures=closures), self.assertRaises(ValueError):
                amendment.canonical_answer(seed, task, spec, patch, closures)
        result = amendment.canonical_answer(seed, task, spec, patch, [closure])
        contracts.validate(result, contracts.result_schema(task))
        self.assertEqual('new-author', result['taskId'])
        self.assertEqual([{'requirement': 'catalog', 'status': 'unresolved',
                           'recordKeys': ['entry'], 'evidence': []}], result['coverage'])
        self.assertEqual(seed['answer']['unknowns'], result['unknowns'])
        self.assertEqual(seed['answer']['factUsage'], result['factUsage'])
        self.assertEqual(seed['followups'], result['followups'])

    def test_same_operation_reuses_frozen_delta_across_new_root_task_identity(self):
        seed, task, spec, patch = fixture()
        resumed = {**task, 'id': 'resumed-author'}
        before = deepcopy(patch)
        self.assertEqual(amendment.response_schema(seed, task, spec),
                         amendment.response_schema(seed, resumed, spec))
        self.assertEqual(amendment.apply_patch(seed, task, spec, patch),
                         amendment.apply_patch(seed, resumed, spec, patch))
        closure = {'requirement': 'catalog', 'status': 'unresolved',
                   'reason': 'Fresh independent review is still required.', 'evidence': []}
        answer = amendment.canonical_answer(seed, resumed, spec, patch, [closure])
        self.assertEqual('resumed-author', answer['taskId'])
        self.assertEqual(before, patch)
        for invalid in [{key: value for key, value in resumed.items() if key != 'amendmentOperationId'},
                        {**resumed, 'amendmentOperationId': '3' * 64}]:
            with self.subTest(task=invalid), self.assertRaises(ValueError):
                amendment.apply_patch(seed, invalid, spec, patch)


if __name__ == '__main__':
    unittest.main()

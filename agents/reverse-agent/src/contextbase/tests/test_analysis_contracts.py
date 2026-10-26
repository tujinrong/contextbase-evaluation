"""Pure v2 contract tests; no model, input-program execution, or project data."""
from copy import deepcopy
import json
import unittest

from jsonschema import Draft202012Validator

from contextbase.analysis import contracts


EVIDENCE = {'path': 'Orders.cs', 'startLine': 1, 'endLine': 2, 'sha256': 'b' * 64}


class Sources:
    paths = ['Orders.cs']

    def verify_evidence(self, evidence):
        if evidence != EVIDENCE:
            raise ValueError('Evidence does not match sealed source')


def obligation(identifier, stage, requires=(), scope='orders'):
    return {'id': identifier, 'question': 'Check ' + identifier, 'stage': stage,
            'scope': scope, 'requires': list(requires)}


class ContractTests(unittest.TestCase):
    def setUp(self):
        self.request = {'schema': contracts.VERSION, 'projectId': 'synthetic',
            'goal': {'id': 'orders', 'question': 'Understand the selected orders flow.',
                'requirements': [obligation('catalog', 'discovery'),
                    obligation('relation', 'relationship', ['catalog']),
                    obligation('behavior', 'behavior', ['relation'])]},
            'allowedPaths': ['Orders.cs'], 'excludedPaths': []}
        self.task = {'id': 'author-task', 'operation': 'extract', 'stage': 'discovery',
            'candidate': None, 'viewSha256': None, 'requirements': ['catalog'],
            'goalRequirementIds': ['catalog', 'relation', 'behavior'],
            'goalRequirements': deepcopy(self.request['goal']['requirements']),
            'unknownBindings': []}
        self.answer = {'taskId': 'author-task', 'records': [
            {'key': 'orders', 'ownerRequirement': 'catalog', 'kind': 'function',
             'name': 'Orders', 'statement': 'The selected source declares the order entry.',
             'basis': 'observed-source', 'evidence': [deepcopy(EVIDENCE)], 'dependsOn': []}],
            'coverage': [{'requirement': 'catalog', 'status': 'supported', 'recordKeys': ['orders'],
                          'evidence': [deepcopy(EVIDENCE)]}], 'unknowns': [], 'followups': []}
        self.source = Sources()

    def check(self, answer=None, task=None, existing=()):
        contracts.validate_result(self.answer if answer is None else answer,
                                  self.task if task is None else task, self.source, existing)

    def unknown(self, identifier='missing-definition'):
        return {'id': identifier, 'question': 'The deployment definition is not in scope.',
                'relatedRequirements': ['catalog'], 'blocksRequirements': [],
                'scopeReason': 'The goal asks for source candidates rather than deployment proof.'}

    def verification(self, bindings=None):
        task = deepcopy(self.task)
        task.update(id='verification-task', operation='verify', candidate='c' * 64,
                    viewSha256='d' * 64,
                    unknownBindings=[] if bindings is None else bindings)
        answer = {'taskId': task['id'], 'candidateSha256': task['candidate'],
            'viewSha256': task['viewSha256'],
            'checks': [{'requirement': 'catalog', 'status': 'pass', 'reason': 'Checked original source.',
                        'evidence': [deepcopy(EVIDENCE)]}], 'unknownChecks': [], 'findings': [], 'unknowns': []}
        for binding in task['unknownBindings']:
            answer['unknownChecks'].append({'unknownId': binding['id'], 'unknownSha256': binding['sha256'],
                'status': 'non-blocking', 'blocksRequirements': [], 'reason': 'Outside the original goal.',
                'evidence': [deepcopy(EVIDENCE)]})
        return task, answer

    def test_valid_three_stage_request(self):
        contracts.validate_request(self.request)
        self.assertEqual(('discovery', 'relationship', 'behavior'), contracts.STAGES)
        self.assertEqual(('extract', 'verify'), contracts.OPERATIONS)

    def test_catalog_only_goal_is_valid(self):
        self.request['goal']['requirements'] = self.request['goal']['requirements'][:1]
        contracts.validate_request(self.request)

    def test_old_or_unversioned_requests_require_explicit_migration(self):
        for version in (None, 'contextbase-analysis/1'):
            request = deepcopy(self.request)
            if version is None:
                del request['schema']
            else:
                request['schema'] = version
            with self.assertRaisesRegex(ValueError, 'not automatically migrated'):
                contracts.validate_request(request)

    def test_relationship_cannot_skip_its_catalog(self):
        self.request['goal']['requirements'][1]['requires'] = []
        with self.assertRaisesRegex(ValueError, 'required discovery'):
            contracts.validate_request(self.request)

    def test_behavior_cannot_use_catalog_instead_of_relationship(self):
        self.request['goal']['requirements'][2]['requires'] = ['catalog']
        with self.assertRaisesRegex(ValueError, 'existing relationship'):
            contracts.validate_request(self.request)

    def test_another_scope_does_not_satisfy_prerequisite(self):
        self.request['goal']['requirements'][2]['scope'] = 'payments'
        with self.assertRaisesRegex(ValueError, 'same scope'):
            contracts.validate_request(self.request)

    def test_missing_prerequisite_is_rejected(self):
        self.request['goal']['requirements'][1]['requires'] = ['missing']
        with self.assertRaisesRegex(ValueError, 'existing discovery'):
            contracts.validate_request(self.request)

    def test_discovery_cannot_have_a_prerequisite(self):
        self.request['goal']['requirements'][0]['requires'] = ['behavior']
        with self.assertRaisesRegex(ValueError, 'do not have prerequisite'):
            contracts.validate_request(self.request)

    def test_duplicate_requirement_identity_is_rejected(self):
        self.request['goal']['requirements'].append(deepcopy(self.request['goal']['requirements'][0]))
        with self.assertRaisesRegex(ValueError, 'IDs must be unique'):
            contracts.validate_request(self.request)

    def test_old_investigation_stage_is_not_silently_remapped(self):
        self.request['goal']['requirements'][1]['stage'] = 'investigation'
        with self.assertRaisesRegex(ValueError, 'contract'):
            contracts.validate_request(self.request)

    def test_goal_must_include_discovery(self):
        self.request['goal']['requirements'] = self.request['goal']['requirements'][1:]
        with self.assertRaisesRegex(ValueError, 'explicit discovery'):
            contracts.validate_request(self.request)

    def test_valid_extraction_has_an_owner_and_exact_coverage(self):
        self.check()
        self.answer['records'][0]['kind'] = 'fact'
        self.check()  # A stage's source-reading responsibility is not a kind prohibition.

    def test_owner_must_be_assigned_to_the_task(self):
        self.answer['records'][0]['ownerRequirement'] = 'relation'
        with self.assertRaisesRegex(ValueError, 'contract'):
            self.check()

    def test_record_cannot_be_hidden_outside_its_owner_coverage(self):
        self.answer['coverage'][0]['recordKeys'] = []
        with self.assertRaisesRegex(ValueError, 'owner coverage'):
            self.check()

    def test_duplicate_record_identity_is_rejected(self):
        self.answer['records'].append(deepcopy(self.answer['records'][0]))
        with self.assertRaisesRegex(ValueError, 'Duplicate record'):
            self.check()

    def test_dependencies_can_reference_frozen_existing_records(self):
        self.answer['records'][0]['dependsOn'] = ['entry']
        self.check(existing={'entry': {'version': 'f' * 64}})
        with self.assertRaisesRegex(ValueError, 'Unknown record dependency'):
            self.check()

    def test_coverage_cannot_claim_an_unassigned_goal_obligation(self):
        self.answer['coverage'][0]['requirement'] = 'behavior'
        with self.assertRaisesRegex(ValueError, 'contract'):
            self.check()

    def test_positive_coverage_needs_sealed_source_evidence(self):
        self.answer['coverage'][0]['evidence'] = []
        with self.assertRaisesRegex(ValueError, 'positive conclusion'):
            self.check()

    def test_evidence_is_checked_against_the_source(self):
        self.answer['records'][0]['evidence'][0]['sha256'] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'sealed source'):
            self.check()

    def test_unknown_association_does_not_itself_mean_blocking(self):
        self.answer['unknowns'] = [self.unknown()]
        self.check()
        self.answer['unknowns'][0]['blocksRequirements'] = ['catalog']
        self.check()  # The host will apply adoption policy after independent verification.

    def test_unknown_blocking_must_be_among_related_goal_obligations(self):
        self.answer['unknowns'] = [self.unknown()]
        self.answer['unknowns'][0]['blocksRequirements'] = ['behavior']
        with self.assertRaisesRegex(ValueError, 'among its related'):
            self.check()

    def test_unknown_cannot_invent_goal_obligations(self):
        self.answer['unknowns'] = [self.unknown()]
        self.answer['unknowns'][0]['relatedRequirements'] = ['invented']
        with self.assertRaisesRegex(ValueError, 'original goal'):
            self.check()

    def test_unknown_has_a_unique_identity_and_scope_reason(self):
        self.answer['unknowns'] = [self.unknown(), self.unknown()]
        with self.assertRaisesRegex(ValueError, 'Duplicate unknown'):
            self.check()
        self.answer['unknowns'] = [self.unknown()]
        self.answer['unknowns'][0]['scopeReason'] = ''
        with self.assertRaisesRegex(ValueError, 'contract'):
            self.check()

    def test_followup_targets_explicit_original_stage_and_scope(self):
        self.answer['followups'] = [{'stage': 'relationship', 'question': 'Trace the handler.',
                                    'paths': ['Orders.cs'], 'requirement': 'relation'}]
        self.check()
        self.answer['followups'][0]['stage'] = 'behavior'
        with self.assertRaisesRegex(ValueError, 'stage must match'):
            self.check()

    def test_followup_cannot_expand_source_or_requirement_scope(self):
        self.answer['followups'] = [{'stage': 'discovery', 'question': 'Another catalog.',
                                    'paths': ['missing.cs'], 'requirement': 'catalog'}]
        with self.assertRaisesRegex(ValueError, 'sealed scope'):
            self.check()
        self.answer['followups'][0]['paths'] = ['Orders.cs']
        self.task['goalRequirementIds'].append('other')
        self.task['goalRequirements'].append(obligation('other', 'discovery', scope='other'))
        self.answer['followups'][0]['requirement'] = 'other'
        with self.assertRaisesRegex(ValueError, 'assigned scope'):
            self.check()

    def test_empty_unknown_binding_verification_is_valid_strict_schema(self):
        task, answer = self.verification()
        Draft202012Validator.check_schema(contracts.result_schema(task))
        self.check(answer, task)

    def test_verifier_is_bound_to_candidate_and_preview_hash(self):
        for field in ('candidateSha256', 'viewSha256'):
            task, answer = self.verification()
            answer[field] = '0' * 64
            with self.assertRaisesRegex(ValueError, 'contract'):
                self.check(answer, task)

    def test_unknown_judgement_is_bound_to_original_content(self):
        task, answer = self.verification([{'id': 'u:author:missing', 'sha256': 'a' * 64}])
        self.check(answer, task)
        answer['unknownChecks'][0]['unknownSha256'] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'content binding'):
            self.check(answer, task)

    def test_every_bound_unknown_needs_one_independent_judgement(self):
        task, answer = self.verification([{'id': 'u:first', 'sha256': 'a' * 64},
                                          {'id': 'u:second', 'sha256': 'b' * 64}])
        answer['unknownChecks'][1] = deepcopy(answer['unknownChecks'][0])
        with self.assertRaisesRegex(ValueError, 'Duplicate unknown verification'):
            self.check(answer, task)

    def test_nonblocking_judgement_cannot_retain_blocking_obligations(self):
        task, answer = self.verification([{'id': 'u:first', 'sha256': 'a' * 64}])
        answer['unknownChecks'][0]['blocksRequirements'] = ['catalog']
        with self.assertRaisesRegex(ValueError, 'cannot block'):
            self.check(answer, task)

    def test_nonblocking_or_resolved_judgement_needs_source_evidence(self):
        for status in ('non-blocking', 'resolved'):
            task, answer = self.verification([{'id': 'u:first', 'sha256': 'a' * 64}])
            answer['unknownChecks'][0].update(status=status, evidence=[])
            with self.assertRaisesRegex(ValueError, 'requires source evidence'):
                self.check(answer, task)

    def test_blocking_and_unresolved_judgements_identify_impacted_goal_obligations(self):
        for status in ('blocking', 'unresolved'):
            task, answer = self.verification([{'id': 'u:first', 'sha256': 'a' * 64}])
            answer['unknownChecks'][0]['status'] = status
            with self.assertRaisesRegex(ValueError, 'identify impacted'):
                self.check(answer, task)
            answer['unknownChecks'][0]['blocksRequirements'] = ['catalog']
            self.check(answer, task)
            answer['unknownChecks'][0]['blocksRequirements'] = ['invented']
            with self.assertRaisesRegex(ValueError, 'unknown goal'):
                self.check(answer, task)

    def test_host_keeps_uniqueness_rules_omitted_from_transport(self):
        schema = contracts.transport_schema(self.task)
        self.assertNotIn('uniqueItems', json.dumps(schema))
        answer = deepcopy(self.answer)
        answer['coverage'][0]['recordKeys'] *= 2
        contracts.validate(answer, schema)
        with self.assertRaisesRegex(ValueError, 'non-unique'):
            self.check(answer)

    def test_unknown_operation_or_stage_does_not_fall_back_to_extraction(self):
        for field in ('operation', 'stage'):
            task = deepcopy(self.task)
            task[field] = 'invented'
            with self.assertRaisesRegex(ValueError, 'Unknown'):
                contracts.result_schema(task)


if __name__ == '__main__':
    unittest.main()

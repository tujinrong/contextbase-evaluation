"""Public incremental agent regressions with synthetic provider/source only.

The fixture provider may inspect the sealed host store to construct expected
responses. Those test-oracle reads are never delivered to the model context and
do not substitute for each child task's recorded source read/query requests.
"""
from collections import Counter
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from contextbase_discovery import DiscoveryAgent
from contextbase_relationship import RelationshipAgent
from contextbase_behavior import BehaviorAgent
from contextbase_runtime import catalog, contracts
from test_independent_agents import request


PROTOCOL = 'contextbase-incremental/1'


class IncrementalAgentTests(unittest.TestCase):
    def setUp(self):
        temporary_root = Path(__file__).resolve().parents[1] / '.tmp'
        temporary_root.mkdir(exist_ok=True)
        self.temporary = tempfile.TemporaryDirectory(prefix='incremental-public-', dir=temporary_root)
        self.root = Path(self.temporary.name)
        self.source = self.root / 'source'
        self.source.mkdir()
        (self.source / 'Entry.cs').write_text(
            'class Entry {\n static void Start() { }\n}\n', encoding='utf-8')
        (self.source / 'Registration.cs').write_text(
            'class Registration {\n bool Save(int value) { return value > 0; }\n}\n', encoding='utf-8')
        self.agents = {}
        self.calls = []
        self.answers = []
        self.fail_once = None
        self.failed = False
        self.mutate = None
        self.cancel_once = False
        self.skip_originals = False
        self.use_prior_draft_listing = False
        self.read_retry_feedback = False
        self.empty_support_units = 0

    def tearDown(self):
        self.temporary.cleanup()

    def create(self, agent_type=DiscoveryAgent, *, handoff=None, name=None):
        agent = agent_type.create(self.source, self.root / (name or agent_type.name), request(),
                                  handoff=handoff, incremental_mode=True)
        self.agents[agent.session.source.root] = agent
        return agent

    @staticmethod
    def _ref(agent, path):
        row = next(item for item in agent.session.source.manifest['files'] if item['path'] == path)
        return {'path': path, 'startLine': 1, 'endLine': 2, 'sha256': row['sha256']}

    def _records(self, agent, task, unit):
        requirement = unit['requirement']
        if task['stage'] == 'discovery':
            entry = {'key': requirement + '.entry', 'ownerRequirement': requirement, 'kind': 'entry',
                     'name': 'Registration entry', 'statement': 'Synthetic source entry.',
                     'basis': 'observed-source', 'evidence': [self._ref(agent, 'Entry.cs')],
                     'dependsOn': [], 'classification': None}
            if unit['id'] == 'entry-unit':
                return [entry]
            owner = next(item for item in request()['goal']['requirements'] if item['id'] == requirement)
            function = {'key': requirement + '.record', 'ownerRequirement': requirement,
                        'kind': 'function', 'name': 'Registration', 'statement': 'Synthetic registration task.',
                        'basis': 'observed-source', 'evidence': [self._ref(agent, 'Registration.cs')],
                        'dependsOn': [], 'classification': {
                            'category': 'main', 'scope': owner['scope'], 'area': 'Synthetic area',
                            'actors': ['Synthetic operator'], 'businessObject': 'Synthetic record',
                            'purpose': 'Register a record', 'trigger': 'Submit', 'outcome': 'Registered',
                            'rationale': 'Synthetic source responsibility.',
                            'alternative': 'Considered an internal operation.',
                            'entryRefs': [requirement + '.entry']}}
            return [function]
        owner = next(item for item in request()['goal']['requirements'] if item['id'] == requirement)
        record = {'key': requirement + '.record', 'ownerRequirement': requirement,
                  'kind': 'relation' if task['stage'] == 'relationship' else 'fact',
                  'name': requirement, 'statement': 'Synthetic downstream claim.',
                  'basis': 'observed-source', 'evidence': [self._ref(agent, 'Registration.cs')],
                  'dependsOn': [key + '.record' for key in owner['requires']]}
        if task.get('catalogPolicy') == catalog.VERSION:
            record['classification'] = None
        return [record]

    def _answer(self, agent, context):
        task = context['task']
        phase = context['incremental']['phase']
        unit = context['incremental'].get('unit')
        if phase == 'plan':
            units = []
            for requirement in task['requirements']:
                if task['stage'] == 'discovery':
                    units.extend({'id': 'support-' + str(number), 'requirement': requirement,
                                  'question': 'Check a supporting source without creating an object.',
                                  'paths': ['Entry.cs']} for number in range(self.empty_support_units))
                    units.extend([
                        {'id': 'entry-unit', 'requirement': requirement,
                         'question': 'Identify the technical entry.', 'paths': ['Entry.cs']},
                        {'id': 'function-unit', 'requirement': requirement,
                         'question': 'Identify its independent user task.', 'paths': ['Registration.cs']}])
                else:
                    units.append({'id': 'analysis-unit', 'requirement': requirement,
                                  'question': 'Answer the assigned stage question.',
                                  'paths': ['Registration.cs']})
            return {'units': units}
        if phase == 'draft':
            expected_versions = []
            if unit['id'].startswith('repair-'):
                pages = {pair['request']['collection']: pair['reply']['result']
                         for pair in context['evidenceDialog']['latestEvidence']
                         if pair['request']['operation'] == 'material'}
                record = json.loads(pages['records']['bodyText'])
                expected_versions = [{'key': record['key'], 'sha256': pages['records']['sha256']}]
                record['dependsOn'] = []
                records = [record]
            elif unit['id'].startswith('support-'):
                records = []
            else:
                records = self._records(agent, task, unit)
            usage = []
            if task.get('sourceFactsSha256'):
                for record in records:
                    ref = record['evidence'][0]
                    available = [fact['id'] for fact in agent.session.fact_index().document['facts']
                                 if fact['path'] == ref['path'] and any(
                                     point['startLine'] <= ref['endLine']
                                     and ref['startLine'] <= point['endLine']
                                     for point in fact['data']['evidence'])]
                    usage.append({'recordKey': record['key'], 'factIds': available[:1],
                                  'reason': 'Synthetic overlapping syntax observation.'})
            return {'unitId': unit['id'], 'records': records, 'expectedVersions': expected_versions, 'removals': [],
                    'unknowns': [], 'followups': [], 'factUsage': usage,
                    'remainingQuestions': [], 'complete': True, 'addUnits': []}
        if phase == 'closure':
            requirement = unit['requirement'] if unit else task['requirements'][0]
            return {'requirement': requirement, 'status': 'supported',
                    'reason': 'Synthetic complete inventory check.',
                    'evidence': [self._ref(agent, 'Entry.cs')]}
        if phase != 'review':
            raise AssertionError('Unexpected incremental phase: ' + str(phase))
        proposal = agent.session.store.get('candidates/' + task['candidate'] + '.json')
        view = proposal['view']
        evidence = [self._ref(agent, 'Entry.cs'), self._ref(agent, 'Registration.cs')]
        positive = {'status': 'pass', 'reason': 'Synthetic independent source check.', 'evidence': evidence}
        classifications = {item['key']: item['sha256'] for item in catalog.bindings(view['records'])}
        return {'unitId': unit['id'], 'candidateSha256': task['candidate'], 'viewSha256': task['viewSha256'],
                'recordChecks': [{'key': key, 'recordSha256': view['records'][key]['version'], **positive}
                                 for key in unit['recordKeys']],
                'classificationChecks': [{'key': key, 'recordSha256': classifications[key], **positive}
                                         for key in unit['recordKeys'] if key in classifications
                                         and task.get('catalogPolicy') == catalog.VERSION],
                'unknownChecks': [{'unknownId': key, 'unknownSha256': view['unknowns'][key]['sha256'],
                                  'status': 'non-blocking', 'blocksRequirements': [],
                                  'reason': 'Synthetic scope determination.', 'evidence': evidence}
                                 for key in unit['unknownIds']],
                'checks': [{'requirement': key, **positive} for key in unit['requirements']],
                'scopeChecks': [{'scope': scope, **positive} for scope in unit['scopes']],
                'findings': [], 'unknowns': [],
                'factUsageCheck': positive if task.get('sourceFactsSha256') else None}

    def provider(self, workspace, job, prompt, schema, timeout):
        context = json.loads(prompt.rsplit('\n', 1)[-1])
        self.calls.append(deepcopy(context))
        agent = self.agents[Path(workspace)]
        task = context['task']
        phase = context['incremental']['phase']
        unit = context['incremental'].get('unit') or {}
        if self.fail_once == (phase, unit.get('id')) and not self.failed:
            self.failed = True
            return {'exit_code': 1, 'metadata': {'status': 'failed'}, 'answer': None}
        wrapper = {'protocol': PROTOCOL, 'taskId': task['id'], 'action': 'requests',
                   'requests': [], 'answer': None, 'workingNotes': ''}
        if context['evidenceDialog']['round'] == 1:
            paths = unit.get('paths') if phase == 'draft' else ['Entry.cs', 'Registration.cs']
            if phase == 'draft' and unit.get('id', '').startswith('repair-'):
                paths = ['Registration.cs']
            wrapper['requests'] = [{'operation': 'query', 'offset': 0, 'limit': 100,
                **{key: None for key in ('path', 'kind', 'text', 'caller', 'callee', 'route')}}]
            if not self.skip_originals:
                wrapper['requests'].extend({'operation': 'read', 'path': path,
                                            'startLine': 1, 'endLine': None} for path in paths)
            if self.use_prior_draft_listing and phase == 'draft' and unit.get('id') == 'function-unit':
                wrapper['requests'].append({'operation': 'listing', 'collection': 'records',
                                            'offset': 0, 'limit': 100})
            if phase == 'draft' and unit.get('id', '').startswith('repair-'):
                wrapper['requests'].append({'operation': 'material', 'collection': 'records',
                    'key': unit['requirement'] + '.record', 'offset': 0, 'limit': 12000})
            feedback_keys = context['incremental'].get('feedbackKeys', [])
            if self.read_retry_feedback and phase == 'plan':
                key = next((key for key in feedback_keys if key.startswith('verification-')), None)
                if key:
                    wrapper['requests'].append({'operation': 'material', 'collection': 'feedback',
                                                'key': key, 'offset': 0, 'limit': 12000})
        else:
            answer = self._answer(agent, context)
            if self.mutate:
                self.mutate(context, answer)
            self.answers.append(deepcopy(answer))
            wrapper.update(action='finish', answer=answer)
        if self.cancel_once:
            self.cancel_once = False
            agent.session.cancel('Synthetic cancellation during provider execution.')
        return {'exit_code': 0, 'metadata': {'status': 'passed'}, 'answer': wrapper}

    def run_agent(self, agent):
        with patch('contextbase_runtime.provider.run_job', side_effect=self.provider):
            return agent.run()

    def phase_counts(self):
        return Counter((context['incremental']['phase'],
                        (context['incremental'].get('unit') or {}).get('id')) for context in self.calls)

    def test_discovery_assembles_two_persisted_drafts_without_a_whole_catalog_model_answer(self):
        agent = self.create()
        self.assertEqual('complete', self.run_agent(agent)['status'])
        self.assertEqual(['catalog'], agent.status()['acceptedRequirements'])
        self.assertEqual({'catalog.entry', 'catalog.record'}, set(agent.status()['records']))
        self.assertTrue(all(len(answer.get('records', [])) <= 1 for answer in self.answers))
        self.assertEqual({'plan', 'draft', 'closure', 'review'},
                         {context['incremental']['phase'] for context in self.calls})
        self.assertTrue(all(context['task']['id'] != context['task']['rootTaskId'] for context in self.calls))
        child_contexts = {context['task']['contextId'] for context in self.calls}
        self.assertGreaterEqual(len(child_contexts), 6)
        self.assertTrue(all('verificationView' not in context for context in self.calls))

    def test_three_agents_run_independently_and_reverify_portable_premises(self):
        handoff = None
        for agent_type in (DiscoveryAgent, RelationshipAgent, BehaviorAgent):
            agent = self.create(agent_type, handoff=handoff)
            self.assertEqual('complete', self.run_agent(agent)['status'])
            handoff = agent.export()
        self.assertEqual(['catalog', 'links', 'rules'], handoff['payload']['acceptedRequirements'])
        for context in self.calls:
            if context['incremental']['phase'] == 'draft':
                self.assertEqual(context['task']['stage'],
                                 next(row['stage'] for row in request()['goal']['requirements']
                                      if row['id'] == context['incremental']['unit']['requirement']))

    def test_total_source_exceeding_window_keeps_prior_typed_draft_queryable(self):
        # Reduce the resource window in the synthetic transport, not the source
        # scope. Both source files and all canonical obligations remain present.
        from contextbase_runtime.incremental import WINDOW_POLICY
        for path in self.source.glob('*.cs'):
            with path.open('a', encoding='utf-8') as handle:
                handle.write('// Synthetic padding preserves source identity.\n' * 200)
        policy = {**WINDOW_POLICY, 'maxChars': 4096}
        self.assertGreater(sum(path.stat().st_size for path in self.source.glob('*.cs')), policy['maxChars'])
        self.use_prior_draft_listing = True
        agent = self.create()
        with patch('contextbase_runtime.incremental.WINDOW_POLICY', policy):
            self.assertEqual('complete', self.run_agent(agent)['status'])
        later = [context for context in self.calls
                 if context['incremental']['phase'] == 'draft'
                 and context['incremental']['unit']['id'] == 'function-unit'
                 and context['evidenceDialog']['round'] > 1]
        listings = [pair for context in later for pair in context['evidenceDialog']['latestEvidence']
                    if pair['request']['operation'] == 'listing']
        self.assertTrue(listings)
        self.assertIn('catalog.entry', {row['key'] for pair in listings for row in pair['reply']['result']['items']})
        self.assertEqual({'catalog.entry', 'catalog.record'}, set(agent.status()['records']))
        self.assertTrue(all(len(answer.get('records', [])) <= 1 for answer in self.answers))

    def test_later_agents_without_handoff_do_not_invoke_an_upstream_agent(self):
        for agent_type in (RelationshipAgent, BehaviorAgent):
            agent = self.create(agent_type)
            self.assertEqual('needs-prerequisites', self.run_agent(agent)['status'])
        self.assertEqual([], self.calls)

    def test_global_omission_blocks_adoption_after_all_local_record_reviews_pass(self):
        agent = self.create()
        def omit(context, answer):
            unit = context['incremental'].get('unit') or {}
            if context['incremental']['phase'] == 'review' and unit.get('kind') == 'global':
                answer['checks'][0]['status'] = 'fail'
                answer['findings'].append({'id': 'missing-entry', 'severity': 'blocking',
                    'requirement': unit['requirements'][0], 'detail': 'Synthetic omitted source entry.',
                    'evidence': [self._ref(agent, 'Entry.cs')]})
        self.mutate = omit
        result = self.run_agent(agent)
        self.assertEqual('needs-investigation', result['status'])
        self.assertEqual([], agent.status()['acceptedRequirements'])
        self.assertEqual(1, len(agent.status()['candidates']))

    def test_local_record_failure_cannot_be_overridden_by_global_pass(self):
        agent = self.create()
        def fail(context, answer):
            unit = context['incremental'].get('unit') or {}
            if context['incremental']['phase'] == 'review' and unit.get('recordKeys'):
                answer['recordChecks'][0]['status'] = 'fail'
        self.mutate = fail
        self.assertEqual('needs-investigation', self.run_agent(agent)['status'])
        self.assertEqual([], agent.status()['acceptedRequirements'])

    def test_draft_failure_resume_preserves_completed_plan_and_first_unit(self):
        agent = self.create()
        self.fail_once = ('draft', 'function-unit')
        with self.assertRaises(RuntimeError):
            self.run_agent(agent)
        before = self.phase_counts()
        self.assertEqual([], agent.status()['candidates'])
        agent.session.resume(request())
        self.assertEqual('complete', self.run_agent(agent)['status'])
        after = self.phase_counts()
        self.assertEqual(before[('plan', None)], after[('plan', None)])
        self.assertEqual(before[('draft', 'entry-unit')], after[('draft', 'entry-unit')])

    def test_review_failure_resume_preserves_frozen_candidate_and_completed_slices(self):
        agent = self.create()
        self.fail_once = ('review', 'global-0001')
        with self.assertRaises(RuntimeError):
            self.run_agent(agent)
        before = self.phase_counts()
        self.assertEqual(1, len(agent.status()['candidates']))
        candidate = agent.status()['candidates'][0]
        agent.session.resume(request())
        self.assertEqual('complete', self.run_agent(agent)['status'])
        after = self.phase_counts()
        self.assertEqual([candidate], agent.status()['candidates'])
        for key in before:
            if key[0] != 'review' or key[1] == 'records-0000':
                self.assertEqual(before[key], after[key], key)

    def test_semantically_rejected_review_slice_is_not_a_completed_resume_checkpoint(self):
        from contextbase_runtime import review_set
        make_units = review_set.make_units
        agent = self.create()
        def invalid_binding(context, answer):
            unit = context['incremental'].get('unit') or {}
            if context['incremental']['phase'] == 'review' and unit.get('id') == 'records-0001':
                answer['recordChecks'][0]['recordSha256'] = 'e' * 64
        self.mutate = invalid_binding
        # Two small slices make the first valid review a real saved checkpoint,
        # followed by an invalid but schema-conforming second review response.
        with patch('contextbase_runtime.review_set.make_units',
                   side_effect=lambda task, view: make_units(task, view, max_records=1)):
            with self.assertRaisesRegex(ValueError, 'fingerprint|contract|schema'):
                self.run_agent(agent)
            self.assertEqual('stopped', agent.status()['status'])
            self.assertEqual(1, len(agent.status()['candidates']))
            before = self.phase_counts()
            self.mutate = None
            agent.session.resume(request())
            self.assertEqual('complete', self.run_agent(agent)['status'])
        after = self.phase_counts()
        self.assertGreater(after[('review', 'records-0001')], before[('review', 'records-0001')])
        self.assertEqual(before[('review', 'records-0000')], after[('review', 'records-0000')])
        for key in before:
            if key[0] != 'review':
                self.assertEqual(before[key], after[key], key)

    def test_conflicting_draft_is_not_a_completed_resume_checkpoint(self):
        agent = self.create()
        def conflict(context, answer):
            unit = context['incremental'].get('unit') or {}
            if context['incremental']['phase'] == 'draft' and unit.get('id') == 'function-unit':
                record = self._records(agent, context['task'], {**unit, 'id': 'entry-unit'})[0]
                record['statement'] = 'A conflicting replacement without an expected version.'
                record['evidence'] = [self._ref(agent, 'Registration.cs')]
                answer['records'] = [record]
                answer['factUsage'][0]['recordKey'] = record['key']
        self.mutate = conflict
        with self.assertRaisesRegex(ValueError, 'expected version'):
            self.run_agent(agent)
        self.assertEqual('stopped', agent.status()['status'])
        self.assertEqual([], agent.status()['candidates'])
        before = self.phase_counts()
        self.mutate = None
        agent.session.resume(request())
        self.assertEqual('complete', self.run_agent(agent)['status'])
        after = self.phase_counts()
        self.assertGreater(after[('draft', 'function-unit')], before[('draft', 'function-unit')])
        self.assertEqual(before[('draft', 'entry-unit')], after[('draft', 'entry-unit')])
        self.assertEqual(before[('plan', None)], after[('plan', None)])

    def test_final_dangling_reference_uses_local_cas_repair_not_whole_catalog_regeneration(self):
        agent = self.create()
        def dangling(context, answer):
            unit = context['incremental'].get('unit') or {}
            if context['incremental']['phase'] == 'draft' and unit.get('id') == 'function-unit':
                answer['records'][0]['dependsOn'] = ['missing.record']
        self.mutate = dangling
        self.assertEqual('complete', self.run_agent(agent)['status'])
        counts = self.phase_counts()
        self.assertEqual(2, counts[('plan', None)])
        self.assertEqual(2, counts[('draft', 'entry-unit')])
        self.assertEqual(2, counts[('draft', 'function-unit')])
        self.assertEqual(4, counts[('closure', None)])
        repairs = [key for key in counts if key[0] == 'draft' and key[1].startswith('repair-')]
        self.assertEqual(1, len(repairs))
        self.assertEqual(2, counts[repairs[0]])
        self.assertEqual([], agent.status()['records']['catalog.record']['dependsOn'])
        repair_answers = [answer for answer in self.answers if answer.get('unitId', '').startswith('repair-')]
        self.assertEqual('catalog.record', repair_answers[0]['expectedVersions'][0]['key'])
        self.assertEqual(64, len(repair_answers[0]['expectedVersions'][0]['sha256']))
        repair_deliveries = [pair for context in self.calls
            if context['incremental']['phase'] == 'draft'
            and (context['incremental'].get('unit') or {}).get('id', '').startswith('repair-')
            for pair in context['evidenceDialog']['latestEvidence']]
        self.assertIn('read', {pair['request']['operation'] for pair in repair_deliveries})
        self.assertIn('material', {pair['request']['operation'] for pair in repair_deliveries})

    def test_explicit_retry_exposes_previous_candidate_and_findings_as_pageable_feedback(self):
        agent = self.create()
        def reject(context, answer):
            unit = context['incremental'].get('unit') or {}
            if context['incremental']['phase'] == 'review' and unit.get('kind') == 'global':
                answer['checks'][0]['status'] = 'fail'
                answer['findings'].append({'id': 'retry-this-gap', 'severity': 'blocking',
                    'requirement': unit['requirements'][0],
                    'detail': 'Synthetic retry finding: inspect the missing registration.',
                    'evidence': [self._ref(agent, 'Registration.cs')]})
        self.mutate = reject
        first = self.run_agent(agent)
        self.assertEqual('needs-investigation', first['status'])
        start = len(self.calls)
        self.mutate = None
        self.read_retry_feedback = True
        with patch('contextbase_runtime.provider.run_job', side_effect=self.provider):
            result = agent.retry(first['pending']['candidate'])
        self.assertEqual('complete', result['status'])
        retried = self.calls[start:]
        plans = [context for context in retried if context['incremental']['phase'] == 'plan']
        self.assertTrue(plans)
        for context in plans:
            keys = context['incremental']['feedbackKeys']
            self.assertIn('previous-candidate', keys)
            self.assertTrue(any(key.startswith('verification-') for key in keys))
            self.assertNotIn('feedback', context)
        pages = [pair['reply']['result']['bodyText'] for context in plans
                 for pair in context['evidenceDialog']['latestEvidence']
                 if pair['request']['operation'] == 'material'
                 and pair['request']['collection'] == 'feedback']
        self.assertTrue(any('Synthetic retry finding' in text for text in pages))

    def test_empty_completed_support_units_do_not_hide_real_same_unit_stagnation(self):
        self.empty_support_units = 3
        agent = self.create(name='completed-supports')
        self.assertEqual('complete', self.run_agent(agent)['status'])
        self.assertEqual({'catalog.entry', 'catalog.record'}, set(agent.status()['records']))
        completed_supports = {answer['unitId'] for answer in self.answers
                              if answer.get('unitId', '').startswith('support-') and answer['complete']}
        self.assertEqual({'support-' + str(number) for number in range(3)}, completed_supports)
        stuck = self.create(name='stuck-support')
        def no_progress(context, answer):
            unit = context['incremental'].get('unit') or {}
            if context['incremental']['phase'] == 'plan':
                # This half isolates genuine same-unit stagnation. Fairly
                # executing other productive units would legitimately reset it.
                answer['units'] = [item for item in answer['units'] if item['id'] == 'support-0']
            elif context['incremental']['phase'] == 'draft' and unit.get('id') == 'support-0':
                answer.update(complete=False, remainingQuestions=['The same question is still unanswered.'])
        self.mutate = no_progress
        start = len(self.calls)
        with self.assertRaisesRegex(ValueError, 'structural progress'):
            self.run_agent(stuck)
        self.assertEqual([], stuck.status()['acceptedRequirements'])
        stopped_drafts = [context for context in self.calls[start:]
                          if context['incremental']['phase'] == 'draft']
        self.assertEqual(3, len({context['task']['id'] for context in stopped_drafts}))
        self.assertTrue(all(context['incremental']['unit']['id'] == 'support-0'
                            for context in stopped_drafts))

    def test_dynamic_empty_unit_expansion_cannot_restart_progress_protection(self):
        agent = self.create()
        drafts = {'count': 0}
        def expand_without_result(context, answer):
            phase = context['incremental']['phase']
            if phase == 'plan':
                answer['units'] = [{'id': 'entry-unit', 'requirement': 'catalog',
                    'question': 'Inspect an initially bounded source responsibility.', 'paths': ['Entry.cs']}]
            elif phase == 'draft':
                drafts['count'] += 1
                if drafts['count'] > 12:
                    raise AssertionError('Mock safety guard: unproductive unit expansion did not stop.')
                answer.update(records=[], expectedVersions=[], removals=[], unknowns=[], followups=[],
                              factUsage=[], remainingQuestions=[], complete=True,
                              addUnits=[{'id': 'next-unit-' + str(drafts['count']),
                                         'requirement': 'catalog',
                                         'question': 'Continue the same unanswered investigation.',
                                         'paths': ['Entry.cs']}])
        self.mutate = expand_without_result
        with self.assertRaisesRegex(ValueError, 'progress'):
            self.run_agent(agent)
        self.assertLessEqual(drafts['count'], 3)
        self.assertEqual('stopped', agent.status()['status'])
        self.assertEqual([], agent.status()['candidates'])
        self.assertEqual([], agent.status()['acceptedRequirements'])

    def test_unresolved_unit_rotates_fairly_with_durable_continuation_and_stays_unadopted(self):
        agent = self.create()
        question = 'Confirm whether the entry has an independent user-facing outcome.'
        draft_order, continuations, first_answers = [], [], []
        def unresolved_entry(context, answer):
            phase = context['incremental']['phase']
            unit = context['incremental'].get('unit') or {}
            if phase == 'draft':
                draft_order.append(unit['id'])
                if unit['id'] == 'entry-unit':
                    if not first_answers:
                        answer.update(complete=False, remainingQuestions=[question], unknowns=[{
                            'id': 'entry-gap', 'question': question, 'relatedRequirements': ['catalog'],
                            'blocksRequirements': ['catalog'],
                            'scopeReason': 'The selected catalog partition remains unresolved.'}])
                        first_answers.append(deepcopy(answer))
                    else:
                        continuations.append(deepcopy(context['incremental'].get('continuation')))
                        answer.update(records=[], expectedVersions=[], removals=[], unknowns=[],
                                      followups=[], factUsage=[], complete=True, remainingQuestions=[])
            elif phase == 'closure':
                answer.update(status='unresolved', reason='The entry boundary remains an unresolved catalog obligation.')
            elif phase == 'review':
                for check in answer['unknownChecks']:
                    check.update(status='blocking', blocksRequirements=['catalog'],
                                 reason='The author ended its unit without answering the source-bound question.')
        self.mutate = unresolved_entry
        result = self.run_agent(agent)
        self.assertEqual('needs-investigation', result['status'])
        self.assertEqual([], agent.status()['acceptedRequirements'])
        entry_positions = [index for index, unit_id in enumerate(draft_order) if unit_id == 'entry-unit']
        self.assertGreaterEqual(len(entry_positions), 2)
        function_position = draft_order.index('function-unit')
        self.assertLess(entry_positions[0], function_position)
        self.assertLess(function_position, entry_positions[1])
        continuation = continuations[0]
        self.assertIsNotNone(continuation)
        self.assertEqual('contextbase-unit-continuation/1', continuation['schema'])
        self.assertEqual(contracts.digest(first_answers[0]), continuation['previousAnswerSha256'])
        self.assertEqual([question], continuation['remainingQuestions'])
        self.assertEqual(['catalog.entry'], continuation['recordKeys'])
        previous_record_sha = contracts.digest(first_answers[0]['records'][0])
        self.assertEqual([{'key': 'catalog.entry', 'sha256': previous_record_sha,
                           'submittedSha256': previous_record_sha}], continuation['recordBindings'])
        self.assertEqual(['entry-unit:entry-gap'], continuation['unknownIds'])
        normalized_question = {**first_answers[0]['unknowns'][0], 'id': 'entry-unit:entry-gap'}
        self.assertEqual([{'id': 'entry-unit:entry-gap', 'sha256': contracts.digest(normalized_question)}],
                         continuation['unknownBindings'])
        self.assertRegex(continuation['currentMergedRecordsSha256'], '^[0-9a-f]{64}$')
        self.assertNotIn('previousAnswer', continuation)
        candidate = agent.session.store.get('candidates/' + result['pending']['candidate'] + '.json')
        self.assertEqual({'catalog.entry', 'catalog.record'}, set(candidate['view']['records']))
        self.assertEqual('unresolved', candidate['answer']['coverage'][0]['status'])
        self.assertEqual(1, len(candidate['answer']['unknowns']))
        self.assertEqual('entry-unit:entry-gap', candidate['answer']['unknowns'][0]['id'])
        self.assertEqual(question, candidate['answer']['unknowns'][0]['question'])
        self.assertEqual(['catalog'], candidate['answer']['unknowns'][0]['blocksRequirements'])
        self.assertTrue(agent.status()['verifications'])
        verification = agent.session.store.get('verifications/' + result['pending']['verification'] + '.json')
        self.assertEqual('blocking', verification['answer']['unknownChecks'][0]['status'])

    def test_two_unfinished_units_cannot_reset_global_checkpoint_stagnation_by_rotation(self):
        agent = self.create()
        draft_order = []
        def rotate_without_result(context, answer):
            if context['incremental']['phase'] == 'draft':
                draft_order.append(context['incremental']['unit']['id'])
                if len(draft_order) > 12:
                    raise AssertionError('Mock safety guard: unfinished units kept rotating without progress.')
                answer.update(records=[], expectedVersions=[], removals=[], unknowns=[], followups=[],
                              factUsage=[], complete=False, addUnits=[],
                              remainingQuestions=['The same investigation is still unanswered.'])
        self.mutate = rotate_without_result
        with self.assertRaisesRegex(ValueError, 'structural progress'):
            self.run_agent(agent)
        self.assertLessEqual(len(draft_order), 3)
        self.assertGreaterEqual(len(set(draft_order)), 2)
        self.assertEqual([], agent.status()['candidates'])
        self.assertEqual([], agent.status()['acceptedRequirements'])

    def test_cancelled_late_provider_result_cannot_record_or_adopt(self):
        agent = self.create()
        self.cancel_once = True
        with self.assertRaises(ValueError):
            self.run_agent(agent)
        state = agent.status()
        self.assertEqual('cancelled', state['status'])
        self.assertEqual([], state['candidates'])
        self.assertEqual([], state['acceptedRequirements'])

    def test_original_source_is_required_per_child_not_only_fact_pointers(self):
        agent = self.create()
        self.skip_originals = True
        with self.assertRaises(ValueError):
            self.run_agent(agent)
        self.assertEqual([], agent.status()['acceptedRequirements'])

    def test_injected_provider_is_never_authority_for_aggregate_adoption(self):
        agent = self.create()
        result = agent.run(runner=self.provider)
        self.assertEqual('needs-investigation', result['status'])
        self.assertEqual([], agent.status()['acceptedRequirements'])

    def corrupt_manifest(self, agent, task_id):
        path = agent.session.store.path('tasks/' + task_id + '/incremental.json')
        stored = json.loads(path.read_text(encoding='utf-8'))
        stored['payload']['tampered'] = True
        # Recompute the storage envelope so the composite provenance binding,
        # rather than only ArtifactStore's generic integrity check, rejects it.
        stored['sha256'] = contracts.digest(stored['payload'])
        path.write_text(json.dumps(stored, ensure_ascii=False), encoding='utf-8')

    def test_composite_transcript_is_replayed_before_normal_adoption(self):
        agent = self.create()
        with patch('contextbase_runtime.provider.run_job', side_effect=self.provider):
            proposal = agent.session.execute('discovery')
            agent.session.verify(proposal['id'])
        artifact = agent.session.store.get('candidates/' + proposal['id'] + '.json')
        self.corrupt_manifest(agent, artifact['taskId'])
        with self.assertRaises(ValueError):
            agent.session.adopt(proposal['id'])
        self.assertEqual([], agent.status()['acceptedRequirements'])

    def test_composite_transcript_is_replayed_before_external_premise_activation(self):
        discovery = self.create()
        self.assertEqual('complete', self.run_agent(discovery)['status'])
        recipient = self.create(RelationshipAgent, handoff=discovery.export())
        from contextbase_runtime import handoff as transfer
        activate = transfer._activate
        def tamper(agent, candidate_id, verification_id):
            artifact = agent.session.store.get('verifications/' + verification_id + '.json')
            self.corrupt_manifest(agent, artifact['taskId'])
            return activate(agent, candidate_id, verification_id)
        with patch('contextbase_runtime.provider.run_job', side_effect=self.provider):
            with patch('contextbase_runtime.handoff._activate', side_effect=tamper):
                with self.assertRaises(ValueError):
                    recipient.run()
        self.assertEqual([], recipient.status()['acceptedRequirements'])
        self.assertIsNone(recipient.status()['revision'])


if __name__ == '__main__':
    unittest.main()

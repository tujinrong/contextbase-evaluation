"""The author's scope closure is distinct from the later independent review."""
from copy import deepcopy
import json
import unittest
from unittest.mock import patch

from contextbase_runtime import catalog, contracts as c, incremental
from contextbase_runtime.evidence_dialog import _DeliveryProgress, validate_delivery
import test_incremental_agents as public_fixture
import test_incremental_protocol as protocol_fixture
from test_incremental_protocol import NoSourceAccess, root_context, root_task


REF = {'path': 'Root.cs', 'startLine': 1, 'endLine': 1, 'sha256': 'a' * 64}


def package_fixture(record_count=123, unit_count=7):
    task = root_task()
    task.update(catalogPolicy=catalog.VERSION, sourceFactsSha256='b' * 64,
                authorizedSourcePaths=['Root.cs'])
    task['goalRequirements'].extend([
        {'id': 'links', 'stage': 'relationship', 'scope': 'system', 'question': 'Trace connections',
         'requires': ['catalog']},
        {'id': 'rules', 'stage': 'behavior', 'scope': 'system', 'question': 'Trace values',
         'requires': ['links']}])
    task['goalRequirementIds'] = ['catalog', 'links', 'rules']
    context = root_context(task)
    context['inventory']['files'] = [{'path': 'Root.cs', 'sha256': REF['sha256'],
                                       'lines': 1, 'bytes': 16, 'encoding': 'utf-8'}]
    context['inventory']['omitted'] = [{'path': 'tests', 'reason': 'excluded-directory'}]
    units = [{'id': 'unit-' + str(number), 'requirement': 'catalog',
              'question': 'Investigate responsibility ' + str(number), 'paths': ['Root.cs']}
             for number in range(unit_count)]
    events = []
    for number, unit in enumerate(units):
        records = [{'key': 'support:' + str(index), 'ownerRequirement': 'catalog',
                    'kind': 'support', 'name': 'Declared support ' + str(index),
                    'statement': 'Synthetic source support.', 'basis': 'observed-source',
                    'evidence': [deepcopy(REF)], 'dependsOn': [], 'classification': None}
                   for index in range(number, record_count, unit_count)]
        followups = ([{'stage': 'behavior', 'requirement': 'rules', 'paths': ['Root.cs'],
                       'question': 'A future behavior question remains open'}] if number == 0 else [])
        events.append({'unit': deepcopy(unit), 'answer': {
            'unitId': unit['id'], 'records': records, 'expectedVersions': [], 'removals': [],
            'unknowns': [], 'followups': followups,
            'factUsage': [{'recordKey': row['key'], 'factIds': ['symbol:declared-' + row['key']],
                           'reason': 'An author-declared supporting syntax fact'} for row in records],
            'remainingQuestions': [], 'complete': True, 'addUnits': []}})
    reduced = incremental.investigation.reduce_drafts(task, events)
    return task, context, units, events, reduced


class ClosurePackageTests(unittest.TestCase):
    def package(self, **kwargs):
        values = package_fixture(**kwargs)
        return (*values, incremental._closure_package(*values))

    def test_complete_catalog_units_future_questions_and_bindings_are_explicit_author_claims(self):
        task, context, units, events, reduced, package = self.package()
        self.assertEqual(123, package['counts']['records'])
        self.assertEqual(7, package['counts']['units'])
        self.assertEqual(0, package['counts']['unknowns'])
        self.assertEqual(1, package['counts']['followups'])
        self.assertEqual(task['goalRequirements'], package['goal']['requirements'])
        self.assertEqual(task['requirements'], package['assignedRequirements'])
        self.assertEqual({row['key'] for row in reduced['records']},
                         {row['key'] for row in package['catalog']})
        self.assertEqual(context['inventory']['omitted'], package['input']['omitted'])
        self.assertEqual(context['request']['allowedPaths'], package['input']['allowedPaths'])
        self.assertEqual(reduced['followups'][0], package['followups'][0]['content'])
        self.assertEqual(c.digest(reduced['followups'][0]), package['followups'][0]['sha256'])
        self.assertEqual('rules', package['followups'][0]['content']['requirement'])
        rows = {row['key']: row for row in reduced['records']}
        for summary, event in zip(package['units'], events):
            self.assertEqual(event['unit']['question'], summary['question'])
            self.assertTrue(summary['investigationEnded'])
            self.assertEqual(c.digest(event['answer']), summary['lastAnswerSha256'])
            for binding in summary['recordBindings']:
                self.assertEqual(c.digest(rows[binding['key']]), binding['sha256'])
        for declaration in package['factUsage']:
            self.assertEqual(1, declaration['declaredFactIdCount'])
            self.assertTrue(declaration['declarationPresent'])
            self.assertNotIn('status', declaration)
            self.assertNotIn('pass', declaration)
        self.assertNotIn('coverage', package)
        self.assertNotIn('supported', package)
        self.assertIn('unverified', package['trust'].lower())
        self.assertLess(len(incremental._json(package)), incremental._CLOSURE_INLINE_CHARS)

    def test_drive_adds_package_only_to_pending_closure_materials(self):
        task, context, units, events, reduced = package_fixture(record_count=14)
        seen = []

        def invoke(phase, unit, materials, schema):
            seen.append((phase, deepcopy(materials)))
            if phase == 'plan':
                return {'units': deepcopy(units)}
            if phase == 'draft':
                return deepcopy(next(event['answer'] for event in events if event['unit']['id'] == unit['id']))
            return {'requirement': 'catalog', 'status': 'unresolved', 'reason': 'Synthetic scope gap', 'evidence': []}

        invoke.commit = lambda: None
        invoke.reject = lambda error: self.fail(str(error))
        result = incremental._drive(task, context, invoke)
        for phase, materials in seen:
            if phase == 'closure':
                self.assertIn('obligation-closure', materials['feedback'])
                self.assertEqual(1, len(materials['feedback']['obligation-closure']['followups']))
            else:
                self.assertNotIn('obligation-closure', materials['feedback'])
        self.assertEqual('unresolved', result['coverage'][0]['status'])
        self.assertEqual(reduced['followups'], result['followups'])

    def test_inherited_unknowns_and_all_available_followups_are_retained_without_scope_filtering(self):
        task, context, units, events, reduced = package_fixture(record_count=1, unit_count=1)
        question = {'id': 'prior-question', 'question': 'An inherited scope question',
                    'relatedRequirements': ['catalog'], 'blocksRequirements': ['catalog'],
                    'scopeReason': 'Needs source review'}
        context['currentUnknowns'] = {question['id']: question}
        other = {'stage': 'relationship', 'requirement': 'links', 'paths': [],
                 'question': 'Another original downstream question'}
        context['handoffQuestions'] = [other]
        context['feedback'] = {'candidate': {'answer': {'followups': [deepcopy(other)]}}}
        package = incremental._closure_package(task, context, units, events, reduced)
        self.assertEqual(1, package['counts']['unknowns'])
        self.assertEqual(question, package['unknowns'][0]['content'])
        self.assertEqual(c.digest(question), package['unknowns'][0]['sha256'])
        self.assertEqual(2, package['counts']['followups'])
        self.assertEqual({'rules', 'links'}, {row['content']['requirement'] for row in package['followups']})

    def test_only_closure_context_receives_complete_inline_package(self):
        task, context, units, events, reduced, package = self.package()
        materials = incremental._collections(reduced['records'], reduced['unknowns'], reduced['factUsage'], units)
        materials['feedback']['obligation-closure'] = package
        child = {**deepcopy(task), 'rootTaskId': task['id']}
        closure = incremental._base_context(context, child, 'closure', {'requirement': 'catalog'}, materials)
        block = closure['incremental']['obligationClosurePackage']
        self.assertEqual('complete-inline', block['delivery'])
        self.assertEqual(package, block['package'])
        self.assertEqual(c.digest(package), block['sha256'])
        self.assertEqual(len(incremental._json(package)), block['totalChars'])
        for phase in ('plan', 'draft'):
            # A package in the separate local test dictionary must not change
            # unrelated phase contexts into a new closure interface.
            base = incremental._base_context(context, child, phase, units[0],
                incremental._collections(reduced['records'], reduced['unknowns'], reduced['factUsage'], units))
            self.assertNotIn('obligationClosurePackage', base['incremental'])
        self.assertNotIn('followups', incremental._COLLECTIONS)

    def test_oversized_package_has_explicit_pageable_complete_future_followups(self):
        task, context, units, events, reduced = package_fixture(record_count=1, unit_count=1)
        events[0]['answer']['followups'][0]['question'] = 'x' * 300_000
        reduced = incremental.investigation.reduce_drafts(task, events)
        package = incremental._closure_package(task, context, units, events, reduced)
        materials = incremental._collections(reduced['records'], reduced['unknowns'], reduced['factUsage'], units)
        materials['feedback']['obligation-closure'] = package
        child = {**deepcopy(task), 'rootTaskId': task['id']}
        closure = incremental._base_context(context, child, 'closure', {'requirement': 'catalog'}, materials)
        block = closure['incremental']['obligationClosurePackage']
        self.assertEqual('pageable', block['delivery'])
        self.assertNotIn('package', block)
        self.assertEqual(1, block['counts']['followups'])
        self.assertEqual('feedback', block['collection'])
        self.assertEqual('obligation-closure', block['key'])
        pieces, offset = [], 0
        while True:
            reply = incremental._material_reply({'operation': 'material', 'collection': block['collection'],
                'key': block['key'], 'offset': offset, 'limit': 12000}, materials, child)
            pieces.append(reply['result']['bodyText'])
            if not reply['result']['truncated']:
                break
            offset = reply['result']['nextOffset']
        self.assertEqual(package, json.loads(''.join(pieces)))

    def test_package_references_and_fact_counts_grant_no_source_or_fact_delivery(self):
        task, context, units, events, reduced, package = self.package(record_count=1, unit_count=1)
        materials = incremental._collections()
        materials['feedback']['obligation-closure'] = package
        request = {'operation': 'material', 'collection': 'feedback', 'key': 'obligation-closure',
                   'offset': 0, 'limit': 12000}
        pair = {'request': request, 'reply': incremental._material_reply(request, materials, task)}
        progress = _DeliveryProgress()
        self.assertFalse(progress.consume([pair]))

        class KnownRefSource:
            @staticmethod
            def verify_evidence_many(refs):
                for ref in refs:
                    c.validate(ref, c.EVIDENCE)

        with self.assertRaisesRegex(ValueError, 'not supplied as original text'):
            validate_delivery(KnownRefSource(), {'evidence': package['catalog'][0]['evidence']}, [pair])
        with self.assertRaisesRegex(ValueError, 'not supplied in this task'):
            validate_delivery(KnownRefSource(), {'factUsage': [{'recordKey': 'support:0',
                'factIds': ['symbol:declared-support:0']}]}, [pair])

    def test_closure_package_does_not_automatically_make_positive_closure_valid(self):
        case = public_fixture.IncrementalAgentTests()
        case.setUp()
        self.addCleanup(case.tearDown)
        agent = case.create()
        original = case.provider

        def provider(workspace, job, prompt, schema, timeout):
            context = json.loads(prompt.rsplit('\n', 1)[-1])
            if context['incremental']['phase'] != 'closure':
                return original(workspace, job, prompt, schema, timeout)
            package = context['incremental']['obligationClosurePackage']['package']
            return {'exit_code': 0, 'metadata': {'status': 'passed'}, 'answer': {
                'protocol': incremental.VERSION, 'taskId': context['task']['id'], 'action': 'finish',
                'requests': [], 'workingNotes': '', 'answer': {'requirement': 'catalog',
                'status': 'supported', 'reason': 'Copied the package citation',
                'evidence': package['catalog'][0]['evidence']}}}

        with patch('contextbase_runtime.provider.run_job', side_effect=provider):
            with self.assertRaisesRegex(ValueError, 'not supplied as original text'):
                agent.run()
        self.assertEqual([], agent.status()['acceptedRequirements'])
        self.assertEqual([], agent.status()['candidates'])

    def test_closure_package_does_not_relax_the_delivery_no_progress_guard(self):
        case = protocol_fixture.IncrementalContinuationTests()
        case.setUp()
        self.addCleanup(case.tearDown)
        task, context, units, events, reduced = package_fixture(record_count=1, unit_count=1)
        package = incremental._closure_package(task, context, units, events, reduced)
        materials = incremental._collections(reduced['records'], reduced['unknowns'], reduced['factUsage'], units)
        materials['feedback']['obligation-closure'] = package
        calls = []

        def provider(workspace, job, prompt, schema, timeout):
            current = json.loads(prompt.rsplit('\n', 1)[-1])
            calls.append(current)
            return {'exit_code': 0, 'metadata': {'status': 'passed'}, 'answer': {
                'protocol': incremental.VERSION, 'taskId': current['task']['id'], 'action': 'requests',
                'answer': None, 'workingNotes': '', 'requests': [{'operation': 'material',
                    'collection': 'feedback', 'key': 'obligation-closure', 'offset': 0, 'limit': 12000}]}}

        with patch('contextbase_runtime.incremental.EvidenceAccess', NoSourceAccess):
            with self.assertRaisesRegex(ValueError, 'no source, material or draft progress'):
                incremental._dialog(case.source, None, case.store, task, context, 'closure',
                    {'requirement': 'catalog'}, materials, 'Synthetic author instruction.',
                    incremental.investigation.closure_schema(task, 'catalog'), provider, 10, lambda: None)
        self.assertEqual(4, len(calls))
        self.assertTrue(all(row['incremental']['obligationClosurePackage']['delivery'] == 'complete-inline'
                            for row in calls))

    def test_public_resume_skips_saved_plan_and_drafts_then_performs_independent_review(self):
        case = public_fixture.IncrementalAgentTests()
        case.setUp()
        self.addCleanup(case.tearDown)
        agent = case.create()
        case.fail_once = ('closure', None)
        with self.assertRaises(RuntimeError):
            case.run_agent(agent)
        before = case.phase_counts()
        self.assertEqual([], agent.status()['candidates'])
        agent.session.resume(public_fixture.request())
        self.assertEqual('complete', case.run_agent(agent)['status'])
        after = case.phase_counts()
        for key in before:
            if key[0] in {'plan', 'draft'}:
                self.assertEqual(before[key], after[key])
        self.assertGreater(sum(count for key, count in after.items() if key[0] == 'review'), 0)
        closures = [row for row in case.calls if row['incremental']['phase'] == 'closure']
        self.assertTrue(all(row['incremental']['obligationClosurePackage']['package']['counts']['units'] == 2
                            for row in closures))

    def test_positive_author_closure_cannot_override_independent_omission_failure(self):
        case = public_fixture.IncrementalAgentTests()
        case.setUp()
        self.addCleanup(case.tearDown)
        agent = case.create()

        def omit(context, answer):
            unit = context['incremental'].get('unit') or {}
            if context['incremental']['phase'] == 'review' and unit.get('kind') == 'global':
                answer['checks'][0]['status'] = 'fail'

        case.mutate = omit
        self.assertEqual('needs-investigation', case.run_agent(agent)['status'])
        self.assertEqual([], agent.status()['acceptedRequirements'])
        self.assertEqual(1, len(agent.status()['candidates']))


if __name__ == '__main__':
    unittest.main()

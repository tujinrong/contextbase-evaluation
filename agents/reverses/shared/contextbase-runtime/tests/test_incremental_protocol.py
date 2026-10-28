"""Incremental pagination and continuation invariants using synthetic transport.

The source stub permits only empty evidence: these tests prove control/protocol
behavior, not source interpretation or independent business acceptance.
"""
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from contextbase_runtime import contracts as c, incremental, review_set
from contextbase_runtime.storage import ArtifactStore


class EmptySource:
    snapshot_id = 'a' * 64

    def __init__(self, root):
        self.root = root

    def verify_evidence_many(self, evidence):
        if evidence:
            raise AssertionError('Protocol fixture does not provide original source evidence')


class NoSourceAccess:
    def __init__(self, source, index, task):
        pass

    def handle(self, request):
        raise AssertionError('This protocol test must not issue a source request')


def root_task():
    obligation = {'id': 'catalog', 'stage': 'discovery', 'scope': 'system',
                  'question': 'Catalog source objects', 'requires': []}
    return {'id': 'root-task', 'contextId': 'root-context', 'executionEpoch': 0,
            'sessionId': 'protocol-session', 'operation': 'extract', 'stage': 'discovery',
            'origin': 'host-executed', 'snapshotId': EmptySource.snapshot_id,
            'baseVersion': 0, 'baseRevision': None, 'candidate': None, 'viewSha256': None,
            'feedback': None, 'goalRequirements': [obligation], 'goalRequirementIds': ['catalog'],
            'requirements': ['catalog'], 'authorizedSourcePaths': [], 'unknownBindings': [],
            'incrementalPolicy': incremental.VERSION, 'reviewSetPolicy': review_set.VERSION,
            'evidenceIndexSha256': 'b' * 64}


def root_context(task):
    return {'task': deepcopy(task),
            'request': {'schema': c.VERSION, 'projectId': 'protocol-fixture',
                        'goal': {'id': 'goal', 'question': 'Catalog',
                                 'requirements': deepcopy(task['goalRequirements'])},
                        'allowedPaths': ['.'], 'excludedPaths': []},
            'inventory': {'files': [], 'omitted': [], 'projectId': 'protocol-fixture'},
            'structure': {'indexSha256': task['evidenceIndexSha256'], 'counts': {}},
            'currentRecords': {}, 'currentUnknowns': {}}


def listing(*, offset=0, limit=100, collection='records'):
    return {'operation': 'listing', 'collection': collection, 'offset': offset, 'limit': limit}


def material(*, key='a', offset=0, limit=100, collection='records'):
    return {'operation': 'material', 'collection': collection, 'key': key,
            'offset': offset, 'limit': limit}


class MaterialProgressTests(unittest.TestCase):
    def setUp(self):
        self.child = {'id': 'child', 'contextId': 'child-context',
                      'snapshotId': EmptySource.snapshot_id}
        self.materials = incremental._collections([
            {'key': key, 'statement': 'text-' + key + '-' + 'x' * 200} for key in ('a', 'b', 'c')])
        self.progress = incremental._MaterialProgress()

    def consume(self, request):
        return self.progress.consume([{'request': request,
            'reply': incremental._material_reply(request, self.materials, self.child)}])

    def test_listing_changed_limit_or_overlapping_page_is_not_new_delivery(self):
        self.assertTrue(self.consume(listing(limit=2)))
        self.assertFalse(self.consume(listing(limit=1)))
        self.assertFalse(self.consume(listing(offset=1, limit=1)))
        self.assertFalse(self.consume(listing(limit=2)))
        self.assertTrue(self.consume(listing(offset=2, limit=1)))
        self.assertFalse(self.consume(listing(limit=100)))

    def test_repeated_character_intervals_and_split_pages_are_not_new_delivery(self):
        self.assertTrue(self.consume(material(offset=0, limit=60)))
        self.assertFalse(self.consume(material(offset=0, limit=10)))
        self.assertFalse(self.consume(material(offset=10, limit=30)))
        self.assertFalse(self.consume(material(offset=59, limit=1)))
        self.assertFalse(self.consume(material(offset=0, limit=60)))
        self.assertTrue(self.consume(material(offset=59, limit=2)))

    def test_character_interval_union_detects_real_gap_then_remembers_it(self):
        self.assertTrue(self.consume(material(offset=0, limit=10)))
        self.assertTrue(self.consume(material(offset=20, limit=10)))
        self.assertTrue(self.consume(material(offset=5, limit=20)))
        self.assertFalse(self.consume(material(offset=3, limit=26)))
        self.assertTrue(self.consume(material(offset=29, limit=2)))
        self.assertFalse(self.consume(material(offset=0, limit=31)))

    def test_empty_pages_do_not_reset_progress(self):
        self.assertFalse(self.consume(listing(offset=1000)))
        self.assertFalse(self.consume(material(offset=1000)))

    def test_material_pagination_rejects_json_integer_floats_before_python_slicing(self):
        requests = [listing(offset=1.0), listing(limit=1.0),
                    material(offset=1.0), material(limit=1.0)]
        for request in requests:
            with self.subTest(request=request), self.assertRaises(ValueError):
                incremental._material_reply(request, self.materials, self.child)

    def test_objects_versions_and_collections_have_distinct_delivery_identities(self):
        self.assertTrue(self.consume(listing(limit=1)))
        self.assertTrue(self.consume(material(limit=1)))
        self.assertFalse(self.consume(material(limit=1)))
        self.materials['units']['a'] = deepcopy(self.materials['records']['a'])
        self.assertTrue(self.consume(listing(limit=1, collection='units')))
        self.assertTrue(self.consume(material(limit=1, collection='units')))
        self.materials['records']['a']['statement'] = 'new content version'
        self.assertTrue(self.consume(listing(limit=1)))
        self.assertTrue(self.consume(material(limit=1)))


class IncrementalContinuationTests(unittest.TestCase):
    def setUp(self):
        temporary_root = Path(__file__).resolve().parents[1] / '.tmp'
        temporary_root.mkdir(exist_ok=True)
        self.temporary = tempfile.TemporaryDirectory(prefix='incremental-protocol-', dir=temporary_root)
        self.root = Path(self.temporary.name)
        self.store = ArtifactStore(self.root)
        self.source = EmptySource(self.root / 'sealed')
        self.task = root_task()
        self.context = root_context(self.task)
        self.materials = incremental._collections([
            {'key': key, 'statement': key + '-' + 'x' * 200} for key in ('a', 'b', 'c')])
        self.result_schema = c.obj({'value': c.TEXT})
        self.calls = []

    def tearDown(self):
        self.temporary.cleanup()

    def provider(self, requests=()):
        def execute(workspace, job, prompt, schema, timeout):
            context = json.loads(prompt.rsplit('\n', 1)[-1])
            self.calls.append(context)
            number = context['evidenceDialog']['round']
            wrapper = {'protocol': incremental.VERSION, 'taskId': context['task']['id'],
                       'action': 'finish', 'requests': [], 'answer': {'value': 'done'},
                       'workingNotes': ''}
            if number <= len(requests):
                wrapper.update(action='requests', requests=[requests[number - 1]], answer=None)
            return {'exit_code': 0, 'metadata': {'status': 'passed'}, 'answer': wrapper}
        return execute

    def dialog(self, *, provider=None, task=None, context=None, result_schema=None, cached=None):
        with patch('contextbase_runtime.incremental.EvidenceAccess', NoSourceAccess):
            return incremental._dialog(self.source, None, self.store, task or self.task,
                context or self.context, 'plan', None, self.materials, 'Synthetic unit instruction.',
                result_schema or self.result_schema, provider or self.provider(), 10, lambda: None, cached)

    def test_dialog_stops_on_third_listing_without_new_object_despite_changed_limits(self):
        requests = [listing(limit=2), listing(limit=1), listing(offset=1, limit=1), listing(limit=2)]
        with self.assertRaisesRegex(ValueError, 'no source, material or draft progress'):
            self.dialog(provider=self.provider(requests))
        self.assertEqual(4, len(self.calls))

    def test_dialog_stops_on_third_slice_without_new_characters(self):
        requests = [material(limit=60), material(limit=20), material(offset=20, limit=20),
                    material(offset=30, limit=30)]
        with self.assertRaisesRegex(ValueError, 'no source, material or draft progress'):
            self.dialog(provider=self.provider(requests))
        self.assertEqual(4, len(self.calls))

    def test_actual_new_character_resets_no_progress_before_phase_finish(self):
        requests = [material(limit=5), material(limit=3), material(offset=2, limit=2),
                    material(offset=4, limit=2)]
        answer, pointer = self.dialog(provider=self.provider(requests))
        self.assertEqual({'value': 'done'}, answer)
        self.assertEqual(5, len(self.calls))
        self.assertTrue(self.store.path('calls/' + pointer + '/complete.json').exists())

    def test_two_candidate_pages_can_be_compared_together_and_replayed_without_a_provider(self):
        expected = {key: incremental._json(self.materials['records'][key]) for key in ('a', 'b')}

        def provider(workspace, job, prompt, schema, timeout):
            context = json.loads(prompt.rsplit('\n', 1)[-1])
            self.calls.append(deepcopy(context))
            dialog = context['evidenceDialog']
            bodies = {row['key']: row['bodyText'] for row in dialog['retainedMaterials']
                      if row['kind'] == 'candidate-material' and row['collection'] == 'records'
                      and row['offset'] == 0}
            for pair in dialog['latestEvidence']:
                request, result = pair['request'], pair['reply']['result']
                if request['operation'] == 'material' and request['collection'] == 'records':
                    if result['offset'] == 0:
                        bodies[result['key']] = result['bodyText']
            if all(bodies.get(key) == value for key, value in expected.items()):
                action, requests, answer = 'finish', [], {'value': 'Compared a and b together'}
            else:
                if dialog['round'] == 1:
                    request = material(key='a', limit=12000)
                elif dialog['round'] == 2:
                    request = material(key='b', limit=12000)
                elif bodies.get('a') != expected['a']:
                    request = material(key='a', limit=12000)
                else:
                    # A listing confirms identity but cannot replace b's body.
                    request = listing(offset=1, limit=1)
                action, requests, answer = 'requests', [request], None
            return {'exit_code': 0, 'metadata': {'status': 'passed'}, 'answer': {
                'protocol': incremental.VERSION, 'taskId': context['task']['id'],
                'action': action, 'requests': requests, 'answer': answer, 'workingNotes': ''}}

        # Reproduce the old source-only window at the same provider seam: after
        # a -> b, a disappears and repeated a/listing(b) eventually stops.
        with patch('contextbase_runtime.incremental.collect_materials', return_value=([], [])):
            with self.assertRaisesRegex(ValueError, 'no source, material or draft progress'):
                self.dialog(provider=provider)
        self.assertGreater(len(self.calls), 3)
        self.calls.clear()

        answer, pointer = self.dialog(provider=provider)
        self.assertEqual({'value': 'Compared a and b together'}, answer)
        self.assertEqual(3, len(self.calls))
        self.assertTrue(any(row['key'] == 'a' and row['bodyText'] == expected['a']
                            for row in self.calls[-1]['evidenceDialog']['retainedMaterials']))
        self.assertEqual([], self.calls[-1]['evidenceDialog']['retainedEvidence'])

        def no_provider(*args, **kwargs):
            raise AssertionError('A completed two-page comparison must replay without model execution')

        rebuilt, reused = self.dialog(provider=no_provider, cached=pointer)
        self.assertEqual((answer, pointer), (rebuilt, reused))
        self.assertEqual(3, len(self.calls))

    def test_same_basis_continuation_keeps_original_child_identity_and_uses_no_provider(self):
        answer, pointer = self.dialog()
        resumed_task = {**deepcopy(self.task), 'id': 'continued-root',
                        'contextId': 'continued-context', 'executionEpoch': 9}
        resumed_context = {**deepcopy(self.context), 'task': resumed_task}
        before = len(self.calls)
        rebuilt, reused = self.dialog(task=resumed_task, context=resumed_context, cached=pointer)
        self.assertEqual((answer, pointer), (rebuilt, reused))
        self.assertEqual(before, len(self.calls))

    def test_cached_child_rejects_different_root_input_context_or_result_schema(self):
        _, pointer = self.dialog()
        changed_context = deepcopy(self.context)
        changed_context['request']['goal']['question'] = 'Different original question'
        with self.assertRaisesRegex(ValueError, 'binding changed'):
            self.dialog(context=changed_context, cached=pointer)
        different_schema = c.obj({'value': c.TEXT, 'extra': c.TEXT})
        with self.assertRaisesRegex(ValueError, 'binding changed'):
            self.dialog(result_schema=different_schema, cached=pointer)
        self.assertEqual(1, len(self.calls))

    def test_cached_child_rejects_other_snapshot_base_candidate_or_feedback_basis(self):
        _, pointer = self.dialog()
        for field, value in (('snapshotId', 'f' * 64), ('baseVersion', 2),
                             ('candidate', 'c' * 64), ('feedback', 'prior-candidate')):
            with self.subTest(field=field):
                changed = {**deepcopy(self.task), field: value}
                with self.assertRaisesRegex(ValueError, 'binding changed'):
                    self.dialog(task=changed, cached=pointer)
        self.assertEqual(1, len(self.calls))

    def test_composite_replay_rejects_root_context_substitution_even_with_new_digest(self):
        def provider(workspace, job, prompt, schema, timeout):
            context = json.loads(prompt.rsplit('\n', 1)[-1])
            phase = context['incremental']['phase']
            if phase == 'plan':
                answer = {'units': [{'id': 'one-unit', 'requirement': 'catalog',
                                     'question': 'Confirm the source scope', 'paths': []}]}
            elif phase == 'draft':
                answer = {'unitId': 'one-unit', 'records': [], 'expectedVersions': [], 'removals': [],
                          'unknowns': [], 'followups': [], 'factUsage': [],
                          'remainingQuestions': [], 'complete': True, 'addUnits': []}
            else:
                answer = {'requirement': 'catalog', 'status': 'unresolved',
                          'reason': 'No original evidence in this protocol fixture', 'evidence': []}
            return {'exit_code': 0, 'metadata': {'status': 'passed'}, 'answer': {
                'protocol': incremental.VERSION, 'taskId': context['task']['id'],
                'action': 'finish', 'requests': [], 'answer': answer, 'workingNotes': ''}}
        path = 'tasks/' + self.task['id'] + '/context.json'
        self.store.put(path, self.context)
        with patch('contextbase_runtime.incremental.EvidenceAccess', NoSourceAccess):
            result = incremental.run(self.source, None, self.store, self.task, self.context,
                                     'Synthetic root instruction.', provider, 10, lambda: None)
            manifest_path = 'tasks/' + self.task['id'] + '/incremental.json'
            manifest = self.store.get(manifest_path)
            manifest['context']['task']['id'] = 'forged-root'
            # A caller cannot substitute an unrelated root context merely by
            # recomputing its generic storage hash and providing its digest.
            self.store.path(manifest_path).write_text(json.dumps({
                'sha256': c.digest(manifest), 'payload': manifest}), encoding='utf-8')
            with self.assertRaises(ValueError):
                incremental.replay(self.source, None, self.store, self.task,
                                   result['answer'], c.digest(manifest))


if __name__ == '__main__':
    unittest.main()

"""Read-only custody import using a synthetic native-provider seam, never a model."""
from copy import deepcopy
import hashlib
import importlib.metadata
import inspect
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

from contextbase_discovery import DiscoveryAgent
from contextbase_runtime import amendment_seed, contracts, controller
from contextbase_runtime.evidence import EvidenceAccess
from contextbase_runtime.handoff import followup_question
from contextbase_runtime.incremental import POLICY
from contextbase_runtime.provider import COMMON_POLICY
from contextbase_runtime.storage import ArtifactStore
from test_independent_agents import request


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False), encoding='utf-8')


def overwrite_artifact(root, relative, payload):
    write_json(root / relative, {'sha256': contracts.digest(payload), 'payload': payload})


def seal(bundle, candidate, agent):
    files = {}
    for path in bundle.rglob('*'):
        if path.is_file() and path != bundle / 'custody.json':
            data = path.read_bytes()
            files[path.relative_to(bundle).as_posix()] = {
                'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data)}
    source, index = agent.session.source, agent.session.fact_index()
    manifest = {'schema': 'contextbase-candidate-custody/1', 'candidateSha256': candidate['id'],
                'viewSha256': ArtifactStore(bundle / 'origin').get('candidates/' + candidate['id'] + '.json')['viewSha256'],
                'sourceSnapshotId': source.snapshot_id, 'sourceFactsSha256': index.sha256,
                'requestSha256': contracts.digest(request()), 'engineSha256': controller.engine_fingerprint(),
                'agentBindingSha256': contracts.digest(agent.binding()), 'originDirectory': 'origin',
                'dependencies': {name: importlib.metadata.version(name) for name in
                                 ('jsonschema', 'tree-sitter', 'tree-sitter-c-sharp', 'tree-sitter-java')},
                'files': files, 'exportCheck': {'authorSourceCustodyReplayed': True}}
    write_json(bundle / 'custody.json', manifest)


class AmendmentSeedTests(unittest.TestCase):
    def setUp(self):
        temporary_root = Path(__file__).resolve().parents[1] / '.tmp'
        temporary_root.mkdir(exist_ok=True)
        self.temporary = tempfile.TemporaryDirectory(prefix='amendment-seed-', dir=temporary_root)
        self.root = Path(self.temporary.name)
        source = self.root / 'source'
        source.mkdir()
        (source / 'README.md').write_text('Synthetic source material.\nSecond line.\n', encoding='utf-8')
        self.agent = DiscoveryAgent.create(source, self.root / 'old', request(), incremental_mode=True)
        self.base_has_followup = True
        with patch('contextbase_runtime.provider.run_job', side_effect=self.provider):
            first = self.agent.session.execute('discovery')
        task = self.agent.session.prepare_verification(first['id'])
        question = self.agent.session.store.get('candidates/' + first['id'] + '.json')['view']['unknowns']
        ref = self.ref()
        answer = {'taskId': task['id'], 'candidateSha256': first['id'], 'viewSha256': task['viewSha256'],
                  'checks': [{'requirement': 'catalog', 'status': 'fail', 'reason': 'Synthetic finding.',
                              'evidence': [ref]}], 'unknownChecks': [
                      {'unknownId': row['id'], 'unknownSha256': row['sha256'], 'status': 'non-blocking',
                       'blocksRequirements': [], 'reason': 'Future work.', 'evidence': [ref]}
                      for row in question.values()],
                  'findings': [{'id': 'inspect-material', 'severity': 'blocking', 'requirement': 'catalog',
                                'detail': 'Synthetic issue, not a real verifier.', 'evidence': [ref]}],
                  'unknowns': [], 'classificationChecks': [], 'scopeChecks': [
                      {'scope': 'registration', 'status': 'fail', 'reason': 'Synthetic gap.', 'evidence': [ref]}],
                  'sourceFactsSha256': self.agent.session.fact_index().sha256,
                  'factUsageCheck': {'status': 'fail', 'reason': 'Synthetic gap.', 'evidence': [ref]}}
        verification = self.agent.session.submit(task['id'], answer)
        self.verification_id = verification['id']
        self.base_has_followup = False
        with patch('contextbase_runtime.provider.run_job', side_effect=self.provider):
            self.candidate = self.agent.session.execute('discovery', feedback=first['id'])
            # A resumed same-basis run legitimately reuses completed children
            # whose rootTaskId remains their original author task.
            self.candidate = self.agent.session.execute('discovery', feedback=first['id'])
        self.bundle = self.root / 'bundle'
        shutil.copytree(self.agent.work, self.bundle / 'origin')
        toolchain = self.bundle / 'toolchain'
        toolchain.mkdir()
        for path in Path(controller.__file__).parent.glob('*.py'):
            shutil.copy2(path, toolchain / path.name)
        for name in ('analysis_instructions.md', 'verification_instructions.md',
                     'native_analysis_instructions.md', 'native_verification_instructions.md'):
            shutil.copy2(Path(controller.__file__).with_name(name), toolchain / name)
        shutil.copy2(inspect.getfile(DiscoveryAgent), toolchain / 'discovery_implementation.py')
        seal(self.bundle, self.candidate, self.agent)

    def tearDown(self):
        self.temporary.cleanup()

    def ref(self):
        row = self.agent.session.source.manifest['files'][0]
        return {'path': row['path'], 'startLine': 1, 'endLine': 2, 'sha256': row['sha256']}

    def provider(self, workspace, job, prompt, schema, timeout, *, instruction_role='analysis'):
        context = json.loads(prompt[prompt.index('{'):])
        task, phase = context['task'], context['incremental']['phase']
        wrapper = {'protocol': 'contextbase-incremental/1', 'taskId': task['id'],
                   'action': 'requests', 'requests': [], 'answer': None, 'workingNotes': ''}
        if context['evidenceDialog']['round'] == 1:
            wrapper['requests'] = [{'operation': 'read', 'path': 'README.md', 'startLine': 1, 'endLine': 2}]
        else:
            if phase == 'plan':
                answer = {'units': [{'id': 'material-unit', 'requirement': 'catalog',
                                     'question': 'Inspect source material.', 'paths': ['README.md']}]}
            elif phase == 'draft':
                record = {'key': 'material', 'kind': 'material', 'ownerRequirement': 'catalog',
                          'name': 'Synthetic material', 'statement': 'Synthetic source claim.',
                          'basis': 'observed-source', 'evidence': [self.ref()],
                          'dependsOn': [], 'classification': None}
                followups = [{'stage': 'relationship', 'question': 'Inspect future relations.',
                              'paths': ['README.md'], 'requirement': 'links'}] if self.base_has_followup else []
                answer = {'unitId': 'material-unit', 'records': [record], 'expectedVersions': [],
                          'removals': [], 'unknowns': [], 'followups': followups,
                          'factUsage': [{'recordKey': 'material', 'factIds': [], 'reason': 'Plain text.'}],
                          'remainingQuestions': [], 'complete': True, 'addUnits': []}
            else:
                answer = {'requirement': 'catalog', 'status': 'supported',
                          'reason': 'Synthetic scope claim.', 'evidence': [self.ref()]}
            wrapper.update(action='finish', answer=answer)
        job.mkdir(parents=True)
        data = (COMMON_POLICY + '\nUser task (within that boundary):\n' + prompt).encode('utf-8')
        answer_bytes = json.dumps(wrapper, ensure_ascii=False).encode('utf-8')
        (job / 'prompt.txt').write_bytes(data)
        (job / 'answer.txt').write_bytes(answer_bytes)
        write_json(job / 'schema.json', schema)
        result = {'exit_code': 0, 'answer': wrapper, 'metadata': {'status': 'passed',
                  'prompt_sha256': hashlib.sha256(data).hexdigest(),
                  'answer_sha256': hashlib.sha256(answer_bytes).hexdigest(),
                  'syntheticProvider': True}}
        write_json(job / 'result.json', result)
        return result

    def load(self, **changes):
        arguments = {'bundle': self.bundle, 'source': self.agent.session.source,
                     'index': self.agent.session.fact_index(), 'request': request(),
                     'verification_id': self.verification_id}
        arguments.update(changes)
        return amendment_seed.load_bundle(**arguments)

    def test_load_rebuilds_author_chain_and_preserves_inherited_followup(self):
        before = {path.relative_to(self.bundle).as_posix(): path.read_bytes()
                  for path in self.bundle.rglob('*') if path.is_file()}
        seed = self.load()
        self.assertEqual(self.candidate['id'], seed['baseCandidateSha256'])
        self.assertEqual([], seed['answer']['followups'])
        self.assertEqual(1, len(seed['followups']))
        question = followup_question(seed['followups'][0], ['catalog'])
        self.assertEqual(question, seed['view']['unknowns'][question['id']])
        self.assertEqual(self.verification_id + ':inspect-material', seed['issues'][0]['id'])
        self.assertEqual(before, {path.relative_to(self.bundle).as_posix(): path.read_bytes()
                                  for path in self.bundle.rglob('*') if path.is_file()})

    def test_semantic_origin_requires_a_new_custody_contract(self):
        store = ArtifactStore(self.bundle / 'origin')
        config = store.get('session.json')
        config['semanticOptions'] = {'schema': 'contextbase-semantic-evidence/1',
                                    'project': 'Example.csproj', 'configuration': 'Release'}
        overwrite_artifact(store.root, 'session.json', config)
        seal(self.bundle, self.candidate, self.agent)
        with self.assertRaisesRegex(ValueError, 'Semantic-session custody import is not supported'):
            self.load()

    def test_install_requires_fresh_discovery_work_and_inherits_no_receipts(self):
        fresh = DiscoveryAgent.create(self.root / 'source', self.root / 'fresh', request(), incremental_mode=True)
        seed, spec = amendment_seed.install(fresh, self.bundle, self.verification_id,
                                            replace_keys=['material'], add_kinds=['material'])
        self.assertEqual(seed, fresh.session.store.get('amendment-seed.json'))
        self.assertEqual(spec, fresh.session.store.get('amendment-spec.json'))
        self.assertEqual(contracts.digest(seed), spec['seedSha256'])
        state = fresh.session.store.get('state.json')
        self.assertEqual([], state['candidates'])
        self.assertEqual([], state['verifications'])
        self.assertEqual([], state['acceptedRequirements'])
        with self.assertRaises(ValueError):
            amendment_seed.install(self.agent, self.bundle, self.verification_id,
                                   replace_keys=['material'], add_kinds=['material'])
        with self.assertRaises(ValueError):
            amendment_seed.install(fresh, self.bundle, self.verification_id,
                                   replace_keys=[], add_kinds=[])

    def test_selected_verifier_answer_cannot_silently_name_another_candidate(self):
        store = ArtifactStore(self.bundle / 'origin')
        verification = store.get('verifications/' + self.verification_id + '.json')
        verification['answer']['candidateSha256'] = '0' * 64
        changed_id = contracts.digest(verification)
        store.put('verifications/' + changed_id + '.json', verification)
        state = store.get('state.json')
        state['verifications'].append(changed_id)
        overwrite_artifact(store.root, 'state.json', state)
        seal(self.bundle, self.candidate, self.agent)
        with self.assertRaises(ValueError):
            self.load(verification_id=changed_id)

    def test_base_view_cannot_change_the_source_author_record_even_when_resealed(self):
        store = ArtifactStore(self.bundle / 'origin')
        candidate = store.get('candidates/' + self.candidate['id'] + '.json')
        frozen = candidate['view']['records']['material']
        frozen['statement'] = 'A different host-manufactured claim.'
        frozen['version'] = contracts.digest({key: value for key, value in frozen.items()
                                               if key not in {'id', 'version'}})
        candidate['viewSha256'] = contracts.digest(candidate['view'])
        changed_id = contracts.digest(candidate)
        store.put('candidates/' + changed_id + '.json', candidate)
        state = store.get('state.json')
        state['candidates'].append(changed_id)
        overwrite_artifact(store.root, 'state.json', state)
        seal(self.bundle, {'id': changed_id}, self.agent)
        with self.assertRaises(ValueError):
            self.load()

    def test_resealed_fake_custody_flags_do_not_replace_actual_original_delivery(self):
        store = ArtifactStore(self.bundle / 'origin')
        candidate = store.get('candidates/' + self.candidate['id'] + '.json')
        manifest = store.get('tasks/' + candidate['taskId'] + '/incremental.json')
        work = ArtifactStore(store.path(manifest['workflow']))
        call = next(key for key in manifest['trace']
                    if work.get('calls/' + key + '/setup.json')['phase'] == 'draft')
        prefix = 'calls/' + call
        setup, complete = work.get(prefix + '/setup.json'), work.get(prefix + '/complete.json')
        request_value = {'operation': 'inventory', 'offset': 0, 'limit': 100}
        access = EvidenceAccess(self.agent.session.source, self.agent.session.fact_index(), setup['task'])
        replacement = {'request': request_value, 'reply': access.handle(request_value)}
        previous, pointers = contracts.digest(setup), []
        for number in range(1, len(complete['rounds']) + 1):
            relative = prefix + f'/round-{number:04d}'
            row = work.get(relative + '.json')
            row['previousSha256'] = previous
            if number == 1:
                row['response']['answer']['requests'] = [request_value]
                row['pairs'] = [replacement]
            else:
                dialog = row['context']['evidenceDialog']
                dialog['latestEvidence'] = [replacement]
                dialog['deliveryLedger'] = [{'request': request_value,
                                             'replySha256': replacement['reply']['replySha256']}]
            context_json = json.dumps(row['context'], sort_keys=True, ensure_ascii=False, separators=(',', ':'))
            prompt = setup['instruction'] + '\n' + POLICY + '\n' + context_json
            raw_prompt = (COMMON_POLICY + '\nUser task (within that boundary):\n' + prompt).encode('utf-8')
            raw_answer = json.dumps(row['response']['answer'], ensure_ascii=False).encode('utf-8')
            row['promptSha256'] = hashlib.sha256(prompt.encode('utf-8')).hexdigest()
            row['response']['metadata'].update(prompt_sha256=hashlib.sha256(raw_prompt).hexdigest(),
                                                answer_sha256=hashlib.sha256(raw_answer).hexdigest())
            job = work.path(prefix + f'/provider/round-{number:04d}')
            (job / 'prompt.txt').write_bytes(raw_prompt)
            (job / 'answer.txt').write_bytes(raw_answer)
            write_json(job / 'result.json', row['response'])
            overwrite_artifact(work.root, relative + '-response.json', row['response'])
            overwrite_artifact(work.root, relative + '.json', row)
            previous = contracts.digest(row)
            pointers.append(previous)
        complete['rounds'] = pointers
        overwrite_artifact(work.root, prefix + '/complete.json', complete)
        seal(self.bundle, self.candidate, self.agent)
        with self.assertRaisesRegex(ValueError, 'not supplied as original text'):
            self.load()

    def test_inventory_source_envelope_and_toolchain_tampering_are_rejected(self):
        extra = self.bundle / 'unexpected.txt'
        extra.write_text('Unlisted data.', encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'inventory'):
            self.load()
        extra.unlink()
        original = self.bundle / 'origin/snapshot/sources/README.md'
        content = original.read_bytes()
        original.write_bytes(content + b'Tampered source.\n')
        with self.assertRaisesRegex(ValueError, 'inventory'):
            self.load()
        seal(self.bundle, self.candidate, self.agent)
        with self.assertRaises(ValueError):
            self.load()
        original.write_bytes(content)
        state_path = self.bundle / 'origin/state.json'
        state_bytes = state_path.read_bytes()
        state = json.loads(state_bytes)
        state['payload']['stopReason'] = 'Tampered without updating artifact seal.'
        write_json(state_path, state)
        seal(self.bundle, self.candidate, self.agent)
        with self.assertRaisesRegex(ValueError, 'integrity mismatch'):
            self.load()
        state_path.write_bytes(state_bytes)
        tool = self.bundle / 'toolchain/contracts.py'
        tool.write_bytes(tool.read_bytes() + b'\n# Changed archived rules.\n')
        seal(self.bundle, self.candidate, self.agent)
        with self.assertRaisesRegex(ValueError, 'engine/dependency'):
            self.load()

    def test_finding_selection_and_current_request_must_match_the_original_scope(self):
        for identifiers in [[], ['absent'], ['inspect-material', 'inspect-material']]:
            with self.subTest(identifiers=identifiers), self.assertRaises(ValueError):
                self.load(finding_ids=identifiers)
        changed_request = request()
        changed_request['goal']['requirements'][0]['scope'] = 'other-scope'
        with self.assertRaises(ValueError):
            self.load(request=changed_request)

    def test_resealed_bundle_missing_raw_provider_prompt_is_not_importable(self):
        store = ArtifactStore(self.bundle / 'origin')
        candidate = store.get('candidates/' + self.candidate['id'] + '.json')
        manifest = store.get('tasks/' + candidate['taskId'] + '/incremental.json')
        prompt = store.path(manifest['workflow'] + '/calls/' + manifest['trace'][0]
                            + '/provider/round-0001/prompt.txt')
        prompt.unlink()
        seal(self.bundle, self.candidate, self.agent)
        with self.assertRaises(ValueError):
            self.load()

    def test_inspection_checks_exact_bytes_without_promoting_export_check_flags(self):
        manifest = json.loads((self.bundle / 'custody.json').read_text(encoding='utf-8'))
        manifest['exportCheck']['authorSourceCustodyReplayed'] = False
        write_json(self.bundle / 'custody.json', manifest)
        inspected = amendment_seed.inspect_bundle(self.bundle)
        self.assertFalse(inspected['exportCheck']['authorSourceCustodyReplayed'])
        original = self.bundle / 'origin/snapshot/sources/README.md'
        original.write_bytes(original.read_bytes() + b'Damaged input.')
        with self.assertRaisesRegex(ValueError, 'inventory'):
            amendment_seed.inspect_bundle(self.bundle)


if __name__ == '__main__':
    unittest.main()

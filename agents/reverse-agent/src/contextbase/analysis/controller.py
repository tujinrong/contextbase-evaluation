"""Host-owned three-stage analysis with independent, content-bound verification."""
from __future__ import annotations

from copy import deepcopy
import importlib.metadata
import json
import math
from pathlib import Path
import time
import uuid

from ..ai.capsule import safe_path
from . import contracts
from .agents import AGENTS, POLICY, VERIFICATION
from .sources import SourceAccess, source_lines
from .storage import ArtifactStore


class AcceptanceError(ValueError):
    """A valid candidate remains partial until its verification obligations pass."""


def engine_fingerprint() -> str:
    files = {name: Path(__file__).with_name(name).read_text(encoding='utf-8')
             for name in ('agents.py', 'contracts.py', 'controller.py', 'storage.py',
                          'sources.py', 'adapters.py')}
    versions = {}
    for package in ('jsonschema', 'tree-sitter', 'tree-sitter-c-sharp', 'tree-sitter-java'):
        try:
            versions[package] = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            versions[package] = None
    return contracts.digest({'files': files, 'dependencies': versions})


class Session:
    def __init__(self, work: Path):
        self.store = ArtifactStore(work)
        self.config = self.store.get('session.json')
        if self.config.get('schema') != contracts.VERSION:
            raise ValueError('Legacy analysis session is preserved but cannot be auto-migrated; '
                             'create a new v2 session with explicit stages, scopes and prerequisites')
        contracts.validate_request(self.config['request'])
        self.source = SourceAccess.open(self.store.path('snapshot'))
        if self.source.snapshot_id != self.config['snapshotId']:
            raise ValueError('Session source binding changed')
        self._state()

    @classmethod
    def create(cls, source: Path, work: Path, request: dict) -> 'Session':
        contracts.validate_request(request)
        source, work = safe_path(source), safe_path(work)
        if source == work or source in work.parents or work in source.parents:
            raise ValueError('Session and source trees must be disjoint')
        if work.exists():
            raise ValueError('Analysis session requires a fresh work directory')
        work.mkdir(parents=True)
        store = ArtifactStore(work)
        access = SourceAccess.create(source, work / 'snapshot', project_id=request['projectId'],
                                     allowed_paths=request['allowedPaths'], excluded_paths=request['excludedPaths'])
        config = {'schema': contracts.VERSION, 'id': uuid.uuid4().hex,
                  'engineSha256': engine_fingerprint(), 'snapshotId': access.snapshot_id,
                  'request': deepcopy(request)}
        store.put('session.json', config)
        store.save_state({'sessionSha256': contracts.digest(config), 'version': 0, 'revision': None,
                          'status': 'active', 'executionEpoch': 0, 'acceptedRequirements': [],
                          'invalidatedRequirements': {}, 'tasks': {}, 'candidates': [],
                          'verifications': [], 'attempts': {}, 'stopReason': None})
        return cls(work)

    @classmethod
    def open(cls, work: Path) -> 'Session':
        return cls(work)

    @property
    def obligations(self) -> dict:
        return {item['id']: item for item in self.config['request']['goal']['requirements']}

    def _ordered(self, identifiers) -> list[str]:
        wanted = set(identifiers)
        return [key for key in self.obligations if key in wanted]

    def _state(self) -> dict:
        if self.config.get('engineSha256') != engine_fingerprint():
            raise ValueError('Extraction rules or dependencies changed; use a new analysis session')
        if self.store.get('session.json') != self.config:
            raise ValueError('Session configuration changed during execution')
        state = self.store.get('state.json')
        if state['sessionSha256'] != contracts.digest(self.config):
            raise ValueError('Session request or contract changed')
        if state['revision']:
            revision = self.store.get('revisions/' + state['revision'] + '.json')
            if (contracts.digest(revision) != state['revision']
                    or revision['version'] != state['version']
                    or revision['snapshotId'] != self.source.snapshot_id
                    or revision['acceptedRequirements'] != state['acceptedRequirements']
                    or revision['invalidatedRequirements'] != state['invalidatedRequirements']):
                raise ValueError('Revision and acceptance pointer disagree')
            self._validate_records(revision['records'])
            if set(revision['receipts']) != set(state['acceptedRequirements']):
                raise ValueError('Adopted requirement receipts disagree')
            for key, receipt in revision['receipts'].items():
                if set(receipt['requires']) != set(self.obligations[key]['requires']):
                    raise ValueError('Requirement prerequisite binding changed')
                if any(dep not in revision['receipts'] or
                       revision['receipts'][dep]['contentSha256'] != version
                       for dep, version in receipt['requires'].items()):
                    raise ValueError('Requirement prerequisite receipt is stale')
        return state

    def _current(self, state) -> dict:
        if not state['revision']:
            return {'records': {}, 'unknowns': {}, 'receipts': {}, 'identities': {}}
        return self.store.get('revisions/' + state['revision'] + '.json')

    def _select(self, identifiers, stage=None) -> list[str]:
        if identifiers is None:
            identifiers = [key for key, item in self.obligations.items()
                           if stage is None or item['stage'] == stage]
        identifiers = list(identifiers)
        if (not identifiers or len(identifiers) != len(set(identifiers))
                or not set(identifiers).issubset(self.obligations)):
            raise ValueError('Requirements must be a nonempty subset of the original goal')
        if stage and any(self.obligations[key]['stage'] != stage for key in identifiers):
            raise ValueError('Task obligations belong to a different stage')
        return self._ordered(identifiers)

    def status(self) -> dict:
        self.source.verify()
        state = self._state()
        current = self._current(state)
        accepted = set(state['acceptedRequirements'])
        return {**deepcopy(state), 'schema': contracts.VERSION,
                'projectId': self.config['request']['projectId'], 'snapshotId': self.source.snapshot_id,
                'remainingRequirements': self._ordered(set(self.obligations) - accepted),
                'readyRequirements': [key for key, item in self.obligations.items()
                                      if key not in accepted and set(item['requires']).issubset(accepted)],
                'records': deepcopy(current['records']), 'unknowns': deepcopy(current['unknowns']),
                'receipts': deepcopy(current['receipts'])}

    def index(self) -> list[dict]:
        from .adapters import index_source_isolated
        return [index_source_isolated(entry['path'], self.source.read(entry['path']),
                                      source_sha256=entry['sha256'])
                for entry in self.source.manifest['files']]

    def _structure_context(self) -> dict:
        indexes = self.index()
        identifier = contracts.digest({'files': indexes})
        self.store.put('indexes/' + identifier + '.json', {'files': indexes})
        files = []
        for item in indexes:
            view = {key: deepcopy(item[key]) for key in
                    ('path', 'language', 'status', 'backend', 'capabilities', 'diagnostics', 'imports')}
            view['symbols'] = [{key: symbol[key] for key in
                                ('id', 'kind', 'name', 'scope', 'signature', 'startLine', 'endLine')}
                               for symbol in item['symbols']]
            view['callSiteCount'] = len(item['calls'])
            files.append(view)
        return {'indexSha256': identifier, 'files': files,
                'sourceAccess': 'Read sources/<path> for behavior. Calls remain unresolved syntax candidates.'}

    def _validate_records(self, records):
        for key, record in records.items():
            body = {k: v for k, v in record.items() if k not in {'id', 'version'}}
            if record['key'] != key or record['version'] != contracts.digest(body):
                raise ValueError('Record content version changed: ' + key)
            for dep in record['dependencies']:
                if dep['key'] not in records or records[dep['key']]['version'] != dep['version']:
                    raise ValueError('Record dependency version is stale: ' + key)

    def _affected(self, current, seeds) -> set[str]:
        affected = set(seeds)
        while True:
            grown = affected | {key for key, item in self.obligations.items()
                                if set(item['requires']) & affected}
            changed_keys = {key for key, record in current['records'].items()
                            if record['ownerRequirement'] in affected}
            grown |= {record['ownerRequirement'] for record in current['records'].values()
                      if any(dep['key'] in changed_keys for dep in record['dependencies'])}
            if grown == affected:
                return affected
            affected = grown

    def _proposal_hash(self, answer, identifier) -> str:
        return contracts.digest({
            'records': sorted((record for record in answer['records']
                               if record['ownerRequirement'] == identifier), key=lambda r: r['key']),
            'coverage': next(item for item in answer['coverage'] if item['requirement'] == identifier),
            'unknowns': sorted(answer['unknowns'], key=lambda item: item['id']),
            'followups': answer['followups']})

    def _proposal_view(self, state, task, answer) -> dict:
        current = self._current(state)
        assigned = set(task['requirements'])
        hashes = {key: self._proposal_hash(answer, key) for key in assigned}
        changed = {key for key in assigned if key in current['receipts']
                   and current['receipts'][key]['contentSha256'] != hashes[key]}
        invalidated = (self._affected(current, changed) - assigned) & set(state['acceptedRequirements'])
        retained = set(state['acceptedRequirements']) - assigned - invalidated
        records = {key: deepcopy(record) for key, record in current['records'].items()
                   if record['ownerRequirement'] in retained}
        incoming = {record['key']: record for record in answer['records']}
        for key, record in incoming.items():
            identity = current['identities'].get(key)
            if identity and (identity['ownerRequirement'] != record['ownerRequirement']
                             or identity['kind'] != record['kind']):
                raise ValueError('A stable record key cannot change owner or kind: ' + key)
        visiting = set()

        def materialize(key):
            if key in records:
                return records[key]
            if key not in incoming:
                raise ValueError('Record dependency is invalidated, removed or unknown: ' + key)
            if key in visiting:
                raise ValueError('Cyclic record dependency: ' + key)
            visiting.add(key)
            record = deepcopy(incoming[key])
            owner = record['ownerRequirement']
            dependencies = []
            for dep_key in record['dependsOn']:
                dep = materialize(dep_key)
                if self.obligations[dep['ownerRequirement']]['scope'] != self.obligations[owner]['scope']:
                    raise ValueError('Record dependency must belong to the same scope')
                dependencies.append({'key': dep_key, 'version': dep['version']})
            visiting.remove(key)
            body = {**record, 'dependencies': dependencies}
            result = {**body, 'id': contracts.record_id(self.config['request']['projectId'], record['kind'], key),
                      'version': contracts.digest(body)}
            records[key] = result
            return result

        # A local dependency may already have been built; distinguish it from
        # an existing retained record collision before traversal.
        retained_keys = set(records)
        if retained_keys & set(incoming):
            raise ValueError('Record key belongs to another requirement')
        for key in incoming:
            if key not in records:
                materialize(key)
        for coverage in answer['coverage']:
            for key in coverage['recordKeys']:
                if key not in records:
                    raise ValueError('Coverage refers to an invalidated or removed record')
                if (self.obligations[records[key]['ownerRequirement']]['scope']
                        != self.obligations[coverage['requirement']]['scope']):
                    raise ValueError('Coverage record must belong to the same scope')
        # Verify unchanged descendants still refer to exactly the same versions.
        self._validate_records(records)
        unknowns = {}
        for key, item in current['unknowns'].items():
            # Open questions outlive the records/owners that first found them.
            # Replacing an author response must not silently resolve a blocker.
            unknowns[key] = {field: deepcopy(item[field]) for field in
                             ('id', 'sha256', 'content', 'owners')}
        for item in answer['unknowns']:
            key = task['id'] + ':' + item['id']
            unknowns[key] = {'id': key, 'sha256': contracts.digest(item),
                             'content': deepcopy(item), 'owners': list(task['requirements'])}
        return {'records': records, 'unknowns': unknowns,
                'acceptedRequirements': self._ordered(retained | assigned),
                'invalidatedRequirements': self._ordered(invalidated),
                'contentHashes': hashes}

    def _prepare(self, stage, operation, requirements, candidate, origin, feedback=None) -> dict:
        if stage not in contracts.STAGES:
            raise ValueError('Unknown extraction stage; v1 investigation/review are not stage aliases')
        self.source.verify()
        self._state()
        with self.store.transaction() as state:
            if state['status'] != 'active':
                raise ValueError('Session is not active; explicitly revise adopted obligations to reopen a completed session')
            current = self._current(state)
            view = None
            if operation == 'verify':
                if candidate not in state['candidates']:
                    raise ValueError('Verification requires a known candidate')
                proposal = self.store.get('candidates/' + candidate + '.json')
                if proposal['stage'] != stage:
                    raise ValueError('Verification stage disagrees with candidate')
                if proposal['baseVersion'] != state['version'] or proposal['baseRevision'] != state['revision']:
                    raise ValueError('Candidate belongs to an obsolete base version')
                author_task = self.store.get('tasks/' + proposal['taskId'] + '/request.json')
                view = self._proposal_view(state, author_task, proposal['answer'])
                if contracts.digest(view) != proposal['viewSha256']:
                    raise ValueError('Candidate verification view changed')
                ids = view['acceptedRequirements']
            else:
                ids = self._select(requirements, stage)
                missing = {dep for key in ids for dep in self.obligations[key]['requires']
                           if dep not in state['acceptedRequirements']}
                if missing:
                    raise ValueError('Stage requires independently verified prerequisites: ' + ', '.join(sorted(missing)))
                if feedback is not None:
                    if feedback not in state['candidates']:
                        raise ValueError('Feedback requires a known candidate from this session')
                    prior = self.store.get('candidates/' + feedback + '.json')
                    scopes = {self.obligations[key]['scope'] for key in ids}
                    if not {self.obligations[key]['scope'] for key in prior['requirements']}.issubset(scopes):
                        raise ValueError('Feedback belongs to another scope')
            task = {'schema': contracts.VERSION, 'id': uuid.uuid4().hex, 'contextId': uuid.uuid4().hex,
                    'sessionId': self.config['id'], 'stage': stage, 'operation': operation, 'origin': origin,
                    'executionEpoch': state['executionEpoch'], 'snapshotId': self.source.snapshot_id,
                    'baseVersion': state['version'], 'baseRevision': state['revision'],
                    'goalSha256': contracts.digest(self.config['request']['goal']),
                    'goalRequirementIds': list(self.obligations),
                    'goalRequirements': deepcopy(list(self.obligations.values())),
                    'requirements': ids, 'candidate': candidate, 'feedback': feedback,
                    'viewSha256': contracts.digest(view) if view else None,
                    'invalidatedRequirements': view['invalidatedRequirements'] if view else [],
                    'unknownBindings': [{'id': item['id'], 'sha256': item['sha256']}
                                        for item in view['unknowns'].values()] if view else [],
                    'prerequisites': {dep: deepcopy(current['receipts'][dep])
                                      for key in ids for dep in self.obligations[key]['requires']
                                      if dep in current['receipts']}}
            self.store.put('tasks/' + task['id'] + '/request.json', task)
            state['tasks'][task['id']] = 'issued'
            self.store.save_state(state)
        return task

    def prepare(self, stage, *, requirements=None, feedback=None) -> dict:
        return self._prepare(stage, 'extract', requirements, None, 'manual-unverified', feedback)

    def prepare_verification(self, candidate) -> dict:
        proposal = self.store.get('candidates/' + candidate + '.json')
        return self._prepare(proposal['stage'], 'verify', None, candidate, 'manual-unverified')

    def _record(self, task, answer, provenance):
        self.source.verify()
        self._state()
        with self.store.transaction() as state:
            if state['tasks'].get(task['id']) != 'issued' or task['executionEpoch'] != state['executionEpoch']:
                raise ValueError('Task has already finished or was never issued in the active epoch')
            if (task['sessionId'] != self.config['id'] or task['snapshotId'] != self.source.snapshot_id
                    or task['goalSha256'] != contracts.digest(self.config['request']['goal'])
                    or state['status'] != 'active' or state['version'] != task['baseVersion']
                    or state['revision'] != task['baseRevision']):
                raise ValueError('Task is cancelled or its base version is obsolete')
            contracts.validate_result(answer, task, self.source, self._current(state)['records'])
            payload = {key: deepcopy(task[key]) for key in
                       ('schema', 'sessionId', 'stage', 'operation', 'baseVersion', 'baseRevision',
                        'snapshotId', 'goalSha256', 'requirements', 'candidate', 'feedback')}
            payload.update(taskId=task['id'], contextId=task['contextId'],
                           answer=deepcopy(answer), provenance=deepcopy(provenance))
            if task['operation'] == 'extract':
                view = self._proposal_view(state, task, answer)
                payload.update(view=view, viewSha256=contracts.digest(view))
            else:
                payload.update(viewSha256=task['viewSha256'],
                               invalidatedRequirements=task['invalidatedRequirements'])
            identifier = contracts.digest(payload)
            folder = 'verifications' if task['operation'] == 'verify' else 'candidates'
            self.store.put(folder + '/' + identifier + '.json', payload)
            state[folder].append(identifier)
            state['tasks'][task['id']] = 'finished'
            self.store.save_state(state)
        return {'id': identifier, 'stage': task['stage'], 'operation': task['operation'],
                'accepted': False, 'origin': task['origin'], 'result': deepcopy(answer)}

    def submit(self, task_id, answer):
        if task_id not in self._state()['tasks']:
            raise ValueError('Unknown task ID')
        task = self.store.get('tasks/' + task_id + '/request.json')
        if task['origin'] != 'manual-unverified':
            raise ValueError('Provider task submissions are owned by the host')
        return self._record(task, answer, {'kind': 'manual-unverified', 'independenceVerified': False})

    def _context(self, task, inline_sources):
        state = self._state()
        context = {'request': self.config['request'], 'task': task,
                   'inventory': self.source.manifest, 'structure': self._structure_context(),
                   'currentRecords': self._current(state)['records']}
        if task['operation'] == 'extract':
            notes = []
            candidates = {receipt['candidate'] for receipt in self._current(state)['receipts'].values()}
            for identifier in sorted(candidates):
                prior = self.store.get('candidates/' + identifier + '.json')
                notes.extend(deepcopy(note) for note in prior['answer']['followups']
                             if note['stage'] == task['stage'] and note['requirement'] in task['requirements'])
            context['handoffQuestions'] = notes
        if task['operation'] == 'verify':
            proposal = self.store.get('candidates/' + task['candidate'] + '.json')
            context.update(candidate=proposal, verificationView=proposal['view'])
        if task['feedback']:
            prior = self.store.get('candidates/' + task['feedback'] + '.json')
            context['feedback'] = {'candidate': prior, 'verifications': [
                self.store.get('verifications/' + key + '.json') for key in state['verifications']
                if self.store.get('verifications/' + key + '.json')['candidate'] == task['feedback']]}
        if inline_sources:
            if sum(entry['bytes'] for entry in self.source.manifest['files']) > 1_048_576:
                raise ValueError('Inline source scope exceeds 1 MiB; choose a smaller explicit scope')
            originals = []
            for entry in self.source.manifest['files']:
                text = self.source.read(entry['path'])
                numbered = '\n'.join(f'{number}: ' + line.removesuffix('\n').removesuffix('\r')
                                     for number, line in enumerate(source_lines(text), 1))
                originals.append({'path': entry['path'], 'sha256': entry['sha256'],
                                  'sourceText': text, 'numberedText': numbered})
            context['sourceDelivery'] = {'mode': 'complete-numbered-originals',
                'instruction': 'sourceText preserves the decoded original including delimiters. '
                               'numberedText is only a display aid. No source lookup or shell is needed.',
                'files': originals}
        return context

    def _execute(self, stage, operation, *, requirements=None, candidate=None, feedback=None,
                 timeout=1800, inline_sources=False, runner=None):
        if (isinstance(timeout, bool) or not isinstance(timeout, (int, float))
                or not math.isfinite(timeout) or timeout <= 0):
            raise ValueError('A positive finite per-operation timeout is required')
        trusted = runner is None
        task = self._prepare(stage, operation, requirements, candidate,
                             'host-executed' if trusted else 'injected-test-transport', feedback)
        start = time.perf_counter()
        try:
            context = self._context(task, inline_sources)
            instruction = VERIFICATION if operation == 'verify' else AGENTS[stage].instruction
            prompt = POLICY + '\n' + instruction + '\n' + json.dumps(context, ensure_ascii=False)
            self.store.put('tasks/' + task['id'] + '/context.json', context)
            provider = runner
            if provider is None:
                from ..ai.provider import run_job
                provider = run_job
            response = provider(self.source.root, self.store.path('tasks/' + task['id'] + '/provider'),
                                prompt, contracts.transport_schema(task), timeout)
            self.store.put('tasks/' + task['id'] + '/transport.json', response)
            if response.get('exit_code') != 0 or response.get('metadata', {}).get('status') != 'passed':
                raise RuntimeError('Analysis provider failed; raw artifacts were preserved')
            answer = response.get('answer')
            provenance = {'kind': task['origin'], 'contextId': task['contextId'],
                          'invocationId': task['id'], 'independenceVerified': trusted and operation == 'verify',
                          'transport': 'codex-ephemeral' if trusted else 'injected-test-transport',
                          'elapsedSeconds': time.perf_counter() - start,
                          'answerSha256': contracts.digest(answer)}
            return self._record(task, answer, provenance)
        except (Exception, KeyboardInterrupt) as exc:
            with self.store.transaction() as latest:
                stale = (latest['executionEpoch'] != task['executionEpoch']
                         or latest['version'] != task['baseVersion']
                         or latest['tasks'].get(task['id']) != 'issued')
                self.store.put('tasks/' + task['id'] + '/failure.json',
                               {'errorType': type(exc).__name__, 'error': str(exc), 'staleReturn': stale})
                if not stale:
                    latest['tasks'][task['id']] = 'failed'
                    if latest['status'] == 'active':
                        latest.update(status='stopped', stopReason=type(exc).__name__ + ': ' + str(exc))
                self.store.save_state(latest)
            raise

    def execute(self, stage, *, requirements=None, feedback=None, timeout=1800,
                inline_sources=False, runner=None):
        return self._execute(stage, 'extract', requirements=requirements, feedback=feedback,
                             timeout=timeout, inline_sources=inline_sources, runner=runner)

    def verify(self, candidate, *, timeout=1800, inline_sources=False, runner=None):
        proposal = self.store.get('candidates/' + candidate + '.json')
        return self._execute(proposal['stage'], 'verify', candidate=candidate,
                             timeout=timeout, inline_sources=inline_sources, runner=runner)

    def _publish(self, state, revision):
        revision.update(version=state['version'] + 1, parent=state['revision'],
                        snapshotId=self.source.snapshot_id)
        identifier = contracts.digest(revision)
        self.store.put('revisions/' + identifier + '.json', revision)
        for task_id, status in state['tasks'].items():
            if status == 'issued':
                state['tasks'][task_id] = 'cancelled'
        state.update(version=revision['version'], revision=identifier,
                     acceptedRequirements=revision['acceptedRequirements'],
                     invalidatedRequirements=revision['invalidatedRequirements'],
                     executionEpoch=state['executionEpoch'] + 1,
                     status='complete' if set(revision['acceptedRequirements']) == set(self.obligations) else 'active',
                     stopReason=None)
        self.store.save_state(state)

    def adopt(self, candidate):
        self.source.verify()
        self._state()
        with self.store.transaction() as state:
            if state['status'] != 'active' or candidate not in state['candidates']:
                raise ValueError('Active session and known candidate required')
            proposal = self.store.get('candidates/' + candidate + '.json')
            if proposal['baseVersion'] != state['version'] or proposal['baseRevision'] != state['revision']:
                raise ValueError('Conflicting candidate base version; re-extract against the current revision')
            verifications = [self.store.get('verifications/' + key + '.json') for key in state['verifications']]
            applicable = [item for item in verifications if item['candidate'] == candidate
                          and item['baseVersion'] == state['version']]
            if not applicable:
                raise AcceptanceError('Independent verification required before adoption')
            verification = applicable[-1]
            for artifact, operation in ((proposal, 'extract'), (verification, 'verify')):
                task = self.store.get('tasks/' + artifact['taskId'] + '/request.json')
                provenance = artifact['provenance']
                if (provenance.get('kind') != 'host-executed'
                        or provenance.get('transport') != 'codex-ephemeral'
                        or task['origin'] != 'host-executed'
                        or task['operation'] != operation or task['stage'] != proposal['stage']
                        or task['sessionId'] != self.config['id']
                        or artifact['sessionId'] != self.config['id']
                        or artifact['snapshotId'] != self.source.snapshot_id
                        or artifact['goalSha256'] != contracts.digest(self.config['request']['goal'])
                        or artifact['baseRevision'] != state['revision']
                        or provenance['contextId'] != task['contextId']
                        or artifact['contextId'] != task['contextId']
                        or provenance['invocationId'] != task['id']
                        or provenance['answerSha256'] != contracts.digest(artifact['answer'])):
                    raise AcceptanceError('Independent host-owned execution provenance required')
                contracts.validate_result(artifact['answer'], task, self.source, self._current(state)['records'])
            if (proposal['contextId'] == verification['contextId']
                    or proposal['taskId'] == verification['taskId']
                    or not verification['provenance']['independenceVerified']):
                raise AcceptanceError('Independent verification context required')
            author_task = self.store.get('tasks/' + proposal['taskId'] + '/request.json')
            verify_task = self.store.get('tasks/' + verification['taskId'] + '/request.json')
            view = self._proposal_view(state, author_task, proposal['answer'])
            view_hash = contracts.digest(view)
            if (view_hash != proposal['viewSha256'] or view_hash != verification['viewSha256']
                    or view_hash != verify_task['viewSha256']
                    or verification['invalidatedRequirements'] != view['invalidatedRequirements']
                    or set(verify_task['requirements']) != set(view['acceptedRequirements'])):
                raise ValueError('Verification view or invalidation binding changed')
            answer = verification['answer']
            accepted = set(view['acceptedRequirements'])
            if (any(item['status'] != 'pass' for item in answer['checks'])
                    or any(item['severity'] == 'blocking' for item in answer['findings'])
                    or any(set(item['blocksRequirements']) & accepted for item in answer['unknownChecks'])
                    or any(set(item['blocksRequirements']) & accepted for item in answer['unknowns'])):
                raise AcceptanceError('Verification has unresolved obligations or blocking findings')
            if (any(item['status'] == 'unresolved' for item in proposal['answer']['coverage'])
                    or any(item['requirement'] in accepted
                           for item in proposal['answer']['followups'])):
                raise AcceptanceError('Candidate has unfinished assigned obligations; retain the partial result')
            current = self._current(state)
            identities = deepcopy(current['identities'])
            for key, record in view['records'].items():
                identities.setdefault(key, {field: record[field] for field in ('id', 'kind', 'ownerRequirement')})
            receipts = {key: deepcopy(value) for key, value in current['receipts'].items() if key in accepted}
            for key in proposal['requirements']:
                receipts[key] = {'stage': self.obligations[key]['stage'], 'scope': self.obligations[key]['scope'],
                                 'contentSha256': view['contentHashes'][key], 'candidate': candidate,
                                 'verification': contracts.digest(verification),
                                 'requires': {dep: current['receipts'][dep]['contentSha256']
                                              for dep in self.obligations[key]['requires']}}
            for receipt in receipts.values():
                receipt['verification'] = contracts.digest(verification)
            invalidated = deepcopy(state['invalidatedRequirements'])
            for key in view['invalidatedRequirements']:
                invalidated[key] = {'reason': 'Upstream content or record dependency changed',
                                    'previousRevision': state['revision']}
            for key in accepted:
                invalidated.pop(key, None)
            decisions = {item['unknownId']: item for item in answer['unknownChecks']}
            unknowns = {key: {**deepcopy(item), 'decision': deepcopy(decisions[key])}
                        for key, item in view['unknowns'].items()}
            for item in answer['unknowns']:
                key = verification['taskId'] + ':' + item['id']
                unknowns[key] = {'id': key, 'sha256': contracts.digest(item), 'content': deepcopy(item),
                                 'owners': list(verify_task['requirements']), 'decision': None}
            revision = {'kind': 'adoption', 'candidate': candidate, 'verification': contracts.digest(verification),
                        'records': view['records'], 'unknowns': unknowns, 'receipts': receipts,
                        'identities': identities, 'acceptedRequirements': view['acceptedRequirements'],
                        'invalidatedRequirements': invalidated}
            self._publish(state, revision)
        return self.status()

    def revise(self, requirements, reason):
        if not isinstance(reason, str) or not reason.strip():
            raise ValueError('An explicit revision reason is required')
        selected = self._select(requirements)
        self.source.verify()
        self._state()
        with self.store.transaction() as state:
            if state['status'] not in {'active', 'complete'}:
                raise ValueError('Resume a stopped/cancelled session before revision')
            current = self._current(state)
            if not set(selected) & set(state['acceptedRequirements']):
                raise ValueError('Revision requires at least one adopted obligation')
            affected = self._affected(current, selected) & set(state['acceptedRequirements'])
            accepted = set(state['acceptedRequirements']) - affected
            invalidated = deepcopy(state['invalidatedRequirements'])
            for key in affected:
                invalidated[key] = {'reason': reason, 'previousRevision': state['revision']}
            revision = {'kind': 'invalidation', 'candidate': None, 'verification': None,
                        'records': {key: value for key, value in current['records'].items()
                                    if value['ownerRequirement'] in accepted},
                        'unknowns': deepcopy(current['unknowns']),
                        'receipts': {key: value for key, value in current['receipts'].items() if key in accepted},
                        'identities': current['identities'], 'acceptedRequirements': self._ordered(accepted),
                        'invalidatedRequirements': invalidated}
            for item in revision['unknowns'].values():
                if (set(item['owners']) | set(item['content']['relatedRequirements'])) & affected:
                    item['decision'] = None
            self._validate_records(revision['records'])
            self._publish(state, revision)
        return self.status()

    def _attempt_key(self, state, ids):
        current = self._current(state)
        scopes = {self.obligations[key]['scope'] for key in ids}
        return contracts.digest({'snapshotId': self.source.snapshot_id, 'requirements': ids,
                                 'goal': self.config['request']['goal'],
                                 'basis': {key: record['version'] for key, record in current['records'].items()
                                           if self.obligations[record['ownerRequirement']]['scope'] in scopes},
                                 'receipts': {key: value['contentSha256'] for key, value in current['receipts'].items()
                                              if self.obligations[key]['scope'] in scopes}})

    def run(self, *, requirements=None, timeout=1800, inline_sources=False, runner=None):
        targets = self._select(requirements)
        needed = set(targets)
        while True:
            expanded = needed | {dep for key in needed for dep in self.obligations[key]['requires']}
            if expanded == needed:
                break
            needed = expanded
        actions = []
        while True:
            state = self._state()
            accepted = set(state['acceptedRequirements'])
            if set(targets).issubset(accepted):
                return {'status': 'complete' if state['status'] == 'complete' else 'scope-complete',
                        'actions': actions, 'session': self.status()}
            if state['status'] != 'active':
                return {'status': state['status'], 'actions': actions, 'session': self.status()}
            ready = [key for key in self.obligations if key in needed - accepted
                     and set(self.obligations[key]['requires']).issubset(accepted)]
            if not ready:
                return {'status': 'needs-investigation', 'reason': 'No verified prerequisite path is ready',
                        'actions': actions, 'session': self.status()}
            # Prefer advancing a verified local slice over finishing all catalogs.
            first = max(ready, key=lambda key: contracts.STAGES.index(self.obligations[key]['stage']))
            stage, scope = self.obligations[first]['stage'], self.obligations[first]['scope']
            ids = [key for key in ready if self.obligations[key]['stage'] == stage
                   and self.obligations[key]['scope'] == scope]
            attempt = self._attempt_key(state, ids)
            if attempt in state['attempts']:
                return {'status': 'needs-investigation', 'reason': 'No new input or prerequisite progress',
                        'pending': deepcopy(state['attempts'][attempt]), 'actions': actions, 'session': self.status()}
            proposed = self.execute(stage, requirements=ids, timeout=timeout,
                                    inline_sources=inline_sources, runner=runner)
            verified = self.verify(proposed['id'], timeout=timeout, inline_sources=inline_sources, runner=runner)
            actions.append({'stage': stage, 'requirements': ids, 'candidate': proposed['id'],
                            'verification': verified['id']})
            try:
                self.adopt(proposed['id'])
            except AcceptanceError as exc:
                pending = {'stage': stage, 'requirements': ids, 'candidate': proposed['id'],
                           'verification': verified['id'], 'reason': str(exc),
                           'followups': proposed['result']['followups'], 'findings': verified['result']['findings']}
                with self.store.transaction() as latest:
                    latest['attempts'][attempt] = pending
                    latest['stopReason'] = str(exc)
                    self.store.save_state(latest)
                return {'status': 'needs-investigation', 'pending': pending,
                        'actions': actions, 'session': self.status()}

    def cancel(self, reason='user-cancelled'):
        self._state()
        with self.store.transaction() as state:
            if state['status'] == 'complete':
                raise ValueError('A completed session must be explicitly revised before cancellation')
            for task_id in state['tasks']:
                if state['tasks'][task_id] == 'issued':
                    state['tasks'][task_id] = 'cancelled'
            state.update(status='cancelled', stopReason=reason, executionEpoch=state['executionEpoch'] + 1)
            self.store.save_state(state)
        return deepcopy(state)

    def resume(self, request):
        contracts.validate_request(request)
        if request != self.config['request']:
            raise ValueError('Resume requires the original goal, scope and permissions')
        self.source.verify()
        self._state()
        with self.store.transaction() as state:
            if state['status'] not in {'cancelled', 'stopped'}:
                raise ValueError('Only a stopped or cancelled session can resume')
            state.update(status='active', stopReason=None)
            self.store.save_state(state)
        return self.status()

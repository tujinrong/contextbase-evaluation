"""Read-only custody validation and explicit import into a fresh discovery work.

Archived code is data: it is hashed/parsed, never imported or executed. An old
session is never opened under the current engine. Source custody proves original
delivery, not business correctness, independence of claims or acceptance.
"""
from __future__ import annotations

import ast
from copy import deepcopy
import hashlib
import importlib.metadata
import json
from pathlib import Path

from . import candidate_amendment, contracts as c, investigation
from .evidence import EvidenceAccess, EvidenceRequestError
from .evidence_dialog import validate_delivery
from .facts import extractor_fingerprint
from .handoff import followup_question
from .paths import material_path, safe_path
from .sources import SourceAccess
from .storage import ArtifactStore

VERSION = 'contextbase-candidate-amendment-seed/1'
CUSTODY_VERSION = 'contextbase-candidate-custody/1'
SEMANTIC_CUSTODY_VERSION = 'contextbase-candidate-custody/2'
SEMANTIC_BINDING_VERSION = 'contextbase-semantic-custody/1'
LEGACY_ENGINE = '5b4157a97836890407be9214ba6eb5a069b48fe030fa5493649bd0d3c4026931'
SEMANTIC_PREDECESSOR_ENGINE = 'ea9fa131c6bb93c3272fba6792fb340d2827b11db39d4db8d2e6d27216577619'
_PACKAGES = ('jsonschema', 'tree-sitter', 'tree-sitter-c-sharp', 'tree-sitter-java')
_SOURCE_OPERATIONS = {'inventory', 'query', 'read', 'search'}


def _json(path):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError('Duplicate custody JSON member')
            result[key] = value
        return result
    def invalid(value):
        raise ValueError('Non-finite custody JSON value')
    return json.loads(path.read_text(encoding='utf-8'), object_pairs_hook=unique, parse_constant=invalid)


def _sha(data):
    return hashlib.sha256(data).hexdigest()


def _basis(task):
    return {key: deepcopy(value) for key, value in task.items()
            if key not in {'id', 'contextId', 'executionEpoch', 'rootTaskId'}}


def _inventory(bundle, manifest):
    declared = manifest['files']
    if not isinstance(declared, dict) or not declared:
        raise ValueError('Custody requires an explicit complete file inventory')
    actual = {}
    for path in bundle.rglob('*'):
        safe_path(path)
        if path.is_file() and path != bundle / 'custody.json':
            data = path.read_bytes()
            actual[path.relative_to(bundle).as_posix()] = {'sha256': _sha(data), 'bytes': len(data)}
        elif not path.is_dir() and path != bundle / 'custody.json':
            raise ValueError('Custody inputs must be ordinary files or directories')
    for relative in declared:
        material_path(bundle, relative)
    if len({key.casefold() for key in declared}) != len(declared) or declared != actual:
        raise ValueError('Custody file inventory, byte size or content hash changed')


def _toolchain(bundle, manifest, store):
    from .controller import engine_fingerprint
    toolchain = material_path(bundle, 'toolchain')
    controller = material_path(toolchain, 'controller.py').read_text(encoding='utf-8')
    tree = ast.parse(controller)
    function = next((node for node in tree.body
                     if isinstance(node, ast.FunctionDef) and node.name == 'engine_fingerprint'), None)
    names = None
    if function:
        for node in ast.walk(function):
            if isinstance(node, ast.comprehension) and isinstance(node.target, ast.Name) and node.target.id == 'name':
                try:
                    values = ast.literal_eval(node.iter)
                except (ValueError, TypeError):
                    continue
                if isinstance(values, (tuple, list)) and values and all(isinstance(value, str) for value in values):
                    names = values
                    break
    if not names or len(set(names)) != len(names):
        raise ValueError('Unsupported archived engine fingerprint declaration')
    files = {name: material_path(toolchain, name).read_text(encoding='utf-8') for name in names}
    dependencies = manifest['dependencies']
    if set(dependencies) != set(_PACKAGES):
        raise ValueError('Incomplete custody dependency binding')
    current_dependencies = {}
    for name in _PACKAGES:
        try:
            current_dependencies[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            current_dependencies[name] = None
    engine = c.digest({'files': files, 'dependencies': dependencies})
    supported = ({SEMANTIC_PREDECESSOR_ENGINE, engine_fingerprint()}
                 if manifest['schema'] == SEMANTIC_CUSTODY_VERSION else {LEGACY_ENGINE, engine_fingerprint()})
    if (engine != manifest['engineSha256'] or engine not in supported
            or dependencies != current_dependencies):
        raise ValueError('Unsupported or changed custody engine/dependency binding')
    binding_files = {name: material_path(toolchain, name).read_text(encoding='utf-8')
                     for name in ('agent.py', 'handoff.py', 'cli.py', 'config.py', 'catalog.py')}
    binding_files['implementation'] = material_path(toolchain, 'discovery_implementation.py').read_text(encoding='utf-8')
    binding = {'schema': 'contextbase-agent/1', 'name': 'discovery-agent', 'stage': 'discovery',
               'implementationSha256': c.digest(binding_files)}
    if binding != store.get('agent.json') or c.digest(binding) != manifest['agentBindingSha256']:
        raise ValueError('Custody discovery implementation binding changed')


def _task(store, identifier, config, source, index, semantic=None):
    task = store.get('tasks/' + identifier + '/request.json')
    if semantic is not None:
        if (task.get('semanticPolicy') != semantic['policy']
                or task.get('semanticIndexSha256') != semantic['indexSha256']):
            raise ValueError('Custody task semantic binding changed')
    elif 'semanticPolicy' in task or 'semanticIndexSha256' in task:
        raise ValueError('Semantic-session custody import is not supported by this seed contract')
    goal = config['request']['goal']
    if (task['id'] != identifier or task['sessionId'] != config['id']
            or task['snapshotId'] != source.snapshot_id
            or task['goalSha256'] != c.digest(goal)
            or task['goalRequirements'] != goal['requirements']
            or task['goalRequirementIds'] != [row['id'] for row in goal['requirements']]
            or task['sourceFactsSha256'] != index.sha256
            or task.get('evidenceIndexSha256') != index.sha256
            or task.get('authorizedSourcePaths') != list(source.paths)):
        raise ValueError('Custody task source, goal, index or scope binding changed')
    obligations = {row['id']: row for row in goal['requirements']}
    if (task['stage'] != 'discovery' or not task['requirements']
            or len(set(task['requirements'])) != len(task['requirements'])
            or any(key not in obligations or obligations[key]['stage'] != 'discovery'
                   for key in task['requirements'])):
        raise ValueError('Custody import supports original discovery obligations only')
    return task


def _semantic_schema():
    from .semantic_support import VERSION as policy
    return c.obj({'schema': {'type': 'string', 'const': SEMANTIC_BINDING_VERSION},
                  'policy': {'type': 'string', 'const': policy},
                  'options': c.obj({'schema': {'type': 'string', 'const': policy},
                                    'project': c.TEXT, 'configuration': c.TEXT}),
                  'runtimeSha256': c.SHA256, 'indexSha256': c.SHA256,
                  'bindingSha256': c.SHA256, 'importEngineSha256': c.SHA256})


def validate_semantic_binding(index, binding, options, task=None):
    """Revalidate an installed semantic seed against current source/toolchain bytes."""
    from .controller import engine_fingerprint
    from .semantic_support import normalize_options
    c.validate(binding, _semantic_schema())
    normalized = normalize_options(options)
    semantic = getattr(index, 'semantic_index', None)
    if (normalized is None or options != normalized or binding['options'] != normalized
            or semantic is None or semantic.facts.sha256 != index.sha256
            or semantic.facts.source.snapshot_id != index.source.snapshot_id
            or binding['importEngineSha256'] != engine_fingerprint()):
        raise ValueError('Amendment semantic source, configuration or engine binding changed')
    semantic.validate()
    document = semantic.document
    if (semantic.sha256 != binding['indexSha256']
            or c.digest(document['binding']) != binding['bindingSha256']
            or document['binding']['rootProject'] != normalized['project']
            or document['binding']['context']['analysisConfiguration'] != normalized['configuration']):
        raise ValueError('Amendment semantic index or settings binding changed')
    if task is not None and (task.get('semanticPolicy') != binding['policy']
                             or task.get('semanticIndexSha256') != binding['indexSha256']):
        raise ValueError('Amendment task semantic binding changed')
    return semantic


def validate_semantic_runtime(runtime, source, index, options):
    from .semantic_support import VERSION as policy, RUNTIME_VERSION
    semantic = getattr(index, 'semantic_index', None)
    if (runtime.get('schema') != RUNTIME_VERSION or runtime.get('policy') != policy
            or runtime.get('options') != options or semantic is None
            or runtime.get('snapshotId') != source.snapshot_id
            or runtime.get('sourceFactsSha256') != index.sha256
            or runtime.get('semanticIndexSha256') != semantic.sha256):
        raise ValueError('Amendment semantic runtime pointer binding changed')


def _semantic_custody(bundle, manifest, store, config, source, index):
    if manifest['schema'] == CUSTODY_VERSION:
        if config.get('semanticOptions') or getattr(index, 'semantic_index', None) is not None:
            raise ValueError('Semantic-session custody import is not supported by this seed contract')
        return None
    binding = manifest['semantic']
    semantic = validate_semantic_binding(index, binding, config.get('semanticOptions'))
    runtime = store.get('semantic-runtime.json')
    validate_semantic_runtime(runtime, source, index, binding['options'])
    if c.digest(runtime) != binding['runtimeSha256']:
        raise ValueError('Custody original semantic runtime pointer changed')
    documents = [store.get(path.relative_to(store.root).as_posix())
                 for path in store.path('semantic-calls').glob('*.json')]
    if semantic.document not in documents:
        raise ValueError('Custody does not contain the exact current semantic index')
    # The archived helpers remain data. Check their exact basis without importing
    # any module or executing any archived/source program.
    toolchain = material_path(bundle, 'toolchain')
    implementation = semantic.document['binding']['implementation']
    host = semantic.document['binding']['host']
    for name, expected in {**implementation, 'dotnet_host.py': host['bootstrapSha256'],
                            'dotnet/SemanticCalls.cs': host['helperSha256'],
                            'dotnet/NugetContentHash.cs': host['packageHashHelperSha256']}.items():
        if _sha(material_path(toolchain, name).read_bytes()) != expected:
            raise ValueError('Custody archived semantic helper binding changed')
    current_support = Path(__file__).with_name('semantic_support.py').read_bytes()
    if material_path(toolchain, 'semantic_support.py').read_bytes() != current_support:
        raise ValueError('Custody semantic initial-delivery implementation changed')
    return deepcopy(binding)


def _artifact(store, folder, identifier):
    c.validate(identifier, c.SHA256)
    artifact = store.get(folder + '/' + identifier + '.json')
    if c.digest(artifact) != identifier:
        raise ValueError('Custody artifact content-address binding changed')
    return artifact


def _artifact_task(artifact, task):
    fields = ('schema', 'sessionId', 'stage', 'operation', 'baseVersion', 'baseRevision',
              'snapshotId', 'goalSha256', 'requirements', 'candidate', 'feedback', 'contextId')
    if artifact['taskId'] != task['id'] or any(artifact.get(key) != task.get(key) for key in fields):
        raise ValueError('Custody artifact and its original task disagree')
    c.validate(artifact['answer'], c.result_schema(task))
    if task['operation'] == 'verify' and artifact['viewSha256'] != task['viewSha256']:
        raise ValueError('Custody verification task view changed')


def _source_refs(value):
    if isinstance(value, dict):
        if set(value) == {'path', 'startLine', 'endLine', 'sha256'}:
            yield value
        else:
            for child in value.values():
                yield from _source_refs(child)
    elif isinstance(value, list):
        for child in value:
            yield from _source_refs(child)


def _author_custody(store, source, index, task, candidate):
    """Validate committed author transcripts without opening/replaying a Session."""
    from .incremental import (VERSION as protocol, ORIGIN, POLICY, _schema,
                              _context, _material_reply, _material_error_reply)
    manifest = store.get('tasks/' + task['id'] + '/incremental.json')
    provenance = candidate['provenance']
    context = store.get('tasks/' + task['id'] + '/context.json')
    transport = store.get('tasks/' + task['id'] + '/transport.json')
    if (task.get('incrementalPolicy') != protocol or task.get('origin') != 'host-executed'
            or task['operation'] != 'extract' or provenance.get('kind') != 'host-composed'
            or provenance.get('executionMode') != 'composite' or provenance.get('responseOrigin') != ORIGIN
            or provenance.get('answerSha256') != c.digest(candidate['answer'])
            or manifest.get('schema') != protocol or manifest.get('basis') != _basis(task)
            or manifest.get('context') != context or context.get('task') != task
            or context.get('request') != store.get('session.json')['request']
            or manifest.get('workflow') != 'workflows/' + c.digest(_basis(task))
            or manifest.get('answerSha256') != c.digest(candidate['answer'])
            or provenance.get('incrementalTranscriptSha256') != c.digest(manifest)
            or transport.get('answer') != candidate['answer']
            or transport.get('metadata', {}).get('incrementalTranscriptSha256') != c.digest(manifest)):
        raise ValueError('Custody author composite binding changed')
    work = ArtifactStore(store.path(manifest['workflow']))
    checkpoint = work.get('state.json')
    if (checkpoint['basis'] != manifest['basis'] or checkpoint['trace'] != manifest['trace']
            or checkpoint.get('schema') != protocol or not manifest['trace']
            or len(set(manifest['trace'])) != len(manifest['trace'])):
        raise ValueError('Custody committed author trace changed')
    events, closures, units = [], {}, {}
    for call_id in manifest['trace']:
        c.validate(call_id, {'type': 'string', 'pattern': '^[A-Za-z0-9_-]+$'})
        prefix = 'calls/' + call_id
        setup, completed = work.get(prefix + '/setup.json'), work.get(prefix + '/complete.json')
        child, phase, unit = setup['task'], setup['phase'], setup['unit']
        original_root = store.get('tasks/' + child['rootTaskId'] + '/request.json')
        if (setup['schema'] != protocol or setup['basis'] != _basis(task)
                or _basis(child) != _basis(task) or child['id'] != call_id
                or original_root['id'] != child['rootTaskId'] or _basis(original_root) != _basis(task)
                or child['contextId'] == original_root['contextId']
                or setup['context'].get('request') != context['request']):
            raise ValueError('Custody author child task binding changed')
        if phase == 'plan':
            schema = investigation.plan_schema(task)
            if units or events or unit is not None:
                raise ValueError('Custody requires one initial author plan')
        elif phase == 'draft':
            schema = investigation.draft_schema(task, unit)
        elif phase == 'closure':
            schema = investigation.closure_schema(task, unit['requirement'])
        else:
            raise ValueError('Custody author trace contains an unsupported phase')
        if setup['resultSchema'] != schema or completed['call'] != call_id or completed['schema'] != protocol:
            raise ValueError('Custody phase schema or completed call changed')
        previous, pairs, latest, answer, notes = c.digest(setup), [], [], None, ''
        if not completed['rounds']:
            raise ValueError('Custody call has no committed provider rounds')
        access = EvidenceAccess(source, index, child)
        if child.get('semanticPolicy'):
            from .semantic_support import initial_pairs
            initial = initial_pairs(access, index, child, unit=unit, materials=setup['materials'])
            if work.get(prefix + '/semantic-initial.json') != {
                    'semanticIndexSha256': child['semanticIndexSha256'], 'pairs': initial}:
                raise ValueError('Custody automatic semantic initial delivery changed')
            pairs, latest = deepcopy(initial), deepcopy(initial)
        rounds = [work.get(prefix + f'/round-{number:04d}.json')
                  for number in range(1, len(completed['rounds']) + 1)]
        access.verify_replies((pair['request'], pair['reply'])
                              for row in rounds for pair in row['pairs']
                              if pair['request']['operation'] in _SOURCE_OPERATIONS)
        wire_schema = c.transport_schema(child, _schema(child, schema))
        for number, (pointer, row) in enumerate(zip(completed['rounds'], rounds), 1):
            relative = prefix + f'/round-{number:04d}'
            response = work.get(relative + '-response.json')
            dialog = row['context']['evidenceDialog']
            if (row['previousSha256'] != previous or row['number'] != number or c.digest(row) != pointer
                    or row['response'] != response or row['context']['task'] != setup['context']['task']
                    or dialog['protocol'] != protocol or dialog['round'] != number
                    or dialog['latestEvidence'] != latest
                    or dialog['deliveryLedger'] != [{'request': pair['request'],
                        'replySha256': pair['reply']['replySha256']} for pair in pairs]):
                raise ValueError('Custody provider hash chain or delivered-context ledger changed')
            if child.get('semanticPolicy') and row['context'] != _context(
                    setup['context'], number, notes, latest, pairs, setup['instruction'],
                    wire_schema, setup['materials']):
                raise ValueError('Custody semantic provider context replay changed')
            job = work.path(prefix + f'/provider/round-{number:04d}')
            prompt = material_path(job, 'prompt.txt').read_bytes()
            raw_answer = material_path(job, 'answer.txt').read_bytes()
            metadata = response.get('metadata', {})
            canonical_context = json.dumps(row['context'], sort_keys=True, ensure_ascii=False,
                                           separators=(',', ':'), allow_nan=False)
            if (response.get('exit_code') != 0 or metadata.get('status') != 'passed'
                    or metadata.get('prompt_sha256') != _sha(prompt)
                    or not prompt.decode('utf-8').endswith('\n' + canonical_context)
                    or row['promptSha256'] != _sha((setup['instruction'] + '\n'
                        + POLICY
                        + '\n' + canonical_context).encode('utf-8'))
                    or metadata.get('answer_sha256') != _sha(raw_answer)
                    or _json(job / 'answer.txt') != response.get('answer')
                    or _json(job / 'result.json') != response):
                raise ValueError('Custody raw provider prompt, answer or result binding changed')
            if _json(job / 'schema.json') != wire_schema:
                raise ValueError('Custody raw provider response schema changed')
            wrapper = response['answer']
            c.validate(wrapper, _schema(child, schema))
            if [pair['request'] for pair in row['pairs']] != wrapper['requests']:
                raise ValueError('Custody provider requests and recorded deliveries disagree')
            for pair in row['pairs']:
                if pair['request']['operation'] in {'listing', 'material'}:
                    try:
                        expected = _material_reply(pair['request'], setup['materials'], child)
                    except EvidenceRequestError as error:
                        expected = _material_error_reply(pair['request'], error, child)
                    if pair['reply'] != expected:
                        raise ValueError('Custody material receipt replay changed')
            if wrapper['action'] == 'requests':
                if not wrapper['requests'] or wrapper['answer'] is not None or number == len(completed['rounds']):
                    raise ValueError('Custody request round cannot complete an author invocation')
            else:
                if wrapper['requests'] or wrapper['answer'] is None or number != len(completed['rounds']):
                    raise ValueError('Custody author result must close its final provider round')
                if wrapper['action'] == 'checkpoint' and phase != 'draft':
                    raise ValueError('Only author drafts support checkpoints')
                answer = wrapper['answer']
                validate_delivery(source, answer, [pair for pair in pairs
                                                   if pair['request']['operation'] in _SOURCE_OPERATIONS])
            previous, latest = pointer, row['pairs']
            pairs.extend(latest)
            notes = wrapper['workingNotes']
        access._assert_binding()
        if (answer is None or completed['answerSha256'] != c.digest(answer)
                or completed['action'] != wrapper['action']):
            raise ValueError('Custody completed author answer binding changed')
        if phase == 'plan':
            investigation.validate_plan(task, answer)
            units.update({row['id']: row for row in answer['units']})
        elif phase == 'draft':
            if unit['id'] in units and units[unit['id']] != unit:
                raise ValueError('Custody author unit identity changed')
            units[unit['id']] = unit
            for added in answer['addUnits']:
                if added['id'] in units and units[added['id']] != added:
                    raise ValueError('Custody added author unit identity changed')
                units[added['id']] = added
            events.append({'unit': unit, 'answer': answer})
        else:
            closures[unit['requirement']] = answer
    if set(units) != {event['unit']['id'] for event in events}:
        raise ValueError('Custody author trace omitted a declared investigation unit')
    if investigation.canonical_answer(task, events, list(closures.values())) != candidate['answer']:
        raise ValueError('Custody author declarations do not reproduce the full base answer')
    return c.digest(manifest)


def inspect_bundle(bundle):
    """Check the sealed file inventory only; this grants no source custody or trust."""
    try:
        bundle = safe_path(Path(bundle))
        manifest = _json(material_path(bundle, 'custody.json'))
        if (manifest.get('schema') not in {CUSTODY_VERSION, SEMANTIC_CUSTODY_VERSION}
                or manifest.get('originDirectory') != 'origin'):
            raise ValueError('An explicit supported custody bundle is required')
        if manifest['schema'] == SEMANTIC_CUSTODY_VERSION:
            c.validate(manifest['semantic'], _semantic_schema())
        elif 'semantic' in manifest:
            raise ValueError('Semantic custody descriptor requires the version 2 contract')
        for key in ('candidateSha256', 'viewSha256', 'sourceSnapshotId', 'sourceFactsSha256',
                    'requestSha256', 'engineSha256', 'agentBindingSha256'):
            c.validate(manifest[key], c.SHA256)
        _inventory(bundle, manifest)
        return manifest
    except (OSError, KeyError, TypeError) as exc:
        raise ValueError('Invalid custody bundle inventory: ' + str(exc)) from exc


def load_bundle(bundle, source, index, request, verification_id, finding_ids=None):
    """Verify a host-owned immutable input as data and return an untrusted seed."""
    try:
        return _load_bundle(bundle, source, index, request, verification_id, finding_ids)
    except (OSError, KeyError, TypeError, SyntaxError, StopIteration) as exc:
        raise ValueError('Invalid custody bundle proof: ' + str(exc)) from exc


def _load_bundle(bundle, source, index, request, verification_id, finding_ids):
    bundle = safe_path(Path(bundle))
    manifest = inspect_bundle(bundle)
    store = ArtifactStore(material_path(bundle, 'origin'))
    # Every persisted store envelope is checked, not merely the selected paths.
    for path in store.root.rglob('*.json'):
        relative = path.relative_to(store.root).as_posix()
        if relative.startswith('snapshot/') or '/provider/' in relative:
            continue
        store.get(relative)
    config, state = store.get('session.json'), store.get('state.json')
    if manifest['schema'] == CUSTODY_VERSION and config.get('semanticOptions'):
        raise ValueError('Semantic-session custody import is not supported by this seed contract')
    _toolchain(bundle, manifest, store)
    c.validate_request(request)
    source.verify()
    index.validate()
    original = SourceAccess.open(store.path('snapshot'))
    if (config.get('incrementalPolicy') != 'contextbase-incremental/1'
            or config.get('engineSha256') != manifest['engineSha256']
            or config.get('request') != request or manifest['requestSha256'] != c.digest(request)
            or config['snapshotId'] != source.snapshot_id or original.snapshot_id != source.snapshot_id
            or manifest['sourceSnapshotId'] != source.snapshot_id
            or manifest['sourceFactsSha256'] != index.sha256
            or index.source.snapshot_id != source.snapshot_id
            or index.document['extractorSha256'] != extractor_fingerprint()
            or state.get('sessionSha256') != c.digest(config)):
        raise ValueError('Custody current source, request, extractor or index binding changed')
    documents = [store.get(path.relative_to(store.root).as_posix())
                 for path in store.path('source-facts').glob('*.json')]
    if index.document not in documents or c.digest(index.document) != index.sha256:
        raise ValueError('Custody does not contain the exact current fact index')
    semantic = _semantic_custody(bundle, manifest, store, config, source, index)
    identifier = manifest['candidateSha256']
    candidate = _artifact(store, 'candidates', identifier)
    task = _task(store, candidate['taskId'], config, source, index, semantic)
    _artifact_task(candidate, task)
    if (candidate['operation'] != 'extract' or candidate['stage'] != 'discovery'
            or candidate['requirements'] != task['requirements']
            or candidate['snapshotId'] != source.snapshot_id
            or candidate['viewSha256'] != c.digest(candidate['view'])
            or manifest['viewSha256'] != candidate['viewSha256']
            or identifier not in state['candidates'] or state['acceptedRequirements']):
        raise ValueError('Custody base must be a frozen unadopted discovery candidate')
    source.verify_evidence_many(list(_source_refs(candidate)))
    transcript = _author_custody(store, source, index, task, candidate)
    verification = _artifact(store, 'verifications', verification_id)
    verifier_task = _task(store, verification['taskId'], config, source, index, semantic)
    _artifact_task(verification, verifier_task)
    ancestors, cursor = {}, identifier
    while cursor:
        if cursor in ancestors:
            raise ValueError('Custody feedback ancestry contains a cycle')
        prior = _artifact(store, 'candidates', cursor)
        prior_task = _task(store, prior['taskId'], config, source, index, semantic)
        _artifact_task(prior, prior_task)
        if (prior['stage'] != candidate['stage'] or prior['requirements'] != candidate['requirements']
                or prior['goalSha256'] != task['goalSha256'] or prior['feedback'] != prior_task['feedback']):
            raise ValueError('Custody feedback ancestry changed its source or assigned obligations')
        ancestors[cursor] = prior
        cursor = prior['feedback']
    source_candidate = verification['candidate']
    if (verification_id not in state['verifications'] or source_candidate not in ancestors
            or verification['operation'] != 'verify' or verifier_task['operation'] != 'verify'
            or verifier_task['candidate'] != source_candidate
            or verification['viewSha256'] != ancestors[source_candidate]['viewSha256']
            or verification['requirements'] != candidate['requirements']
            or verification['snapshotId'] != source.snapshot_id
            or verification['goalSha256'] != task['goalSha256']):
        raise ValueError('Selected findings must come from the same scoped feedback ancestry')
    source.verify_evidence_many(list(_source_refs(verification)))
    findings = {row['id']: row for row in verification['answer']['findings']}
    chosen = list(findings) if finding_ids is None else list(finding_ids)
    if (not chosen or len(set(chosen)) != len(chosen) or not set(chosen).issubset(findings)
            or len(findings) != len(verification['answer']['findings'])):
        raise ValueError('Select exact unique existing finding identities')
    issues = []
    for key in chosen:
        finding = findings[key]
        if finding['requirement'] not in task['requirements']:
            raise ValueError('Selected finding belongs to an unassigned obligation')
        issue = {'id': verification_id + ':' + key, 'sourceCandidateSha256': source_candidate,
                 'sourceVerificationSha256': verification_id, 'finding': deepcopy(finding)}
        issue['sha256'] = c.digest(issue)
        issues.append(issue)
    followups = {}
    position = state['candidates'].index(identifier)
    for pointer in state['candidates'][:position + 1]:
        prior = _artifact(store, 'candidates', pointer)
        _task(store, prior['taskId'], config, source, index, semantic)
        for note in prior['answer']['followups']:
            question = followup_question(note, prior['requirements'])
            if question['id'] in candidate['view']['unknowns']:
                if question != candidate['view']['unknowns'][question['id']]:
                    raise ValueError('Retained followup content or ownership changed')
                followups.setdefault(c.digest(note), deepcopy(note))
    expected_followups = {key for key in candidate['view']['unknowns'] if key.startswith('followup:')}
    if {'followup:' + key for key in followups} != expected_followups:
        raise ValueError('Custody retained view is missing original followup declarations')
    for key, question in candidate['view']['unknowns'].items():
        if question['id'] != key or question['sha256'] != c.digest(question['content']):
            raise ValueError('Custody retained unknown content binding changed')
    seed = {'schema': VERSION, 'requestSha256': c.digest(request), 'snapshotId': source.snapshot_id,
            'indexSha256': index.sha256, 'stage': task['stage'], 'requirements': deepcopy(task['requirements']),
            'baseCandidateSha256': identifier, 'baseViewSha256': candidate['viewSha256'],
            'answer': deepcopy(candidate['answer']), 'view': deepcopy(candidate['view']),
            'followups': list(followups.values()), 'issues': issues,
            'custody': {'bundlePath': str(bundle), 'bundleSha256': c.digest(manifest),
                        'engineSha256': manifest['engineSha256'], 'authorTranscriptSha256': transcript,
                        'sourceVerificationSha256': verification_id}}
    if semantic is not None:
        seed['semanticBinding'] = semantic
    candidate_amendment.validate_spec(seed, task, {
        'schema': candidate_amendment.VERSION, 'seedSha256': c.digest(seed),
        'replaceKeys': [], 'addKinds': []})
    _inventory(bundle, manifest)
    return seed


def install(agent, bundle, verification_id, finding_ids=None, *, replace_keys, add_kinds):
    """Seal an untrusted seed/spec in fresh native discovery work, importing no state."""
    from .incremental import VERSION as protocol
    session = agent.session
    if agent.stage != 'discovery' or session.config.get('incrementalPolicy') != protocol:
        raise ValueError('Amendment seeds require a fresh incremental discovery workspace')
    work, bundle = safe_path(agent.work), safe_path(Path(bundle))
    if work == bundle or work in bundle.parents or bundle in work.parents:
        raise ValueError('Amendment input and new workspace must be disjoint')
    state = session._state()
    if (state['version'] != 0 or state['revision'] is not None or state['tasks']
            or state['candidates'] or state['verifications'] or state['acceptedRequirements']
            or state.get('attempts') or state.get('status') != 'active'
            or session.store.path('incoming.json').exists() or session.store.path('repair-seed.json').exists()):
        raise ValueError('Amendment installation requires fresh work with no inherited tasks or acceptance')
    seed = load_bundle(bundle, session.source, session.fact_index(), session.config['request'],
                       verification_id, finding_ids)
    if 'semanticBinding' in seed:
        current_index = session.fact_index()
        validate_semantic_binding(current_index, seed['semanticBinding'], session.config.get('semanticOptions'))
        validate_semantic_runtime(session.store.get('semantic-runtime.json'), session.source,
                                  current_index, seed['semanticBinding']['options'])
    spec = {'schema': candidate_amendment.VERSION, 'seedSha256': c.digest(seed),
            'replaceKeys': list(replace_keys), 'addKinds': list(add_kinds)}
    task = {'id': 'amendment-seed-install', 'operation': 'extract', 'stage': agent.stage,
            'origin': 'host-executed', 'requirements': seed['requirements'],
            'goalRequirements': session.config['request']['goal']['requirements'],
            'goalRequirementIds': [row['id'] for row in session.config['request']['goal']['requirements']],
            'snapshotId': session.source.snapshot_id, 'sourceFactsSha256': session.fact_index().sha256,
            'requestSha256': c.digest(session.config['request']),
            'authorizedSourcePaths': list(session.source.paths), 'recordKinds': sorted(agent.record_kinds),
            'catalogPolicy': getattr(agent, 'catalog_policy', None)}
    candidate_amendment.validate_spec(seed, task, spec)
    with session.store.transaction() as current:
        if current != state:
            raise ValueError('Workspace changed during amendment seed validation')
        # Preflight both immutable artifacts before writing either one.
        for name, payload in [('amendment-seed.json', seed), ('amendment-spec.json', spec)]:
            if session.store.path(name).exists() and session.store.get(name) != payload:
                raise ValueError('An installed amendment seed/spec cannot be replaced')
        session.store.put('amendment-seed.json', seed)
        session.store.put('amendment-spec.json', spec)
    return seed, spec

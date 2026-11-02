"""Explicit amendment-work bindings and replayable base-plus-delta provenance.

The importer owns original custody validation. This module preserves those
immutable inputs in a new workspace; it never imports acceptance or old tasks.
"""
from __future__ import annotations

from copy import deepcopy

from . import candidate_amendment as amendment, contracts as c


def operation_id(seed, spec):
    return c.digest({'schema': spec['schema'], 'seedSha256': c.digest(seed),
                     'specSha256': c.digest(spec), 'snapshotId': seed['snapshotId'],
                     'indexSha256': seed['indexSha256'], 'requestSha256': seed['requestSha256']})


def installed(session, task=None):
    names = ('amendment-seed.json', 'amendment-spec.json')
    present = [session.store.path(name).exists() for name in names]
    if not any(present):
        if task and task.get('amendmentPolicy'):
            raise ValueError('An amendment task lost its installed seed/spec')
        return None
    if not all(present):
        raise ValueError('Amendment seed/spec installation is incomplete')
    seed, spec = (session.store.get(name) for name in names)
    if spec.get('schema') == amendment.NATIVE_VERSION:
        from .native_amendment import installed as native_installed
        return native_installed(session, task)
    index = session.fact_index()
    if (not session.config.get('incrementalPolicy') or seed['stage'] != 'discovery'
            or seed['snapshotId'] != session.source.snapshot_id
            or seed['indexSha256'] != index.sha256
            or seed['requestSha256'] != c.digest(session.config['request'])
            or spec['seedSha256'] != c.digest(seed)):
        raise ValueError('Installed amendment source/request/index binding changed')
    semantic = seed.get('semanticBinding')
    if semantic is not None:
        from .amendment_seed import validate_semantic_binding, validate_semantic_runtime
        validate_semantic_binding(index, semantic, session.config.get('semanticOptions'), task)
        validate_semantic_runtime(session.store.get('semantic-runtime.json'), session.source,
                                  index, semantic['options'])
    elif (session.config.get('semanticOptions') or getattr(index, 'semantic_index', None) is not None
          or (task and ('semanticPolicy' in task or 'semanticIndexSha256' in task))):
        raise ValueError('Semantic amendment requires its installed semantic custody binding')
    if task is not None:
        if (task.get('amendmentPolicy') != amendment.VERSION
                or task.get('amendmentSeedSha256') != c.digest(seed)
                or task.get('amendmentSpecSha256') != c.digest(spec)
                or task.get('amendmentOperationId') != operation_id(seed, spec)
                or task.get('requestSha256') != seed['requestSha256']):
            raise ValueError('Amendment task seed/spec binding changed')
        if task['operation'] == 'extract':
            amendment.validate_spec(seed, task, spec)
    return seed, spec


def extensions(session, task):
    inputs = installed(session)
    if inputs is None or task['origin'] == 'external-handoff':
        return {}
    seed, spec = inputs
    if task['stage'] != 'discovery' and spec['schema'] != amendment.NATIVE_VERSION:
        raise ValueError('Candidate amendments currently support Discovery only')
    result = {'amendmentPolicy': spec['schema'], 'amendmentSeedSha256': c.digest(seed),
              'amendmentSpecSha256': c.digest(spec), 'requestSha256': seed['requestSha256'],
              'amendmentOperationId': operation_id(seed, spec)}
    if task['operation'] == 'extract':
        amendment.validate_spec(seed, {**task, **result}, spec)
        if task['feedback'] is not None:
            raise ValueError('Amendment and ordinary retry feedback are distinct operations')
    else:
        proposal = session.store.get('candidates/' + task['candidate'] + '.json')
        author = session.store.get('tasks/' + proposal['taskId'] + '/request.json')
        patch = patch_for_task(session, author)
        if proposal['provenance'].get('proposalOrigin') != 'amended-untrusted-candidate':
            raise ValueError('An amendment workspace verifies only its explicit amended candidate')
        result['amendmentIssueBindings'] = amendment.issue_bindings(seed, patch)
    return result


def patch_for_task(session, task):
    """Read and validate the committed delta in its original transport format."""
    seed, spec = installed(session, task)
    if task.get('nativeToolsPolicy'):
        return _native_patch(session, task, seed, spec)
    return _incremental_patch(session, task, seed, spec)


def _native_patch(session, task, seed, spec):
    manifest, transport = _native_manifest(session, task)
    submission = manifest['submission']
    delta = submission['amendment']
    answer = amendment.canonical_answer(seed, task, spec, delta['patch'], delta['closures'])
    if answer != submission['answer'] or answer != transport['answer']:
        raise ValueError('Native amendment composition changed')
    return deepcopy(delta['patch'])


def _incremental_patch(session, task, seed, spec):
    from .incremental import _basis

    manifest = session.store.get('tasks/' + task['id'] + '/incremental.json')
    if manifest['basis'] != _basis(task) or not manifest['trace']:
        raise ValueError('Amendment trace has a different task basis')
    call = manifest['trace'][0]
    prefix = manifest['workflow'] + '/calls/' + call
    setup = session.store.get(prefix + '/setup.json')
    complete = session.store.get(prefix + '/complete.json')
    if setup['phase'] != 'amend' or setup['basis'] != _basis(task):
        raise ValueError('Amendment provenance requires an explicit committed delta phase')
    response = session.store.get(prefix + f"/round-{len(complete['rounds']):04d}.json")
    patch = response['response']['answer']['answer']
    if c.digest(patch) != complete['answerSha256']:
        raise ValueError('Amendment committed delta content changed')
    amendment.apply_patch(seed, task, spec, patch)
    return patch


def _native_manifest(session, task):
    from .native_tools import _binding
    transport = session.store.get('tasks/' + task['id'] + '/transport.json')
    identifier = transport['metadata']['nativeTranscriptSha256']
    manifest = session.store.get('native-transcripts/' + identifier + '.json')
    if (c.digest(manifest) != identifier
            or manifest['binding'] != _binding(session.source, session.fact_index(), task)):
        raise ValueError('Native amendment transcript binding changed')
    return manifest, transport


def provenance(session, task, answer):
    seed, spec = installed(session, task)
    patch = patch_for_task(session, task)
    return {'proposalOrigin': 'amended-untrusted-candidate',
            'amendmentOperationId': operation_id(seed, spec),
            'amendmentSeedSha256': c.digest(seed), 'amendmentSpecSha256': c.digest(spec),
            'baseCandidateSha256': seed['baseCandidateSha256'],
            'baseViewSha256': seed['baseViewSha256'], 'patchSha256': c.digest(patch),
            'composition': 'untrusted-frozen-base+new-author-delta+fresh-author-closures',
            'combinedAnswerSha256': c.digest(answer)}


def audit(session, task):
    seed, spec = installed(session, task)
    patch = patch_for_task(session, task)
    return {'trust': 'Old findings and candidate claims are untrusted investigation inputs. '
                     'Independently check every disposition against this full new candidate and source. '
                     'An author declaration never supplies a verdict or source delivery.',
            'seedSha256': c.digest(seed), 'specSha256': c.digest(spec),
            'operationId': operation_id(seed, spec),
            'baseCandidateSha256': seed['baseCandidateSha256'],
            'baseViewSha256': seed['baseViewSha256'], 'patchSha256': c.digest(patch),
            'issues': deepcopy(seed['issues']), 'dispositions': deepcopy(patch['dispositions']),
            **({'priorFindings': deepcopy(seed['priorFindings'])} if 'priorFindings' in seed else {})}


def pending_ids(seed, task, record):
    """Retain old global question identities, namespacing only genuinely new ones."""
    original = next((row for row in seed['answer']['records'] if row['key'] == record['key']), None)
    if original == record:
        return deepcopy(seed['view']['records'][record['key']]['classification']['unknownIds'])
    known = seed['view']['unknowns']
    old = seed['answer']['taskId'] + ':'
    return [identifier if identifier in known else
            old + identifier if old + identifier in known else task['id'] + ':' + identifier
            for identifier in record['classification']['unknownIds']]


def validate_replay(session, task, artifact):
    seed, spec = installed(session, task)
    manifest = (_native_manifest(session, task)[0] if task.get('nativeToolsPolicy') else
                session.store.get('tasks/' + task['id'] + '/incremental.json'))
    if task['operation'] == 'extract':
        if manifest['context'].get('candidateAmendment') != {'seed': seed, 'spec': spec}:
            raise ValueError('Amendment replay retained input changed')
        expected = provenance(session, task, artifact['answer'])
        if any(artifact['provenance'].get(key) != value for key, value in expected.items()):
            raise ValueError('Amendment base/delta composition provenance changed')
    else:
        proposal = session.store.get('candidates/' + task['candidate'] + '.json')
        author = session.store.get('tasks/' + proposal['taskId'] + '/request.json')
        expected_audit = audit(session, author)
        if manifest['context'].get('amendmentAudit') != expected_audit:
            raise ValueError('Independent amendment issue/disposition audit changed')
        if task.get('amendmentIssueBindings') != amendment.issue_bindings(seed, patch_for_task(session, author)):
            raise ValueError('Independent amendment issue bindings changed')


def unresolved(session, candidate):
    proposal = session.store.get('candidates/' + candidate + '.json')
    if proposal['provenance'].get('proposalOrigin') != 'amended-untrusted-candidate':
        return []
    task = session.store.get('tasks/' + proposal['taskId'] + '/request.json')
    patch = patch_for_task(session, task)
    return [deepcopy(row) for row in patch['dispositions'] if row['status'] == 'unresolved']


def drive(task, context, invoke, validate_final):
    """One small author delta plus fresh closures; never a whole-base re-extract."""
    from . import incremental, investigation
    seed, spec = context['candidateAmendment']['seed'], context['candidateAmendment']['spec']
    amendment.validate_spec(seed, task, spec)
    materials = incremental._collections(seed['view']['records'], seed['view']['unknowns'],
                                         seed['answer'].get('factUsage', []))
    materials['feedback']['selected-amendment-issues'] = deepcopy(seed['issues'])
    patch = invoke('amend', None, materials, amendment.response_schema(seed, task, spec))
    try:
        draft = amendment.apply_patch(seed, task, spec, patch)
    except ValueError as exc:
        invoke.reject(exc)
        raise
    invoke.commit()
    materials = incremental._collections(draft['records'], seed['view']['unknowns'], draft['factUsage'])
    materials['feedback']['selected-amendment-issues'] = deepcopy(seed['issues'])
    materials['feedback']['amendment-dispositions'] = deepcopy(patch['dispositions'])
    package = {'schema': 'contextbase-obligation-closure/1',
               'trust': 'Untrusted retained base plus author delta; fresh closure required.',
               'requirements': deepcopy(task['goalRequirements']), 'assignedRequirements': task['requirements'],
               'records': deepcopy(draft['records']),
               'retainedUnknowns': deepcopy(seed['view']['unknowns']),
               'unknowns': deepcopy(draft['unknowns']), 'followups': deepcopy(draft['followups']),
               'issues': deepcopy(seed['issues']), 'dispositions': deepcopy(patch['dispositions']),
               'counts': {'records': len(draft['records']), 'unknowns': len(seed['view']['unknowns']) + len(patch['unknowns']),
                          'followups': len(draft['followups']), 'issues': len(seed['issues'])}}
    materials['feedback']['obligation-closure'] = package
    closures = []
    for key in task['requirements']:
        closure = invoke('closure', {'requirement': key}, materials, investigation.closure_schema(task, key))
        if closure['status'] != 'unresolved' and not closure['evidence']:
            error = ValueError('A positive obligation closure requires original-source evidence')
            invoke.reject(error)
            raise error
        invoke.commit()
        closures.append(closure)
    result = amendment.canonical_answer(seed, task, spec, patch, closures)
    if validate_final is not None:
        validate_final(result)
    return result

"""Lossless explicit project-input packaging; no business analysis or source execution."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, importlib.util, json, sys
sys.dont_write_bytecode = True
RUN = Path(r'D:/開発/contextbase-evaluation/agents/spec-agent/.tmp/20261014-nenkin-high-01')
REPORT = Path(r'D:/開発/contextbase-evaluation/agents/spec-agent/report/20261014-nenkin-high-01')
INPUT = Path(r'D:/開発/contextbase-evaluation/agents/reverse-agent/input')
HELPER = RUN / 'review_plan_with_scope_r01.py'
HELPER_SHA = '6cb4ca230efe445912a1ca6daa28148edfa764d3bd300d2cb0fae91c247ea2e5'
EXTRAS = ('nenkin/README.md', 'nenkin/.classpath', 'nenkin/.project', 'nenkin/.gitignore')
DESTINATION = RUN / 'snapshot-input-02'
CONTEXT = RUN / 'execution-context-input-02.json'
PLAN = RUN / 'jobs/plan-02/plan-verified.json'
PLAN_SHA = 'f6f63186086b33a76cb26f448b7e9052dc16bc5f47236bcdb477254de2646048'
HANDOFF_SHA = 'b14bffb4e680e07e204be5337dcc04c6fd149549320ab4e55b0e92d98730a727'

def initial_safe(value):
    path = Path(value).absolute()
    for node in (path, *path.parents):
        if node.is_symlink() or (node.exists() and getattr(node.lstat(), 'st_file_attributes', 0) & 0x400):
            raise ValueError('Linked path refused before access')
    return path.resolve()

if hashlib.sha256(initial_safe(HELPER).read_bytes()).hexdigest() != HELPER_SHA:
    raise ValueError('Fixed audited helper changed')
spec = importlib.util.spec_from_file_location('fixed_spec_scope_packer', initial_safe(HELPER))
guard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(guard)
safe, sha, load, require = guard.safe, guard.sha, guard.load, guard.require

def fresh(path, data):
    path = safe(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('xb') as stream:
        stream.write(data)

def write_json(path, value):
    fresh(path, (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode('utf-8'))

def source_inventory():
    found = {}
    def descend(directory):
        for path in sorted(safe(directory).iterdir()):
            path = safe(path)
            if path.is_dir():
                descend(path)
            else:
                require(path.is_file(), 'Unsupported input entry')
                found[path.relative_to(safe(INPUT)).as_posix()] = {'bytes': path.stat().st_size, 'sha256': sha(path)}
    descend(INPUT)
    return found

def main():
    runtime = guard.bootstrap()
    from contextbase.ai import capsule
    require(sha(guard.SNAPSHOT / 'manifest.json') == guard.SNAPSHOT_SHA and sha(guard.CONTEXT) == guard.CONTEXT_SHA,
            'Prior sealed input/context changed')
    old = capsule.verify(guard.SNAPSHOT)
    require(len(old['files']) == 175 and old['mode'] == 'source-only' and not old['referenceFiles'], 'Unexpected original capsule')
    before = source_inventory()
    seal = load(REPORT / 'protected-inputs-before.json')
    protected_seal_sha = sha(REPORT / 'protected-inputs-before.json')
    expected = {item['path']: {'bytes': item['bytes'], 'sha256': item['sha256']} for item in seal['files']}
    require(before == expected and len(before) == 345, 'Original input protected baseline differs')
    require(sha(PLAN) == PLAN_SHA and sha(PLAN.parent / 'plan-handoff.json') == HANDOFF_SHA, 'Prior plan/handoff changed')
    require(not safe(DESTINATION).exists() and not safe(CONTEXT).exists(), 'Fresh expanded capsule/context required')
    prior_paths = {item['path'] for item in old['files']}
    require(not set(EXTRAS) & prior_paths and set(EXTRAS) <= set(before), 'Invalid explicit primary project additions')
    manifest = json.loads(json.dumps(old))
    manifest['createdAt'] = datetime.now(timezone.utc).isoformat()
    manifest['priorSourceCapsuleManifestSha256'] = guard.SNAPSHOT_SHA
    manifest['packagingPolicy'] = 'Explicit user-requested project input source documentation and configuration; frozen extension filter unmodified'
    manifest['documentationIsRuntimeProof'] = False
    manifest['explicitAdditionalProjectTextPaths'] = list(EXTRAS)
    manifest['omitted'] = [entry for entry in old['omitted'] if entry['path'] not in EXTRAS]
    for entry in old['files']:
        for relative in ('sources/' + entry['path'], entry['indexed']):
            old_path = capsule.material_path(safe(guard.SNAPSHOT), relative)
            fresh(capsule.material_path(safe(DESTINATION), relative), old_path.read_bytes())
    for relative in EXTRAS:
        original = capsule.material_path(safe(INPUT), relative)
        raw = original.read_bytes()
        require(hashlib.sha256(raw).hexdigest() == before[relative]['sha256'], 'Project declaration changed before copy')
        text, encoding = capsule.decode(raw)
        lines = text.splitlines(keepends=True)
        indexed = 'indexed/' + relative + '.txt'
        fresh(capsule.material_path(safe(DESTINATION), 'sources/' + relative), raw)
        fresh(capsule.material_path(safe(DESTINATION), indexed),
              ''.join(f'{index:06d} | {line}' for index, line in enumerate(lines, 1)).encode('utf-8'))
        manifest['files'].append({'path': relative, 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest(),
                                  'encoding': encoding, 'lines': len(lines), 'indexed': indexed,
                                  'sourceMaterialClass': 'project-documentation-declaration' if relative.endswith('README.md')
                                                         else 'project-configuration-declaration'})
    write_json(DESTINATION / 'manifest.json', manifest)
    write_json(DESTINATION / 'seal.json', {'schema': 'reverse-ai-capsule-seal/1',
                                         'manifestSha256': sha(DESTINATION / 'manifest.json')})
    verified = capsule.verify(DESTINATION)
    require(len(verified['files']) == 179 and source_inventory() == before and guard.bootstrap() == runtime,
            'Expanded capsule/input/runtime verification failed')
    scope = load(guard.CONTEXT)
    scope['previousPlanProvided'] = True
    scope['primaryDocumentationSourcePaths'] = ['nenkin/README.md']
    scope['primaryProjectConfigurationSourcePaths'] = list(EXTRAS[1:])
    scope['ownProjectInputDocumentationIncluded'] = True
    scope['documentationInterpretation'] = 'Project input documentation/configuration declarations are observed text, not proof of runtime behavior. Distinguish declared requirements, implementation, conflicts and unknowns; no referenced external files are authorized.'
    scope['externalReferencedMaterialReadAuthorized'] = False
    scope['sourceSnapshotManifestSha256'] = sha(DESTINATION / 'manifest.json')
    scope['priorSourceSnapshotManifestSha256'] = guard.SNAPSHOT_SHA
    scope['priorExecutionContextSha256'] = guard.CONTEXT_SHA
    write_json(CONTEXT, scope)
    feedback = {'schema': 'spec-agent-expanded-input-plan-context/1',
                'executionContext': scope, 'previousAiPlan': load(PLAN), 'previousPlanSha256': PLAN_SHA,
                'previousPlanHandoffSha256': HANDOFF_SHA,
                'previousPlanScope': 'Prior sealed source input with primary README and project declarations omitted',
                'revisionRequirement': 'Create a fresh complete AI plan for the new sealed input. Preserve existing IDs and paths where responsibilities remain, add documentation/deployment coverage as needed. Read additional project declarations from this capsule; distinguish declarations from implemented behavior, retain source evidence and unknowns. Do not execute original programs or follow documentation links outside this capsule. Keep canonical feature/table kinds and separate analysis reports from specifications.',
                'additionalSourcePaths': list(EXTRAS), 'businessFactsOrCorrectionsAssembledByPython': False,
                'originalSpecificationsOrEvaluationExpectationsProvided': False}
    write_json(RUN / 'plan-input-expansion-context-r01.json', feedback)
    require(sha(guard.SNAPSHOT / 'manifest.json') == guard.SNAPSHOT_SHA and
            sha(guard.CONTEXT) == guard.CONTEXT_SHA and sha(PLAN) == PLAN_SHA and
            sha(PLAN.parent / 'plan-handoff.json') == HANDOFF_SHA and
            sha(REPORT / 'protected-inputs-before.json') == protected_seal_sha and
            capsule.verify(guard.SNAPSHOT) == old and source_inventory() == before and
            guard.bootstrap() == runtime and capsule.verify(DESTINATION) == verified,
            'Fixed original metadata/source/runtime or expanded capsule changed before final evidence')
    report = {'schema': 'spec-agent-lossless-input-expansion/1', 'status': 'PACKAGED_AND_FROZEN_CORE_VERIFIED',
              'createdAt': datetime.now(timezone.utc).isoformat(), 'snapshot': str(safe(DESTINATION)),
              'snapshotManifestSha256': sha(DESTINATION / 'manifest.json'), 'sourceFileCount': 179,
              'priorManifestSha256': guard.SNAPSHOT_SHA, 'oldSourceAndIndexedBytesModified': False,
              'additionalFiles': [item for item in verified['files'] if item['path'] in EXTRAS],
              'executionContext': str(safe(CONTEXT)), 'executionContextSha256': sha(CONTEXT),
              'planRevisionContext': str(safe(RUN / 'plan-input-expansion-context-r01.json')),
              'planRevisionContextSha256': sha(RUN / 'plan-input-expansion-context-r01.json'),
              'protectedOriginalInputCount': len(before), 'originalInputBeforeAfterUnchanged': True,
              'frozenRuntimeBeforeAfterUnchanged': True, 'runtimeReceiptSha256': guard.RECEIPT_SHA,
              'frozenCoreOrPromptModified': False, 'businessFactsOrProseAssembledByPython': False,
              'originalProgramsOrDatabaseExecuted': False, 'externalDocumentationTargetsRead': False,
              'independentVerification': 'PENDING', 'formalPercentage': None, 'published': False}
    write_json(REPORT / 'input-expansion-packaging-r01.json', report)
    print(json.dumps(report, ensure_ascii=False))

if __name__ == '__main__':
    main()

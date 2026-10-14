"""Seal the selected input and execution metadata; no business prose generation."""
from pathlib import Path
from datetime import datetime, timedelta, timezone
import hashlib
import json
from contextbase.ai import capsule

REPO = Path(r'D:/開発/contextbase-evaluation')
AGENT = REPO / 'agents/spec-agent'
WORK = AGENT / '.tmp/20261014-nenkin-high-01'
REPORT = AGENT / 'report/20261014-nenkin-high-01'
INPUT = REPO / 'agents/reverse-agent/input'
OUTPUT = REPO / 'agents/reverse-agent/output'
RUNTIME_RECORD = REPO / 'agents/reverse-agent/test-report/20261013-rerun-12h/source-pilot/runtime-code-source-13.json'
EXPECTED_RUNTIME = '5c3eeafb764afb64e3ef80fb422e4f68a9c41b98f000d13a8d57a505d947cc79'

def sha(path):
    return hashlib.sha256(capsule.safe_path(path).read_bytes()).hexdigest()

def fresh(path, value):
    path = capsule.safe_path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')

assert sha(RUNTIME_RECORD) == EXPECTED_RUNTIME
runtime = json.loads(RUNTIME_RECORD.read_text(encoding='utf-8'))
runtime_root = capsule.safe_path(Path(runtime['destination']))
actual_runtime = {p.relative_to(runtime_root).as_posix(): sha(p) for p in runtime_root.rglob('*')
                  if p.is_file() and '__pycache__' not in p.parts and p.suffix != '.pyc'}
assert actual_runtime == runtime['files'] and len(actual_runtime) == 128
assert capsule.safe_path(Path(capsule.__file__)) == runtime_root / 'contextbase/ai/capsule.py'
assert sha(Path(capsule.__file__)) == runtime['files']['contextbase/ai/capsule.py']
assert capsule.safe_path(INPUT) != capsule.safe_path(OUTPUT)
source_files = []
for path in sorted(INPUT.rglob('*')):
    if not path.is_file():
        continue
    path = capsule.safe_path(path)
    if not path.is_relative_to(INPUT):
        raise ValueError('Input leaves selected source root')
    source_files.append({'path': path.relative_to(INPUT).as_posix(),
                         'bytes': path.stat().st_size, 'sha256': sha(path)})
fresh(REPORT / 'protected-inputs-before.json', {'schema': 'spec-agent-input-seal/1', 'sourceRoot': str(INPUT), 'files': source_files})
snapshot = WORK / 'snapshot'
manifest = capsule.create(INPUT, snapshot, project_id='nenkin')
assert capsule.reference_mode(capsule.verify(snapshot)) == 'source-only'
source_hashes = {e['path']: e['sha256'] for e in manifest['files']}
registry = REPO / 'agents/reverse-agent/ContextBase/identities.json'
identities = json.loads(registry.read_text(encoding='utf-8'))
stable = []
for entry in identities['entries']:
    if entry.get('active') is True and entry.get('path') in source_hashes:
        stable.append({'id': entry['id'], 'kind': entry['kind'], 'sourcePath': entry['path'],
                       'aliases': entry.get('aliases', []),
                       'recordedSourceHashMatches': entry.get('source_sha256') == source_hashes[entry['path']]})
scope = {'schema': 'spec-agent-execution-context/1', 'classification': 'USER_REQUESTED_EXECUTION_SCOPE',
         'previousPlanProvided': False, 'agentRole': 'AG-SPEC', 'projectId': 'nenkin',
         'primarySourceDirectory': 'nenkin', 'dependencySourceDirectory': 'n2framework',
         'scopeRule': 'nenkin is the selected application; n2framework is included for its reachable framework dependencies. Do not turn unrelated framework application operations into separate target applications.',
         'sourceOnly': True, 'originalSpecificationsAuthorized': False, 'evaluationExpectationsAuthorized': False,
         'stableIdentities': stable, 'identityRegistrySha256': sha(registry),
         'existingBusinessProseProvided': False,
         'requestedQuality': 'Source-backed fields, all event branches, UI/backend/SQL/CRUD/transaction/exception traceability and independent text plus native visual review; no invented numerical qualification.',
         'requestedExcelPatterns': ['cover', 'normal', 'list'], 'preserveExistingExcelLayout': True,
         'originalProgramsAndDatabaseExecutionAuthorized': False}
fresh(WORK / 'execution-context.json', scope)
now = datetime.now(timezone.utc)
deadline = now + timedelta(hours=12)
rules = [REPO / 'AGENTS.md', REPO / 'agents/README.md', AGENT / 'AGENT.md',
         *sorted((REPO / 'docs').glob('*.md')), REPO / 'agents/reverse-agent/AGENTS.md']
run = {'schema': 'spec-agent-execution-manifest/1', 'runId': '20261014-nenkin-high-01',
       'createdAt': now.isoformat(), 'deadline': deadline.isoformat(),
       'timeLimitBasis': 'The previous user-requested maximum twelve hours is conservatively applied to this separate execution.',
       'status': 'SOURCE_SEALED_PLAN_PENDING', 'agentRole': 'AG-SPEC',
       'executionInfrastructure': 'Improved contextbase.ai source-only pipeline; spec-agent remains the authoring role contract.',
       'projectId': 'nenkin', 'scopeSelection': 'Existing input selected by stated assumption; asynchronous scope question may steer the execution.',
       'sourceRoot': str(INPUT), 'outputRoot': str(OUTPUT), 'workRoot': str(WORK),
       'stagingRoot': str(WORK / 'staging'), 'sourceSnapshot': str(snapshot),
       'sourceSnapshotManifestSha256': sha(snapshot / 'manifest.json'), 'sourceMode': 'source-only',
       'includedSourceFiles': len(manifest['files']), 'allProtectedInputFiles': len(source_files),
       'omittedMaterials': manifest.get('omitted', []),
       'runtimeReceipt': str(RUNTIME_RECORD), 'runtimeReceiptSha256': EXPECTED_RUNTIME,
       'runtimeRoot': str(runtime_root), 'runtimeFileCount': 128,
       'engineeringEvidence': 'Prior r19 452 tests; this is infrastructure evidence, not this project quality or formal95.',
       'rulePins': {str(p): sha(p) for p in rules},
       'executionContext': str(WORK / 'execution-context.json'), 'executionContextSha256': sha(WORK / 'execution-context.json'),
       'originalApplicationExecuted': False, 'formalPercentage': None, 'published': False,
       'requiredChecks': ['source unchanged', 'plan coverage and reachability', 'typed source facts',
                          'independent text review', 'Markdown structural validation', 'complete native figure/state review',
                          'literal Markdown/Excel value equality', 'cover/normal/list border separation',
                          'HTML/PDF/XLSX display and complete delivery manifest']}
fresh(REPORT / 'run-manifest.json', run)
print(json.dumps({'runId': run['runId'], 'projectId': 'nenkin', 'sourceFiles': len(manifest['files']),
                  'protectedFiles': len(source_files), 'snapshotSha256': run['sourceSnapshotManifestSha256'],
                  'deadline': run['deadline'], 'oldOutputChanged': False}))

"""Read-only mechanical comparison; no source semantics or plan mutation."""
from pathlib import Path
from collections import Counter
from datetime import datetime, timezone
import hashlib, importlib.util, json, sys

sys.dont_write_bytecode = True
REPO = Path(r'D:/開発/contextbase-evaluation')
RUN = REPO/'agents/spec-agent/.tmp/20261014-nenkin-high-01'
AUDIT = REPO/'agents/spec-agent/report/20261014-nenkin-high-01/independent-audit'
HELPER = RUN/'review_plan_with_scope_r05.py'
HELPER_SHA = '9d5ec80c5fd3efe2044302104a64ff928777fd98d3cdd0e0c8ef0ff301ee5802'
PREVIOUS = RUN/'jobs/plan-03/plan-verified.json'
PREVIOUS_SHA = 'f302f6d345e87add5a9ac4ef6b0d19f9708dfcb9bdd3c92e3d411795e9d8146d'
PLAN = RUN/'jobs/plan-04/plan-verified.json'
HANDOFF = PLAN.parent/'plan-handoff.json'
EXPECTED_PLAN_SHA = 'e14b5e5acd96aed44c800209efbe452d094cb595f7d57da097b8c9a4a7bc9ee3'
EXPECTED_HANDOFF_SHA = '2815a418a728f5ba8e71ec8a8d0cf7308b1920ecdf283b6ec9288e0831b68660'
OUT = AUDIT/'plan-04-mechanical-precheck-r01.json'

def safe(path):
    path = Path(path).absolute()
    for node in (path, *path.parents):
        if node.is_symlink() or (node.exists() and getattr(node.lstat(), 'st_file_attributes', 0)&0x400):
            raise ValueError('Linked path refused before read/write')
    return path.resolve()

def read(path):
    return safe(path).read_bytes()

def sha(path):
    return hashlib.sha256(read(path)).hexdigest()

def require(value, message):
    if not value:
        raise ValueError(message)

require(sha(HELPER) == HELPER_SHA, 'Fixed scoped helper changed')
require(sha(PREVIOUS) == PREVIOUS_SHA, 'Previous original plan changed')
require(sha(PLAN) == EXPECTED_PLAN_SHA and sha(HANDOFF) == EXPECTED_HANDOFF_SHA,
        'Parent fixed plan04 bytes changed')
require(not safe(OUT).exists(), 'Fresh report required')
spec = importlib.util.spec_from_file_location('scoped_plan04_metadata_guard', safe(HELPER))
guard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(guard)
runtime_before = guard.bootstrap()
plan_sha, handoff_sha = sha(PLAN), sha(HANDOFF)
pin, definition, plan, manifest, original_bytes = guard.current_pin(PLAN, plan_sha, handoff_sha)
previous = json.loads(read(PREVIOUS).decode('utf-8-sig'))
old_docs = {doc['id']: doc for doc in previous['documents']}
docs = {doc['id']: doc for doc in plan['documents']}
require(len(docs) == len(plan['documents']), 'Duplicate document identity')
removed = sorted(set(old_docs)-set(docs))
added = [{key: docs[identity][key] for key in ('id', 'kind', 'path')}
         for identity in sorted(set(docs)-set(old_docs))]
identity_changes = [{'id': identity, 'beforeKind': old_docs[identity]['kind'],
                     'afterKind': docs[identity]['kind'], 'beforePath': old_docs[identity]['path'],
                     'afterPath': docs[identity]['path']}
                    for identity in sorted(set(docs)&set(old_docs))
                    if any(old_docs[identity][key] != docs[identity][key] for key in ('kind', 'path'))]
responsibility_changes = [{'id': identity, 'before': old_docs[identity]['responsibilities'],
                           'after': docs[identity]['responsibilities']}
                          for identity in sorted(set(docs)&set(old_docs))
                          if old_docs[identity]['responsibilities'] != docs[identity]['responsibilities']]
source_changes = [{'id': identity, 'removed': sorted(set(old_docs[identity]['sourcePaths'])-set(docs[identity]['sourcePaths'])),
                   'added': sorted(set(docs[identity]['sourcePaths'])-set(old_docs[identity]['sourcePaths']))}
                  for identity in sorted(set(docs)&set(old_docs))
                  if set(old_docs[identity]['sourcePaths']) != set(docs[identity]['sourcePaths'])]
aliases = sorted({doc['kind'] for doc in docs.values()} &
                 {'detailed-design', 'logical-data', 'database-table'})
kind_counts = dict(Counter(doc['kind'] for doc in plan['documents']))
mandatory = all(kind_counts.get(kind, 0)>0 for kind in
                ('index', 'basic-design', 'detailed-specification', 'database-index',
                 'logical-table-definition', 'physical-table-definition'))
direct = sorted({path for doc in docs.values() for path in doc['sourcePaths']})
previous_direct = {path for doc in old_docs.values() for path in doc['sourcePaths']}
manifest_paths = {entry['path'] for entry in manifest['files']}
guard.recheck(pin, runtime_before)
require(sha(PREVIOUS) == PREVIOUS_SHA and sha(HELPER) == HELPER_SHA,
        'Audit inputs changed while comparing')
result = {
    'schema': 'spec-agent-plan-mechanical-precheck/2',
    'createdUtc': datetime.now(timezone.utc).isoformat(),
    'projectId': 'nenkin', 'plan': str(safe(PLAN)),
    'planSha256': plan_sha, 'handoffSha256': handoff_sha,
    'previousPlanSha256': PREVIOUS_SHA, 'scopedHelperSha256': HELPER_SHA,
    'inputPin': pin, 'runtimeFileCount': runtime_before['runtimeFileCount'],
    'loadedImportCount': len(runtime_before['loadedImports']),
    'criticalModuleCount': len(runtime_before['criticalModules']),
    'documentCount': len(docs), 'previousDocumentCount': len(old_docs),
    'kindCounts': kind_counts, 'removedDocumentIds': removed,
    'addedDocuments': added, 'existingKindOrPathChanges': identity_changes,
    'legacyRoutingAliases': aliases, 'mandatoryCanonicalKindsPresent': mandatory,
    'responsibilityChanges': responsibility_changes, 'sourcePathChanges': source_changes,
    'distinctDirectSourcePaths': len(direct), 'sourceManifestTextCount': len(manifest_paths),
    'pathsNotRawManifestSpelling': [path for path in direct if path not in manifest_paths],
    'newDirectSourcePaths': sorted(set(direct)-previous_direct),
    'removedDirectSourcePaths': sorted(previous_direct-set(direct)),
    'analysisReportCount': kind_counts.get('analysis-report', 0),
    'includedInFinalSpecificationBundleCount': len(docs)-kind_counts.get('analysis-report', 0),
    'mechanicalPreparationEligible': not removed and not identity_changes and not aliases and mandatory,
    'semanticResponsibilityPreservationProven': False,
    'sourceCoverageAndReachabilityApproved': False,
    'providerReviewExecuted': False,
    'preparationToolCorrection': 'Initial local metadata attempt used a nonexistent plan projectId key; no report was saved. Scope identity is fixed by the audited current_pin context guard.',
    'limitations': [
        'Exact metadata comparison is not a proof of semantic responsibility preservation.',
        'Direct source paths are not a dependency closure or evidence of complete raw material reading.',
        'The previous raw review was unverified; its finding is not treated as an established defect.',
        'The current wrapper delivers the full execution scope metadata to downstream roles.',
        'Analysis reports remain report material outside the final specification bundle.'
    ]
}
encoded = (json.dumps(result, ensure_ascii=False, indent=2)+'\n').encode('utf-8')
with safe(OUT).open('xb') as stream:
    stream.write(encoded)
print(json.dumps({'report': str(safe(OUT)), 'reportSha256': sha(OUT),
                  'planSha256': plan_sha, 'handoffSha256': handoff_sha,
                  'documentCount': len(docs), 'kindCounts': kind_counts,
                  'responsibilityChanges': len(responsibility_changes),
                  'sourcePathChanges': len(source_changes),
                  'mechanicalPreparationEligible': result['mechanicalPreparationEligible']},
                 ensure_ascii=False))

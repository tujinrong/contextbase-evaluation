"""Metadata from a closed owned review, with bounded saved tool-output observations.

No source command replay, original application execution, answer edit, or prose generation.
Run only after unified session91430 is observed CLOSED; pass its actual terminal exit code.
"""
from pathlib import Path
from datetime import datetime, timezone
import argparse, collections, hashlib, importlib.util, json, re, sys

sys.dont_write_bytecode = True
R = Path(r'D:/開発/contextbase-evaluation/agents/spec-agent/.tmp/20261014-nenkin-high-01')
P = Path(r'D:/開発/contextbase-evaluation/agents/spec-agent/report/20261014-nenkin-high-01')
A = P/'independent-audit'
HELPER = R/'review_plan_with_scope_r06.py'
HELPER_SHA = '21b518c3fde79a6036b7c4e98cddc9d34489f1ed013cc4a9151687555c682fc8'
PREP = P/'independent-plan-review/independent-plan-review-05/preparation.json'
PREP_SHA = 'f1005f1f5614e71f1ad4bb83fccc9be8ebee8bbf1369076bdeb2caab697ebd09'
JOB = R/'jobs/independent-plan-review-05'
PLAN = R/'jobs/plan-04/plan-verified.json'
PLAN_SHA = 'e14b5e5acd96aed44c800209efbe452d094cb595f7d57da097b8c9a4a7bc9ee3'
HANDOFF_SHA = '2815a418a728f5ba8e71ec8a8d0cf7308b1920ecdf283b6ec9288e0831b68660'

def safe(path):
    path = Path(path).absolute()
    for node in (path, *path.parents):
        if node.is_symlink() or (node.exists() and getattr(node.lstat(), 'st_file_attributes', 0)&0x400):
            raise ValueError('Linked path refused before read/write')
    return path.resolve()

def require(value, message):
    if not value:
        raise ValueError(message)

def initial_sha(path):
    return hashlib.sha256(safe(path).read_bytes()).hexdigest()

parser = argparse.ArgumentParser()
parser.add_argument('--terminal-exit-code', type=int, choices=(0, 1), required=True)
args = parser.parse_args()
require(initial_sha(HELPER) == HELPER_SHA, 'Fixed approved helper bytes changed')
spec = importlib.util.spec_from_file_location('terminal_scoped_guard_r06', safe(HELPER))
g = importlib.util.module_from_spec(spec)
spec.loader.exec_module(g)
require(g.sha(PREP) == PREP_SHA, 'Fixed approved preparation bytes changed')
bp = R/'jobs/independent-plan-review-05-plan-review-before.json'
ap = R/'jobs/independent-plan-review-05-plan-review-after.json'
before, after = g.load(bp), g.load(ap)
require(before['input'] == after['input'] and
        before['preparationSha256'] == after['preparationSha256'] == PREP_SHA,
        'Review scope sidecar binding mismatch')
runtime = g.bootstrap()
require(runtime == before['runtime'], 'Current runtime differs from review initial runtime')
pin, _, plan, manifest, _ = g.current_pin(PLAN, PLAN_SHA, HANDOFF_SHA)
require(pin == before['input'], 'Current plan input differs from review initial input')
sbp = R/'jobs/independent-plan-review-05-snapshot-before.json'
sap = R/'jobs/independent-plan-review-05-snapshot-after.json'
sb, sa = g.load(sbp), g.load(sap)
require(sa == {'status': 'UNCHANGED', 'before': sb, 'after': sb} and sb == pin['snapshot'],
        'Provider capsule before/after differs')
answer = g.load(JOB/'answer.txt')
raw_sha = g.sha(JOB/'answer.txt')
provider_result = g.load(JOB/'result.json')
metadata = provider_result['metadata']
from contextbase.ai import plan_review, provider
require(provider_result['answer'] == answer and provider_result['exit_code'] == 0 and
        metadata['status'] == 'passed' and g.safe(metadata['workspace']) == g.safe(g.SNAPSHOT) and
        metadata['reference_mode'] == 'source-only' and metadata['input_execution_policy'] == 'forbidden',
        'Raw provider result identity or status mismatch')
require(g.load(JOB/'schema.json') == plan_review.PLAN_REVIEW, 'Provider review schema differs')
require(g.read(JOB/'prompt.txt') ==
        (provider.COMMON_POLICY+'\nUser task (within that boundary):\n').encode('utf-8')+
        g.read(PREP.parent/'prepared-prompt.txt') and
        metadata['prompt_sha256'] == g.sha(JOB/'prompt.txt'),
        'Provider effective prompt bytes differ from fixed approved prepared prompt')
validated = after['status'] == 'UNCHANGED_AND_REVIEW_VALIDATED'
verified, handoff = JOB/'plan-review-verified.json', JOB/'plan-review-handoff.json'
if validated:
    require(args.terminal_exit_code == 0 and after['runtime'] == runtime,
            'Closed result differs from successful scoped sidecar')
    require(g.read(verified) == g.read(JOB/'answer.txt'), 'Verified bytes differ from original raw answer')
    plan_review._validate(answer, plan, manifest)
    h = g.load(handoff)
    require(h['reviewSha256'] == raw_sha and h['approved'] == answer['approved'] and
            h['scopePreparationSha256'] == PREP_SHA and
            h['aiResponseBytesModified'] is False and h['snapshot'] == pin['snapshot'],
            'Verified handoff binding mismatch')
else:
    require(after['status'] == 'REVIEW_NOT_VERIFIED' and args.terminal_exit_code == 1 and
            not safe(verified).exists() and not safe(handoff).exists(),
            'Failure cannot claim a verified review/handoff')

commands, eventtypes = [], collections.Counter()
for line in g.safe(JOB/'events.jsonl').read_text(encoding='utf-8-sig').splitlines():
    event = json.loads(line)
    eventtypes[event.get('type', 'unknown')] += 1
    item = event.get('item', {})
    if event.get('type') == 'item.completed' and item.get('type') == 'command_execution':
        commands.append(item)
entries = {entry['path']: entry for entry in manifest['files']}
alias = {path: path for path in entries}
for path, entry in entries.items():
    alias['sources/'+path] = path
    alias[entry['indexed']] = path
canonical_declared = {alias[path] for path in answer['sourcePathsRead'] if path in alias}
observations, returned, mentioned, families = [], set(), set(), collections.Counter()
for command in commands:
    cmd, out = command['command'], command.get('aggregated_output', '')
    body = cmd.split('-Command ', 1)[-1].strip().lstrip('"\'')
    family = body.split(None, 1)[0] if body else 'unknown'
    families[family] += 1
    listing = family == 'rg' and '--files' in body
    mentions = {path for spelling, path in alias.items() if spelling in cmd and
                ('sources/'+path in cmd or entries[path]['indexed'] in cmd)}
    content = set()
    if not listing:
        for path, entry in entries.items():
            if any(re.search(r'(?m)^'+re.escape(spelling)+r':\d+:', out)
                   for spelling in ('sources/'+path, entry['indexed'])):
                content.add(path)
    if (not listing and family == 'rg' and '-n' in body and len(mentions) == 1 and
            command.get('exit_code') == 0 and re.search(r'(?m)^\d+:', out)):
        content.update(mentions)
    returned.update(content)
    mentioned.update(mentions)
    observations.append({'eventItemId': command.get('id'), 'exitCode': command.get('exit_code'),
                         'status': command.get('status'), 'commandFamily': family,
                         'inventoryOnly': listing,
                         'commandSha256': hashlib.sha256(cmd.encode()).hexdigest(),
                         'outputSha256': hashlib.sha256(out.encode()).hexdigest(),
                         'literalSourcePathMentions': sorted(mentions),
                         'returnedContentPathObservations': sorted(content)})
empty_evidence = [{'group': group, 'id': item.get('id', item.get('documentId')),
                   'basis': item['basis'], 'referenceCount': 0}
                  for group in ('subjects', 'documentCoverage', 'reachability', 'findings',
                                'blockingUnresolved', 'scopeLimits')
                  for item in answer[group]
                  if item['basis'] != 'plan-structure' and not item['references']]
files = [*g.safe(JOB).iterdir(), bp, ap, PREP, HELPER, sbp, sap]
artifacts = {str(g.safe(path)): g.sha(path) for path in files if g.safe(path).is_file()}
limitations = [
    'Literal command/path mentions do not prove file contents were read.',
    'Returned rg lines demonstrate bounded partial returned content only, not complete file coverage or semantic comprehension.',
    'Directory searches, unqualified outputs and truncated outputs may omit a matched path observation; absence is not proof no read occurred.',
    'SourcePathsRead is the original AI declaration, not a mechanical proof of full reading.',
    'No saved command, original application, database or source program was replayed.',
    'Unsealed n2framework IDE declarations and compiled artifacts remain unassessed; all345 semantic analysis is not claimed.'
]
obs = {'schema': 'spec-agent-plan-review-tool-observations/1',
       'createdUtc': datetime.now(timezone.utc).isoformat(), 'job': str(g.safe(JOB)),
       'eventsSha256': g.sha(JOB/'events.jsonl'), 'rawAnswerSha256': raw_sha,
       'declaredReadPathCount': len(answer['sourcePathsRead']),
       'declaredUniqueCanonicalSourceCount': len(canonical_declared),
       'manifestTextSourceCount': len(entries), 'completedCommandCount': len(commands),
       'exitCounts': dict(collections.Counter(str(item.get('exit_code')) for item in commands)),
       'commandFamilyCounts': dict(families), 'eventTypes': dict(eventtypes),
       'literalSourcePathMentionCount': len(mentioned),
       'returnedContentPathObservationCount': len(returned), 'returnedContentPaths': sorted(returned),
       'declaredCanonicalWithoutReturnedPathObservation': sorted(canonical_declared-returned),
       'commands': observations, 'commandsReplayed': False,
       'allDeclaredSourcesFullyReadProven': False, 'semanticComprehensionProven': False,
       'limitations': limitations}
obsfile, terminalfile = A/'plan-review-05-tool-observations-r01.json', A/'plan-review-05-terminal-r01.json'
require(not g.safe(obsfile).exists() and not g.safe(terminalfile).exists(), 'Fresh terminal evidence required')
require(all(g.sha(path) == digest for path, digest in artifacts.items()), 'Original artifacts changed')
g.recheck(pin, runtime)
with g.safe(obsfile).open('x', encoding='utf-8', newline='\n') as stream:
    json.dump(obs, stream, ensure_ascii=False, indent=2)
    stream.write('\n')
terminal = {'schema': 'spec-agent-independent-plan-review-terminal/1',
            'createdUtc': datetime.now(timezone.utc).isoformat(), 'ownedUnifiedSessionId': 91430,
            'observedTerminalExitCode': args.terminal_exit_code,
            'reviewProtocolValidated': validated, 'rawApproved': answer['approved'],
            'rawFindingCount': len(answer['findings']),
            'rawFindingSeverities': dict(collections.Counter(item['severity'] for item in answer['findings'])),
            'rawBlockingUnresolvedCount': len(answer['blockingUnresolved']),
            'rawScopeLimitsCount': len(answer['scopeLimits']),
            'rawSubjectCount': len(answer['subjects']),
            'rawDocumentCoverageCount': len(answer['documentCoverage']),
            'rawReachabilityCount': len(answer['reachability']),
            'rawDeclaredReadCount': len(answer['sourcePathsRead']),
            'rawAnswerSha256': raw_sha, 'job': str(g.safe(JOB)), 'input': pin,
            'preparationSha256': PREP_SHA, 'emptyEvidenceObjects': empty_evidence,
            'errorType': after.get('errorType'), 'error': after.get('error'),
            'providerSnapshotBeforeAfterUnchanged': True, 'scopeInputCurrentEqualsBefore': True,
            'providerRawAnswerSchemaAndFixedEffectivePromptVerified': True,
            'runtime128Files13Imports7CriticalCurrentEqualsBefore': True,
            'verifiedReviewFile': str(g.safe(verified)) if validated else None,
            'verifiedReviewSha256': g.sha(verified) if validated else None,
            'handoffSha256': g.sha(handoff) if validated else None,
            'artifacts': artifacts, 'toolObservations': str(g.safe(obsfile)),
            'toolObservationsSha256': g.sha(obsfile), 'aiResponseBytesModified': False,
            'oldApprovalOrFindingTransferred': False,
            'fullExecutionScopeMetadataDeliveredByCurrentWrapper': True,
            'formalPercentage': None, 'semanticComprehensionMechanicallyProven': False,
            'targetApplicationOrDatabaseExecutedByAuditor': False, 'limitations': limitations}
require(all(g.sha(path) == digest for path, digest in artifacts.items()), 'Original artifacts changed before terminal save')
g.recheck(pin, runtime)
with g.safe(terminalfile).open('x', encoding='utf-8', newline='\n') as stream:
    json.dump(terminal, stream, ensure_ascii=False, indent=2)
    stream.write('\n')
print(json.dumps({'terminal': str(g.safe(terminalfile)), 'terminalSha256': g.sha(terminalfile),
                  'toolObservationsSha256': g.sha(obsfile), 'rawAnswerSha256': raw_sha,
                  'protocolValidated': validated, 'approved': answer['approved'],
                  'findings': len(answer['findings']), 'blocking': len(answer['blockingUnresolved']),
                  'declaredPaths': len(answer['sourcePathsRead']), 'returnedContentObservedPaths': len(returned),
                  'completedCommands': len(commands)}, ensure_ascii=False))

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(r'D:\開発\contextbase-evaluation\agents\reverse-agent\test-report\20261013-rerun-12h')
PROV = ROOT / 'evaluator-only/batches/assisted-search-detail-r02-r6-retry01/retry-provenance.json'
RECEIPT = ROOT / 'evaluator-only/checkpoints/search-detail-first-phase-terminal-r01.json'
HELPER = ROOT / 'evaluator-only/retry_partial_batch_r01.py'
PIN = '25a51057284b23906380b9d9191f42970205c5c554debd21e004cfa823ffea5f'
HELPER_PIN = 'a6453e61c716f275865d418d5ef59ee70b0e2d2dfed284fac95909f74322b9bf'

def read_metadata(path):
    if not path.is_absolute() or not path.is_relative_to(ROOT):
        raise ValueError('Outside metadata audit root')
    for part in reversed((path, *path.parents)):
        if part.is_symlink() or part.is_junction():
            raise ValueError('Linked metadata path')
    return path.read_bytes()

raw = read_metadata(PROV)
receipt_raw = read_metadata(RECEIPT)
helper_raw = read_metadata(HELPER)
p = json.loads(raw)
c = json.loads(receipt_raw)
sha = lambda value: hashlib.sha256(value).hexdigest()
checks = []
def check(name, condition):
    checks.append({'name': name, 'passed': bool(condition)})
    if not condition:
        raise AssertionError(name)

check('fixed terminal receipt SHA', sha(receipt_raw) == PIN)
check('unchanged audited helper SHA', sha(helper_raw) == HELPER_PIN)
check('provenance schema', p['schema'] == 'independent-evaluation-immutable-partial-retry/1')
check('closed controller metadata', p['controllerExited'] is True and type(p['controllerExitCode']) is int and p['controllerExitCode'] == 1 and p['startedJobLimit'] == 2 and p['allStartedJobsTerminal'] is True)
check('root receipt binding', p['completionReceiptSha256'] == PIN and p['completionReceipt'] == str(RECEIPT) and p['sourceBatch'] == c['sourceBatch'] and p['sourceBatchManifestSha256'] == c['sourceBatchManifestSha256'])
check('one reuse one retry eighteen unstarted', p['totalJobCount'] == 20 and len(p['reusedAcceptedJobs']) == 1 and len(p['retryJobs']) == 1 and len(p['unstartedJobs']) == 18)
original = p['originalInventory']
files, dirs = original['files'], set(original['directories'])
copied = p['copiedFileHashes']
check('all inventory hashes valid', all(re.fullmatch('[0-9a-f]{64}', digest) for digest in [*files.values(), *copied.values()]))
check('all recorded relative paths plain', all(not path.startswith('/') and '\\' not in path and '..' not in path.split('/') for path in [*files, *copied, *dirs]))
ids = [j['shardId'] for j in p['reusedAcceptedJobs'] + p['retryJobs'] + p['unstartedJobs']]
check('twenty unique sequential shards', len(set(ids)) == 20 and set(ids) == {f'CSHARP_ASPNET-DET-CSharp_ASPNET-SCR-STU-001-S{i:03d}' for i in range(1, 21)})
reused, retried = p['reusedAcceptedJobs'][0], p['retryJobs'][0]
check('terminal job root receipt pins', c['terminalJobs'][0]['shardId'] == retried['shardId'] and c['terminalJobs'][0]['status'] == retried['previousStatus'] == 'TIMEOUT' and c['terminalJobs'][0]['resultSha256'] == retried['previousResultSha256'] and c['terminalJobs'][1]['shardId'] == reused['shardId'] and c['terminalJobs'][1]['status'] == reused['previousStatus'] == 'PASSED' and c['terminalJobs'][1]['resultSha256'] == reused['previousResultSha256'])
accepted_prefix = 'jobs/' + reused['shardId'] + '/'
expected_copied = {name: digest for name, digest in files.items() if name.startswith('capsule/') or name.startswith(accepted_prefix) or name in ('batch.json', 'answer-schema.json', 'canonical-pin.json')}
expected_copied['partial-controller-terminal-receipt.json'] = PIN
check('copied hash map exactly accepted subtree plus capsule and three pins and receipt', copied == expected_copied)
check('accepted answer original and copied SHA', files[accepted_prefix + 'answer.txt'] == copied[accepted_prefix + 'answer.txt'] == reused['answerSha256'])
check('accepted result original and copied SHA', files[accepted_prefix + 'result.json'] == copied[accepted_prefix + 'result.json'] == reused['previousResultSha256'])
check('failed source raw retained in original inventory', any(name.startswith('jobs/' + retried['shardId'] + '/') for name in files))
check('failed and unstarted raw excluded from copied map', all(j['rawCopiedToRetry'] is False and not any(name.startswith('jobs/' + j['shardId'] + '/') for name in copied) for j in p['retryJobs'] + p['unstartedJobs']))
check('unstarted absent from recorded original directories', all('jobs/' + j['shardId'] not in dirs for j in p['unstartedJobs']))
request_names = {name for name in files if name.startswith('capsule/requests/')}
check('twenty requests same recorded hashes', len(request_names) == 20 and all(copied[name] == files[name] for name in request_names))
check('original manifest pin retained', files['batch.json'] == copied['batch.json'] == p['sourceBatchManifestSha256'])
check('original before after immutability recorded', p['originalBeforeAfterUnchanged'] is True and p['originalBatchModified'] is False)
check('no rewritten fabricated data or preparation provider recorded', p['answerContentRewritten'] is False and p['rubricOrCanonicalChanged'] is False and p['unstartedAnswersOrResultsFabricated'] is False and p['providerExecutedByPreparation'] is False)
check('no score or formal completion claim', p['qualityScore'] is None and p['formallyComplete'] is False)
check('metadata bytes unchanged during audit', read_metadata(PROV) == raw and read_metadata(RECEIPT) == receipt_raw and read_metadata(HELPER) == helper_raw)
report = {
    'schema': 'independent-partial-retry-metadata-audit/1',
    'createdAt': datetime.now(timezone.utc).isoformat(),
    'scope': 'METADATA_ONLY_PREPARATION_PROVENANCE_CONSISTENCY',
    'subject': str(PROV), 'subjectSha256': sha(raw),
    'completionReceipt': str(RECEIPT), 'completionReceiptSha256': sha(receipt_raw),
    'auditedHelper': str(HELPER), 'auditedHelperSha256': sha(helper_raw),
    'checks': checks, 'passed': len(checks), 'failed': 0,
    'recordedOriginalFiles': len(files), 'recordedOriginalDirectories': len(dirs),
    'recordedCopiedFiles': len(copied), 'requests': len(request_names),
    'acceptedAnswerHashOriginalEqualsCopy': True,
    'failedAndUnstartedFilesAbsentAtPreparationAsRecorded': True,
    'originalBeforeAfterInvariantAsRecorded': True,
    'liveOriginalBytesIndependentlyRead': False,
    'liveRetryDirectoryAbsenceAsserted': False,
    'scopeLimit': 'The controller is now active. This audit checks the immutable preparation metadata and audited helper contract; it does not re-read grading content or make a current job-directory absence claim.',
    'actualAnswerBodyReads': 0, 'capsuleReferenceOrExpectedBodyReads': 0,
    'providerRuns': 0, 'originalAppRuns': 0, 'gradingDataMutations': 0,
    'findings': [], 'qualityScore': None,
}
out = Path(__file__).with_name('review.json')
with out.open('x', encoding='utf-8', newline='\n') as handle:
    json.dump(report, handle, ensure_ascii=False, indent=2)
    handle.write('\n')
print(json.dumps({'checks': len(checks), 'passed': len(checks), 'report': str(out), 'reportSha256': sha(out.read_bytes()), 'provenanceSha256': sha(raw)}, ensure_ascii=False))

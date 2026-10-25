"""Run the actual report publisher against disposable current/stale evidence.

Only fixture copies are poisoned. No executable, database, canonical suite
record, or specification is executed or modified by this regression.
"""
import sys
sys.dont_write_bytecode = True

from pathlib import Path
import datetime
import hashlib
import json
import os
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from evidence import compiled_inputs, binary_hashes, binary_path
from checked_sources import checked_source_hashes
from output_paths import ensure_directory, reset_work, write_json

RUN = os.environ.get('COBOL_RUN_ID', '20261025-regenerate')
RECORD = ROOT / 'build/test-results/report-provenance-regression.json'
SUITES = {
    'host': 'build/test-results/host-tests/host-tests.json',
    'static': 'build/test-results/static/static.json',
    'text': 'build/test-results/text/text.json',
}
BASE_RECORDS = [
    'build/test-results/host-build/host-build.json',
    *SUITES.values(),
    '.tmp/host/build-evidence.json',
    'build/input-manifest.json',
    'build/test-results/summary.json',
    'build/test-results/README.md',
]
HELPERS = [
    'tools/write_report.py', 'tools/evidence.py', 'tools/output_paths.py',
    'tools/checked_sources.py', 'tools/host_tests.py',
    'tools/static_check.py', 'tools/test_text.py',
]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def under(root, relative):
    target = root / relative
    if not target.resolve().is_relative_to(root.resolve()):
        raise ValueError('Fixture member escaped its root: ' + relative)
    return target


def put(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes((json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode('utf-8'))


def main():
    start = datetime.datetime.now(datetime.timezone.utc).isoformat()
    inputs, binaries, checked = compiled_inputs(), binary_hashes(), checked_source_hashes()
    members = sorted(set(inputs) | set(checked) | set(HELPERS) | set(BASE_RECORDS))
    binary_members = {name: binary_path(name).relative_to(ROOT).as_posix() for name in binaries}
    members = sorted(set(members) | set(binary_members.values()))
    snapshots = {name: under(ROOT, name).read_bytes() for name in members}
    before = {name: hashlib.sha256(data).hexdigest() for name, data in snapshots.items()}
    scratch = reset_work(ROOT / '.tmp/report-provenance-regression')
    fixture = ensure_directory(scratch / 'method')
    for name, data in snapshots.items():
        target = under(fixture, name)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    if (fixture / 'spec').exists():
        raise AssertionError('Specifications must not be copied into the fixture')

    env = os.environ.copy()
    env.update(COBOL_RUN_ID=RUN, PYTHONDONTWRITEBYTECODE='1', PYTHONUTF8='1')
    cases = []
    changed_members = set()

    def case(name, poison=None, success=False):
        # Restore fixture records/files only. Existing real evidence remains read-only.
        for member in set(BASE_RECORDS) | changed_members:
            target = under(fixture, member)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(snapshots[member])
        changed_members.clear()
        summary = fixture / 'build/test-results/summary.json'
        put(summary, {'status': 'PASSED', 'buildSucceeded': True,
                      'applicationVerification': 'OLD_PASS', 'formalScore': 100})
        if poison:
            poison()
        command = [sys.executable, '-X', 'utf8', str(fixture / 'tools/write_report.py')]
        result = subprocess.run(command, cwd=fixture, env=env, capture_output=True, timeout=30)
        current = json.loads(summary.read_text(encoding='utf-8'))
        expected = 'VERIFIED_WITH_LIMITS' if success else 'VERIFICATION_FAILED'
        good = (result.returncode == 0 if success else result.returncode != 0)
        good = good and current.get('status') == expected and current.get('formalScore', 'missing') is None
        if not success:
            good = good and current.get('buildSucceeded') is False
            good = good and current.get('applicationVerification') == 'NOT_ESTABLISHED'
        log = result.stdout.decode('utf-8', 'replace') + result.stderr.decode('utf-8', 'replace')
        (scratch / (name + '.log')).write_bytes(log.encode('utf-8'))
        cases.append({'id': name, 'passed': good, 'exitCode': result.returncode,
                      'summaryStatus': current.get('status'), 'formalScore': current.get('formalScore'),
                      'failure': current.get('failure'), 'command': command,
                      'fixtureLog': (scratch / (name + '.log')).relative_to(ROOT).as_posix()})
        print(name, 'PASS' if good else 'FAIL', flush=True)

    def stale_field(member, field, value):
        def poison():
            path = under(fixture, member)
            data = json.loads(path.read_text(encoding='utf-8'))
            data[field] = value
            put(path, data)
        return poison

    def stale_map(member, field):
        def poison():
            path = under(fixture, member)
            data = json.loads(path.read_text(encoding='utf-8'))
            key = sorted(data[field])[0]
            data[field][key] = '0' * 64
            put(path, data)
        return poison

    def tamper(member):
        def poison():
            path = under(fixture, member)
            path.write_bytes(path.read_bytes() + b'\n/* isolated provenance regression */\n')
            changed_members.add(member)
        return poison

    case('current-evidence-replaces-old-pass', success=True)
    for suite, member in SUITES.items():
        case(suite + '-old-run', stale_field(member, 'runId', 'old-regeneration-run'))
        case(suite + '-old-input-manifest', stale_field(member, 'inputManifestSha256', '0' * 64))
        case(suite + '-old-runner', stale_field(member, 'runnerSha256', '0' * 64))
        case(suite + '-old-compiled-source', stale_map(member, 'compiledInputs'))
        case(suite + '-old-binary', stale_map(member, 'binaryHashes'))
    build = 'build/test-results/host-build/host-build.json'
    proof = '.tmp/host/build-evidence.json'
    case('build-old-run', stale_field(build, 'runId', 'old-regeneration-run'))
    case('build-old-input-manifest', stale_field(build, 'inputManifestSha256', '0' * 64))
    case('proof-old-compiled-source', stale_map(proof, 'compiledInputs'))
    case('proof-old-binary', stale_map(proof, 'binaries'))
    sql = next(name for name in sorted(checked) if name.startswith('sql/') and name.endswith('.sql'))
    ddl = next(name for name in sorted(checked) if name.startswith('database/') and name.endswith('.sql'))
    case('static-sql-body-changed', tamper(sql))
    case('static-ddl-body-changed', tamper(ddl))
    case('current-evidence-restored-after-negative-cases', success=True)

    after = {name: sha(under(ROOT, name)) for name in members}
    canonical_unchanged = before == after
    cases.append({'id': 'canonical-inputs-records-and-binaries-unchanged', 'passed': canonical_unchanged,
                  'checkedFiles': len(members)})
    passed = sum(row['passed'] for row in cases)
    record = {
        'runId': RUN, 'profileId': 'COBOL', 'recordedAt': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'startedAt': start, 'status': 'PASSED' if passed == len(cases) else 'FAILED',
        'passed': passed, 'total': len(cases), 'results': cases,
        'scope': 'Actual write_report subprocess against isolated copies; stale PASS invalidation; no application/DB execution',
        'compiledInputFilesCopied': len(inputs), 'checkedSourceFilesCopied': len(checked),
        'binaryFilesCopied': len(binaries), 'binaryMembers': binary_members,
        'canonicalInputsUnchanged': canonical_unchanged,
        'sourceHashes': {name: sha(ROOT / name) for name in [*HELPERS, 'tests/report-provenance-regression.py']},
        'canonicalRecordHashes': {name: before[name] for name in BASE_RECORDS},
        'fixtureRoot': fixture.relative_to(ROOT).as_posix(),
        'notExecuted': ['binaries or compilers', 'real database', 'manual Console/IME acceptance', 'formal scoring'],
        'formalScore': None,
    }
    write_json(RECORD, record)
    print(json.dumps({'status': record['status'], 'passed': passed, 'total': len(cases),
                      'canonicalInputsUnchanged': canonical_unchanged, 'binaryFilesCopied': len(binaries)}))
    return 0 if record['status'] == 'PASSED' else 1


if __name__ == '__main__':
    raise SystemExit(main())

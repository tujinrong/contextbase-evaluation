"""Compare protected input bytes with the run's original seal; read only."""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[5]
REPORT = REPO / 'agents/reverse-agent/test-report/20261013-rerun-12h'
SUBJECT = REPO / 'test-project1/srcs/CSharp_ASPNET'
EXCLUDED = {'.git', '.vs', 'bin', 'obj'}

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    if not output.is_relative_to(REPORT.resolve()):
        raise ValueError('Verification output must be inside this run report')
    before_path = REPORT / 'protected-inputs-before.json'
    before = json.loads(before_path.read_text(encoding='utf-8'))
    expected = {record['path']: record for record in before['files']}
    actual = {}
    for path in sorted(SUBJECT.rglob('*')):
        if not path.is_file() or any(part.casefold() in EXCLUDED for part in path.relative_to(SUBJECT).parts):
            continue
        if not path.resolve().is_relative_to(SUBJECT.resolve()):
            raise ValueError('Protected input resolves outside the original source tree')
        actual[path.relative_to(REPO).as_posix()] = {'bytes': path.stat().st_size, 'sha256': sha(path)}
    changed = [key for key in expected.keys() & actual.keys()
               if any(expected[key][field] != actual[key][field] for field in ('bytes', 'sha256'))]
    result = {
        'schema': 'protected-input-verification/1',
        'observedAt': datetime.now(timezone.utc).isoformat(),
        'beforeSealSha256': sha(before_path), 'protectedFiles': len(expected),
        'observedFiles': len(actual), 'changed': sorted(changed),
        'missing': sorted(expected.keys() - actual.keys()),
        'added': sorted(actual.keys() - expected.keys()),
    }
    result['unchanged'] = not any(result[key] for key in ('changed', 'missing', 'added'))
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    print(json.dumps(result, ensure_ascii=False))
    raise SystemExit(0 if result['unchanged'] else 1)

if __name__ == '__main__':
    main()

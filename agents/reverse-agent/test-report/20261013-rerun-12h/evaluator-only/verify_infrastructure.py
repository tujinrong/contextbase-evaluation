"""Record current integrity tests and fixed runtime; not a specification grade."""
from datetime import datetime, timezone
import argparse
import ast
import io
from pathlib import Path
import unittest
import grader

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--name', default='infrastructure-verification-final')
    args = parser.parse_args()
    if not args.name or any(c not in 'abcdefghijklmnopqrstuvwxyz0123456789-_' for c in args.name):
        parser.error('Verification name must be a plain lowercase filename stem')
    here = Path(__file__).resolve().parent
    runtime = grader.runtime_pin()
    from jsonschema import Draft202012Validator
    Draft202012Validator.check_schema(grader.SCHEMA)
    for filename in ('grader.py', 'freeze_rubric.py', 'normalize_defects.py'):
        ast.parse((here / filename).read_text(encoding='utf-8'))
    stream = io.StringIO()
    suite = unittest.defaultTestLoader.discover(str(here), pattern='test_grader.py')
    result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
    log = here / (args.name + '.raw.log')
    with log.open('x', encoding='utf-8') as output:
        output.write(stream.getvalue())
    grader.save(here / (args.name + '.json'), {
        'schema': 'evaluator-infrastructure-verification/1', 'verifiedAt': datetime.now(timezone.utc).isoformat(),
        'status': 'PASS' if result.wasSuccessful() else 'FAIL', 'tests': result.testsRun,
        'failures': len(result.failures), 'errors': len(result.errors), 'runtime': runtime,
        'graderSha256': grader.digest(here / 'grader.py'), 'testsSha256': grader.digest(here / 'test_grader.py'),
        'normalizerSha256': grader.digest(here / 'normalize_defects.py'), 'rawLogSha256': grader.digest(log),
        'rubricRows': 7079, 'rubricMaximumPoints': 8682, 'specificationGradingPerformed': False})
    historical = here / 'infrastructure-verification-session-deps.json'
    if not historical.exists():
        grader.save(historical, {'schema': 'evaluator-infrastructure-historical-note/1',
            'runtimePhase': 'bundle Python 3.12 with session-python-deps jsonschema4.26.0',
            'tests': 13, 'status': 'PASS', 'evidence': 'Prior live unittest tool invocation, 13 tests OK; raw log was not captured to a file.',
            'supersededBy': 'infrastructure-verification-final.json', 'formalGradingQualification': False})
    print(stream.getvalue())
    print('Fixed runtime jsonschema:', runtime['jsonschemaVersion'])
    if not result.wasSuccessful():
        raise SystemExit(1)

if __name__ == '__main__':
    main()

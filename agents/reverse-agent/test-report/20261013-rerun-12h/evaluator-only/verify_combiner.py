"""Run synthetic combination integrity checks, never benchmark-grade a draft."""
from datetime import datetime, timezone
import argparse
import ast
import io
from pathlib import Path
import unittest
import grader
import combine_batches

def main():
    here = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser()
    parser.add_argument('--name', default='combiner-verification')
    args = parser.parse_args()
    if not args.name or Path(args.name).name != args.name or any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_' for c in args.name):
        raise ValueError('Verification name must be a plain artifact filename stem')
    from jsonschema import Draft202012Validator
    schema = grader.load(here / 'batch-selection.schema.json')
    Draft202012Validator.check_schema(schema)
    ast.parse((here / 'combine_batches.py').read_text(encoding='utf-8'))
    stream = io.StringIO()
    tests = unittest.defaultTestLoader.discover(str(here), pattern='test_combine_batches.py')
    result = unittest.TextTestRunner(stream=stream, verbosity=2).run(tests)
    log = here / (args.name + '.raw.log')
    with log.open('x', encoding='utf-8') as output:
        output.write(stream.getvalue())
    grader.save(here / (args.name + '.json'), {'schema': 'evaluator-combiner-verification/1',
        'verifiedAt': datetime.now(timezone.utc).isoformat(), 'status': 'PASS' if result.wasSuccessful() else 'FAIL',
        'tests': result.testsRun, 'failures': len(result.failures), 'errors': len(result.errors),
        'runtime': grader.runtime_pin(), 'combinerSha256': grader.digest(here / 'combine_batches.py'),
        'testsSha256': grader.digest(here / 'test_combine_batches.py'),
        'selectionSchemaSha256': grader.digest(here / 'batch-selection.schema.json'),
        'fixedSnapshots': combine_batches.FIXED_SNAPSHOTS,
        'rawLogSha256': grader.digest(log), 'specificationGradingPerformed': False})
    print(stream.getvalue())
    if not result.wasSuccessful():
        raise SystemExit(1)

if __name__ == '__main__':
    main()

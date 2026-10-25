"""Exercise destructive-output guards against disposable Windows junctions/links."""
import sys
sys.dont_write_bytecode = True
from pathlib import Path
import datetime
import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from output_paths import ensure_directory, write_json

checks = []
def check(name, condition):
    checks.append({'name': name, 'passed': bool(condition)})
    if not condition:
        raise AssertionError(name)

def rejected(name, action):
    try:
        action()
    except ValueError:
        check(name, True)
    else:
        check(name, False)

scratch = ensure_directory(ROOT / '.tmp/output-regression')
with tempfile.TemporaryDirectory(prefix='fixture-', dir=scratch) as temporary:
    fixture = Path(temporary)
    method = fixture / 'method'
    (method / 'tools').mkdir(parents=True)
    shutil.copyfile(ROOT / 'tools/output_paths.py', method / 'tools/output_paths.py')
    spec = importlib.util.spec_from_file_location('isolated_output_paths', method / 'tools/output_paths.py')
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    poison = fixture / 'input'
    poison.mkdir()
    marker = poison / 'protected.txt'
    marker.write_bytes(b'INPUT MUST SURVIVE')
    links = []
    def junction(link, target):
        link.parent.mkdir(parents=True, exist_ok=True)
        result = subprocess.run(['cmd', '/d', '/c', 'mklink', '/J', str(link), str(target)], capture_output=True)
        check('junction created: ' + link.name, result.returncode == 0)
        links.append(link)
    try:
        junction(method / '.tmp', poison)
        rejected('work root junction rejected', lambda: helper.reset_work(method / '.tmp/host'))
        check('work junction did not delete input', marker.read_bytes() == b'INPUT MUST SURVIVE')
        os.rmdir(links.pop())
        (method / '.tmp').mkdir()
        junction(method / 'build/test-results', poison)
        rejected('report junction rejected', lambda: helper.result_dir('suite'))
        check('report junction did not create suite', not (poison / 'suite').exists())
        os.rmdir(links.pop())
        nested = method / '.tmp/host'
        nested.mkdir()
        junction(nested / 'nested', poison)
        rejected('nested cleanup junction rejected', lambda: helper.reset_work(nested))
        check('nested cleanup did not delete input', marker.read_bytes() == b'INPUT MUST SURVIVE')
        os.rmdir(links.pop())
        rejected('entire work root reset rejected', lambda: helper.reset_work(method / '.tmp'))
        rejected('external report root rejected', lambda: helper.result_dir('suite', poison))
        rejected('suite traversal rejected', lambda: helper.result_dir('../input'))
        output = helper.result_dir('suite') / 'result.json'
        os.link(marker, output)
        helper.write_json(output, {'current': 1})
        check('atomic write preserves hardlinked input', marker.read_bytes() == b'INPUT MUST SURVIVE')
        helper.write_json(output, {'current': 2})
        check('fixed output replaced with latest', json.loads(output.read_text('utf-8')) == {'current': 2})
        helper.reset_work(nested)
        check('valid scratch reset succeeds', nested.is_dir() and not list(nested.iterdir()))
        shutil.copyfile(ROOT / 'build.py', method / 'build.py')
        summary = method / 'build/test-results/summary.json'
        summary.write_text('{"status":"PASS","formalScore":100}', encoding='utf-8')
        env = os.environ.copy()
        env['COBOL_RUN_ID'] = 'negative-build-fixture'
        result = subprocess.run([sys.executable, '-X', 'utf8', method / 'build.py', '--sdk', method / 'missing-sdk',
                                 '--cc', method / 'missing-compiler.exe'], env=env, capture_output=True)
        current = json.loads(summary.read_text('utf-8'))
        check('missing compiler build fails', result.returncode != 0)
        check('failed rebuild invalidates old PASS', current['status'] == 'BUILD_FAILED')
        check('failed rebuild cannot retain formal score', current['formalScore'] is None)
        check('all fixture inputs preserved', marker.read_bytes() == b'INPUT MUST SURVIVE')
    finally:
        for link in reversed(links):
            os.rmdir(link)

record = {'runId': os.environ.get('COBOL_RUN_ID', 'local-cobol'),
          'recordedAt': datetime.datetime.now(datetime.timezone.utc).isoformat(),
          'status': 'PASS', 'passed': len(checks), 'checks': checks,
          'sourceHashes': {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
                           for name in ('tools/output_paths.py', 'build.py', 'tests/output-path-regression.py')},
          'scope': 'Disposable fixtures only; junction and hardlink rejection, fixed outputs, stale PASS invalidation.',
          'formalScore': None}
write_json(ROOT / 'build/test-results/path-regression.json', record)
print(json.dumps({'status': record['status'], 'checks': len(checks)}))

"""Seal tested generic label guidance for future jobs, without altering active jobs."""
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys

report = Path(__file__).resolve().parents[1]
agent = report.parents[1]
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
load = lambda p: json.loads(p.read_text(encoding='utf-8-sig'))
write = lambda p, value: p.write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
log = report/'engine/all-ai-r14-tests.log'
match = re.search(r'Ran (\d+) tests in ([0-9.]+)s\s+OK', log.read_text(encoding='utf-8-sig'))
if not match or int(match[1]) != 339:
    raise ValueError('Full passing 339-test receipt required')
previous = load(report/'source-pilot/runtime-code-source-07.json')
source = agent/'src'
files = {p.relative_to(source).as_posix(): sha(p) for p in source.rglob('*')
         if p.is_file() and '__pycache__' not in p.parts and p.suffix != '.pyc'}
if len(files) != 124 or set(files) != set(previous['files']):
    raise ValueError('Full trusted 124-file source inventory required')
old = load(report/'engine/all-ai-r13-result.json')
if {name for name in files if files[name] != old['files'][name]} != {'contextbase/ai/rendering.py', 'contextbase/tests/test_ai_rendering.py'}:
    raise ValueError('Only trusted rendering and its regressions may differ from tested r13')
receipts = []
for mode, version, receipt_name, schema in (
    ('source-only', 'source-08', 'source-pilot/runtime-code-source-08.json', 'source-pilot-frozen-runtime/1'),
    ('training-assisted', 'assisted-06', 'training-assisted/runtime-code-assisted-06.json', 'training-assisted-frozen-runtime/1'),
):
    destination = agent/'.tmp/20261013-rerun-12h'/mode/'runtime-code'/version/'src'
    if destination.exists() or (report/receipt_name).exists():
        raise ValueError('Fresh immutable runtime required')
    destination.mkdir(parents=True)
    for relative, digest in files.items():
        original, target = source/relative, destination/relative
        if original.is_symlink():
            raise ValueError('No linked trusted code')
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(original, target)
        if sha(original) != digest or sha(target) != digest:
            raise ValueError('Frozen code byte-copy drift')
    environment = dict(os.environ)
    environment['PYTHONPATH'] = os.pathsep.join(map(str, (destination,
        agent/'.tmp/20261013-rerun-12h/engine-runtime-deps', agent/'.tmp/session-python-deps')))
    code = 'import importlib,json;names='+repr(list(previous['imports']))+';print(json.dumps({n:importlib.import_module(n).__file__ for n in names}))'
    result = subprocess.run([sys.executable, '-X', 'utf8', '-c', code], cwd=destination, env=environment,
        capture_output=True, text=True, encoding='utf-8', check=True, timeout=60,
        creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0)
    imports = json.loads(result.stdout)
    if any(not Path(path).resolve().is_relative_to(destination.resolve()) for path in imports.values()):
        raise ValueError('Import escaped frozen runtime')
    if files != {p.relative_to(source).as_posix(): sha(p) for p in source.rglob('*')
                 if p.is_file() and '__pycache__' not in p.parts and p.suffix != '.pyc'}:
        raise ValueError('Source changed during freeze')
    write(report/receipt_name, {'schema': schema, 'createdAt': datetime.now(timezone.utc).isoformat(),
        'source': str(source), 'destination': str(destination), 'fileCount': len(files), 'files': files,
        'sourceUnchangedDuringFreeze': True, 'byteIdenticalCopy': True, 'imports': imports,
        'pythonExecutable': sys.executable, 'verification': 'engine/all-ai-r14-result.json',
        'scope': 'full trusted agent source excluding bytecode; not application source'})
    receipts.append(receipt_name)
result = {'schema': 'reverse-ai-engine-verification/1', 'revision': 'r14', 'status': 'PASS',
    'createdAt': datetime.now(timezone.utc).isoformat(), 'testsPassed': int(match[1]), 'seconds': float(match[2]),
    'scope': 'full AI regression suite; trusted 320px label wrapping with intact identifiers, numbers and secured width configuration',
    'log': log.relative_to(report).as_posix(), 'logSha256': sha(log), 'files': files,
    'frozenRuntimeReceipts': receipts, 'activeJobRuntimesChanged': False,
    'businessExpectedAnswersIncluded': False, 'originalApplicationExecuted': False,
    'modelWeightTrainingPerformed': False, 'specificationQualityVerified': False}
write(report/'engine/all-ai-r14-result.json', result)
path = report/'run-manifest.json'
old_bytes = path.read_bytes()
(report/'checkpoints/run-manifest-before-r14.json').write_bytes(old_bytes)
manifest = json.loads(old_bytes)
manifest['engineeringValidation']['previousFullSuiteReport'] = manifest['engineeringValidation']['report']
manifest['engineeringValidation'].update(report='engine/all-ai-r14-result.json', passedTests=339)
manifest['updatedAt'] = result['createdAt']
write(path, manifest)
print(json.dumps({'testsPassed': 339, 'filesPerRuntime': 124, 'importsPerRuntime': len(imports), 'receipts': receipts}))

"""Seal verified engine code for future clean author jobs; leave active jobs intact."""
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
write = lambda p, obj: p.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
log = report / 'engine/all-ai-r11-tests.log'
match = re.search(r'Ran (\d+) tests in ([0-9.]+)s\s+OK', log.read_text(encoding='utf-8-sig'))
if not match or int(match[1]) != 335:
    raise ValueError('Complete passing 335-test receipt required')
previous = load(report / 'source-pilot/runtime-code-source-05.json')
names = set(previous['files'])
source = agent / 'src'
current = {p.relative_to(source).as_posix() for p in source.rglob('*')
           if p.is_file() and '__pycache__' not in p.parts and p.suffix != '.pyc'}
if names != current or len(names) != 124:
    raise ValueError('Frozen inventory must match the full trusted 124-file source tree')
before = {name: sha(source / name) for name in sorted(names)}
modules = list(previous['imports'])
receipts = []
for mode, name, receipt_name, schema in (
    ('source-only', 'source-06', 'source-pilot/runtime-code-source-06.json', 'source-pilot-frozen-runtime/1'),
    ('training-assisted', 'assisted-04', 'training-assisted/runtime-code-assisted-04.json', 'training-assisted-frozen-runtime/1'),
):
    destination = agent / '.tmp/20261013-rerun-12h' / mode / 'runtime-code' / name / 'src'
    if destination.exists() or (report / receipt_name).exists():
        raise ValueError('Fresh immutable runtime paths required')
    destination.mkdir(parents=True)
    for relative in sorted(names):
        original = source / relative
        if original.is_symlink():
            raise ValueError('Trusted code must not be linked')
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(original, target)
        if sha(target) != before[relative]:
            raise ValueError('Frozen runtime byte copy mismatch')
    environment = dict(os.environ)
    environment['PYTHONPATH'] = os.pathsep.join(map(str, (
        destination, agent / '.tmp/20261013-rerun-12h/engine-runtime-deps',
        agent / '.tmp/session-python-deps')))
    code = 'import importlib,json; names=' + repr(modules) + '; print(json.dumps({n:importlib.import_module(n).__file__ for n in names}))'
    result = subprocess.run([sys.executable, '-X', 'utf8', '-c', code], cwd=destination,
                            env=environment, capture_output=True, text=True, encoding='utf-8',
                            check=True, timeout=60,
                            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0)
    imports = json.loads(result.stdout)
    if any(not Path(path).resolve().is_relative_to(destination.resolve()) for path in imports.values()):
        raise ValueError('Import escaped the frozen runtime')
    if before != {relative: sha(source / relative) for relative in sorted(names)}:
        raise ValueError('Trusted source changed during freezing')
    receipt = {'schema': schema, 'createdAt': datetime.now(timezone.utc).isoformat(),
        'source': str(source), 'destination': str(destination), 'fileCount': len(names), 'files': before,
        'sourceUnchangedDuringFreeze': True, 'byteIdenticalCopy': True, 'imports': imports,
        'pythonExecutable': sys.executable, 'verification': 'engine/all-ai-r11-result.json',
        'scope': 'full agents/reverse-agent/src excluding bytecode caches; application source is not copied here'}
    write(report / receipt_name, receipt)
    receipts.append(receipt_name)
result = {'schema': 'reverse-ai-engine-verification/1', 'revision': 'r11', 'status': 'PASS',
    'createdAt': datetime.now(timezone.utc).isoformat(), 'testsPassed': int(match[1]), 'seconds': float(match[2]),
    'scope': 'complete test_ai regression suite including synthetic static browser rendering',
    'command': "python -X utf8 -m unittest discover -s src/contextbase/tests -p 'test_ai*.py' -v",
    'changes': ['Trace invalid values through rejection redisplay and secondary view exceptions',
                'Review documentLocation distinct from sealed raw/reference material citations'],
    'log': log.relative_to(report).as_posix(), 'logSha256': sha(log),
    'files': before, 'frozenRuntimeReceipts': receipts,
    'businessExpectedAnswersIncluded': False, 'originalApplicationExecuted': False,
    'modelWeightTrainingPerformed': False, 'specificationQualityVerified': False}
write(report / 'engine/all-ai-r11-result.json', result)
path = report / 'run-manifest.json'
old = path.read_bytes()
(report / 'checkpoints/run-manifest-before-r11.json').write_bytes(old)
manifest = json.loads(old)
manifest['engineeringValidation']['previousFullSuiteReport'] = manifest['engineeringValidation']['report']
manifest['engineeringValidation']['report'] = 'engine/all-ai-r11-result.json'
manifest['engineeringValidation']['passedTests'] = int(match[1])
manifest['updatedAt'] = result['createdAt']
write(path, manifest)
print(json.dumps({'testsPassed': int(match[1]), 'frozenFileCount': len(names),
                  'importsVerifiedPerRuntime': len(modules), 'receipts': receipts}))

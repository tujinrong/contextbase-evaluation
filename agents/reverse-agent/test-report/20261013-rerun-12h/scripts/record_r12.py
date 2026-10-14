"""Record tested trusted-renderer change without changing active author runtimes."""
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import re

report = Path(__file__).resolve().parents[1]
agent = report.parents[1]
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
load = lambda p: json.loads(p.read_text(encoding='utf-8-sig'))
write = lambda p, v: p.write_text(json.dumps(v, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
log = report/'engine/all-ai-r12-tests.log'
match = re.search(r'Ran (\d+) tests in ([0-9.]+)s\s+OK', log.read_text(encoding='utf-8-sig'))
if not match or int(match[1]) != 337:
    raise ValueError('Full passing 337-test receipt required')
old = load(report/'engine/all-ai-r11-result.json')
files = {p.relative_to(agent/'src').as_posix(): sha(p) for p in (agent/'src').rglob('*')
         if p.is_file() and '__pycache__' not in p.parts and p.suffix != '.pyc'}
if set(files) != set(old['files']):
    raise ValueError('Trusted source inventory changed')
changed = {name for name in files if files[name] != old['files'][name]}
if changed != {'contextbase/ai/rendering.py', 'contextbase/tests/test_ai_rendering.py'}:
    raise ValueError('Unexpected non-renderer changes')
for name in ('source-pilot/runtime-code-source-06.json', 'training-assisted/runtime-code-assisted-04.json'):
    receipt = load(report/name)
    root = Path(receipt['destination'])
    actual = {p.relative_to(root).as_posix(): sha(p) for p in root.rglob('*')
              if p.is_file() and '__pycache__' not in p.parts and p.suffix != '.pyc'}
    if receipt['files'] != actual:
        raise ValueError('Existing author runtime changed')
result = {'schema': 'reverse-ai-engine-verification/1', 'revision': 'r12', 'status': 'PASS',
    'createdAt': datetime.now(timezone.utc).isoformat(), 'testsPassed': int(match[1]),
    'seconds': float(match[2]), 'log': log.relative_to(report).as_posix(), 'logSha256': sha(log),
    'scope': 'complete test_ai suite; trusted opaque edge labels preserve geometry and resist author directives',
    'command': "python -X utf8 -m unittest discover -s src/contextbase/tests -p 'test_ai*.py' -v",
    'files': files, 'changedFiles': sorted(changed), 'authorFrozenRuntimeChanged': False,
    'geometryPreservationVerifiedOnSyntheticDiagram': True,
    'prototypeReport': 'delivery/mermaid-layout-probe-r01/layout-review-final.json',
    'prototypeReportSha256': sha(report/'delivery/mermaid-layout-probe-r01/layout-review-final.json'),
    'businessExpectedAnswersIncluded': False, 'originalApplicationExecuted': False,
    'modelWeightTrainingPerformed': False, 'specificationQualityVerified': False}
write(report/'engine/all-ai-r12-result.json', result)
path = report/'run-manifest.json'
old_bytes = path.read_bytes()
(report/'checkpoints/run-manifest-before-r12.json').write_bytes(old_bytes)
manifest = json.loads(old_bytes)
manifest['engineeringValidation']['previousFullSuiteReport'] = manifest['engineeringValidation']['report']
manifest['engineeringValidation'].update(report='engine/all-ai-r12-result.json', passedTests=337)
manifest['updatedAt'] = result['createdAt']
write(path, manifest)
print(json.dumps({'testsPassed': 337, 'authorRuntimesUnchanged': True, 'rendererSha256': files['contextbase/ai/rendering.py']}))

"""Record trusted renderer regression evidence without assigning document quality."""
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import re

report = Path(__file__).resolve().parents[1]
agent = report.parents[1]
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
log = report / 'engine/all-ai-r10-tests.log'
match = re.search(r'Ran (\d+) tests in ([0-9.]+)s\s+OK', log.read_text(encoding='utf-8-sig'))
if not match or int(match[1]) != 335:
    raise ValueError('Complete passing 335-test receipt required')
result = {
    'schema': 'reverse-ai-engine-verification/1', 'revision': 'r10', 'status': 'PASS',
    'createdAt': datetime.now(timezone.utc).isoformat(),
    'scope': 'complete test_ai regression suite including synthetic static browser rendering',
    'changes': ['Markdown-only table markers and column widths, unchanged cell values',
                'CSS image-set direct string URL validation and local asset embedding'],
    'command': "python -X utf8 -m unittest discover -s src/contextbase/tests -p 'test_ai*.py' -v",
    'testsPassed': int(match[1]), 'seconds': float(match[2]),
    'log': log.relative_to(report).as_posix(), 'logSha256': sha(log),
    'files': {name: sha(agent / name) for name in (
        'src/contextbase/ai/prompts.py', 'src/contextbase/ai/validation.py',
        'src/contextbase/ai/rendering.py', 'src/contextbase/tests/test_ai_rendering.py')},
    'authorFrozenRuntimeChanged': False, 'businessExpectedAnswersIncluded': False,
    'originalApplicationExecuted': False, 'modelWeightTrainingPerformed': False,
    'specificationQualityVerified': False,
}
with (report / 'engine/all-ai-r10-result.json').open('x', encoding='utf-8', newline='\n') as stream:
    json.dump(result, stream, ensure_ascii=False, indent=2)
    stream.write('\n')
manifest_path = report / 'run-manifest.json'
old_bytes = manifest_path.read_bytes()
(report / 'checkpoints/run-manifest-before-r10.json').write_bytes(old_bytes)
manifest = json.loads(old_bytes)
manifest['engineeringValidation']['previousFullSuiteReport'] = manifest['engineeringValidation']['report']
manifest['engineeringValidation']['report'] = 'engine/all-ai-r10-result.json'
manifest['engineeringValidation']['passedTests'] = result['testsPassed']
manifest['updatedAt'] = result['createdAt']
manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'testsPassed': result['testsPassed'], 'specificationQualityVerified': False}))

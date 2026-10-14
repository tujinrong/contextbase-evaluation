"""Seal the complete trusted AI-engine regression suite, separate from quality scoring."""
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import re

report = Path(__file__).resolve().parents[1]
agent = report.parents[1]
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
log = report / 'engine/all-ai-r9-tests.log'
match = re.search(r'Ran (\d+) tests in ([0-9.]+)s\s+OK', log.read_text(encoding='utf-8-sig'))
if not match or int(match[1]) != 331:
    raise ValueError('Complete passing regression receipt required')
result = {
    'schema': 'reverse-ai-engine-verification/1', 'revision': 'r9', 'status': 'PASS',
    'createdAt': datetime.now(timezone.utc).isoformat(),
    'scope': 'complete test_ai regression suite including synthetic static browser rendering',
    'command': "python -X utf8 -m unittest discover -s src/contextbase/tests -p 'test_ai*.py' -v",
    'testsPassed': int(match[1]), 'seconds': float(match[2]),
    'log': log.relative_to(report).as_posix(), 'logSha256': sha(log),
    'formatReceipt': 'engine/static-format-r9-result.json',
    'sourceFrozenRuntime': 'source-pilot/runtime-code-source-05.json',
    'assistedFrozenRuntime': 'training-assisted/runtime-code-assisted-03.json',
    'files': {name: sha(agent / name) for name in (
        'src/contextbase/ai/prompts.py', 'src/contextbase/ai/validation.py',
        'src/contextbase/tests/test_ai_validation.py')},
    'businessExpectedAnswersIncluded': False, 'originalApplicationExecuted': False,
    'modelWeightTrainingPerformed': False, 'specificationQualityVerified': False,
}
with (report / 'engine/all-ai-r9-result.json').open('x', encoding='utf-8', newline='\n') as stream:
    json.dump(result, stream, ensure_ascii=False, indent=2)
    stream.write('\n')
manifest_path = report / 'run-manifest.json'
manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
manifest['engineeringValidation']['previousFullSuiteReport'] = manifest['engineeringValidation']['report']
manifest['engineeringValidation']['report'] = 'engine/all-ai-r9-result.json'
manifest['engineeringValidation']['passedTests'] = result['testsPassed']
manifest['updatedAt'] = result['createdAt']
manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'testsPassed': result['testsPassed'], 'specificationQualityVerified': False}))

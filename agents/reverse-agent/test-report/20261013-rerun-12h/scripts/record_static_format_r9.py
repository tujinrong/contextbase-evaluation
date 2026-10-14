"""Record verified engine metadata only; never author or repair specification text."""
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import re

report = Path(__file__).resolve().parents[1]
agent = report.parents[1]
log = report / 'engine/static-format-r9-tests.log'
text = log.read_text(encoding='utf-8-sig')
match = re.search(r'Ran (\d+) tests in ([0-9.]+)s\s+OK', text)
if not match or int(match[1]) != 131:
    raise ValueError('The required completed passing test log is absent')
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
result = {
    'schema': 'reverse-agent-format-validation/1', 'revision': 'r9',
    'recordedAt': datetime.now(timezone.utc).isoformat(),
    'testsPassed': int(match[1]), 'testSeconds': float(match[2]), 'status': 'PASS',
    'testModules': ['contextbase.tests.test_ai_validation', 'contextbase.tests.test_ai_document_contract',
                    'contextbase.tests.test_ai_rendering'],
    'log': log.relative_to(report).as_posix(), 'logSha256': sha(log),
    'files': {name: sha(agent / name) for name in [
        'src/contextbase/ai/validation.py', 'src/contextbase/ai/prompts.py',
        'src/contextbase/tests/test_ai_validation.py']},
    'change': 'HTML boolean attribute conformance; generic numbered subflow readability guidance',
    'businessExpectedAnswersIncluded': False, 'specificationQualityVerified': False,
    'originalApplicationExecuted': False,
    'priorAttempts': [{'status': 'FAILED_MISSING_TEST_ENVIRONMENT',
                       'log': 'engine/static-format-r9-missing-render-env.log'}],
}
with (report / 'engine/static-format-r9-result.json').open('x', encoding='utf-8', newline='\n') as stream:
    json.dump(result, stream, ensure_ascii=False, indent=2)
    stream.write('\n')
print(json.dumps(result, ensure_ascii=False))

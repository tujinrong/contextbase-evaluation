"""Append design watchpoints to a fresh audit receipt; no executable authoring."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json

REPORT = Path(r'D:/開発/contextbase-evaluation/agents/spec-agent/report/20261014-nenkin-high-01')
BASE = REPORT / 'independent-audit/durable-conversion-independent-design-review-r01.json'
BASE_SHA = '3ab9072ab9036f19ae00b80fb8b74d86b4e1cacc0963f7a7c28c7b60b0af0720'
OUT = REPORT / 'independent-audit/durable-conversion-independent-design-review-r02.json'
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
assert not OUT.exists() and sha(BASE) == BASE_SHA
value = json.loads(BASE.read_text(encoding='utf-8'))
assert value['status'] == 'APPROVED_DESIGN_SCOPE_ONLY_NOT_EXECUTION_OR_QUALIFICATION'
value['createdAt'] = datetime.now(timezone.utc).isoformat()
value['priorAudit'] = {'path': str(BASE), 'sha256': BASE_SHA, 'preserved': True}
value['implementationRequirementsStillOpen'].extend([
    'Workspace identity must independently match installed-package placement or a root-approved immutable workspace identity; a self-declared config workspace does not establish ownership.',
    'runId must be validated as one canonical folder segment before deriving workspace/run roots; structural string length is insufficient.',
    'Inherit the outer run deadline from the accepted current execution context/bridge and enforce stage timeout <= total timeout <= actual remaining budget; structural timeout ranges do not establish those relationships.'
])
assert all(sha(Path(pin['path'])) == pin['sha256'] for pin in value['metadataPins'])
assert sha(BASE) == BASE_SHA
with OUT.open('x', encoding='utf-8', newline='\n') as stream:
    json.dump(value, stream, ensure_ascii=False, indent=2)
    stream.write('\n')
print(json.dumps({'report': str(OUT), 'sha256': sha(OUT), 'status': value['status'],
                  'providerStarts': 0, 'priorAuditPreserved': True}, ensure_ascii=False))

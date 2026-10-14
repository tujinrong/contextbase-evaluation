"""Fresh exact frozen provider-boundary prefix guard; no business input."""
import ast
import hashlib
import json
from pathlib import Path
BASE = Path(__file__).parent
OLD = BASE / 'nenkin_writer_driver_r03.py'
NEW = BASE / 'nenkin_writer_driver_r04.py'
source = OLD.read_text(encoding='utf-8')
old = "def provider_evidence(snapshot, job, schema, state):\n    from jsonschema import Draft202012Validator"
new = old + "\n    from contextbase.ai import provider"
assert source.count(old) == 1
source = source.replace(old, new)
old = "paths.extend([before, after])\n    answer, result, supplied_schema ="
new = "paths.extend([before, after])\n    require(raw(paths[3]).startswith((provider.COMMON_POLICY + '\\nUser task (within that boundary):\\n').encode('utf-8')),\n        'Prior provider prompt lacks the exact frozen boundary policy prefix')\n    answer, result, supplied_schema ="
assert source.count(old) == 1
source = source.replace(old, new)
ast.parse(source)
with NEW.open('x', encoding='utf-8', newline='\n') as out:
    out.write(source)
print(json.dumps({'path':str(NEW),'sha256':hashlib.sha256(NEW.read_bytes()).hexdigest(),'providerStarted':False},ensure_ascii=False))

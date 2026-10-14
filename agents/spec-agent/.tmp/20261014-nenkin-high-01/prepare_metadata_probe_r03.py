from pathlib import Path
import ast, hashlib
ROOT = Path(r'D:/開発/contextbase-evaluation/agents/spec-agent/report/20261014-nenkin-high-01/independent-audit')
old = ROOT / 'probe_writer_metadata_r05_r02.py'
source = old.read_text(encoding='utf-8')
source = source.replace("writer-metadata-r05-toy-r02'", "writer-metadata-r05-toy-r03'", 1)
source = source.replace("writer-metadata-r05-bounded-probes-r02.json'", "writer-metadata-r05-bounded-probes-r03.json'", 1)
source = source.replace("    f['supplement']['records'][0]['sha256']", "    f['supplement']['records'][0]['path'] = str(f['routePath'])\n    f['supplement']['records'][1]['path'] = str(f['completionPath'])\n    f['supplement']['records'][0]['sha256']", 1)
source = source.replace("    results.append({'name': name, 'expected': expected, 'actual': result, 'passed': result == expected, 'detail': detail})",
    "    meaningful_reject = detail is None or detail['type'] in {'ValueError', 'ValidationError'}\n    results.append({'name': name, 'expected': expected, 'actual': result, 'passed': result == expected and meaningful_reject, 'detail': detail})", 1)
source = source.replace("'priorProbeInvalidated':'r01 was an invalid -I dependency environment; all negative results there were import failures, not behavioral validation',",
    "'priorProbeInvalidated':'r01 was an invalid -I dependency environment; r02 outside-record case referred to the old nonexistent path and rejected with FileNotFoundError. r03 uses the mutated record path and only counts typed boundary/schema rejection errors as meaningful negatives.',", 1)
ast.parse(source)
new = ROOT / 'probe_writer_metadata_r05_r03.py'
with new.open('x', encoding='utf-8', newline='\n') as f:
    f.write(source)
print(hashlib.sha256(new.read_bytes()).hexdigest())

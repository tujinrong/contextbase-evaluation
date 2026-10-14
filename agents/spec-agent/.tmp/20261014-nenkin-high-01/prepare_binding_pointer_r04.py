"""Exact producer-pointer update; no business data or runtime imports."""
from pathlib import Path
from datetime import datetime, timezone
import ast, hashlib, json
RUN = Path(r'D:/開発/contextbase-evaluation/agents/spec-agent/.tmp/20261014-nenkin-high-01')
REPORT = Path(r'D:/開発/contextbase-evaluation/agents/spec-agent/report/20261014-nenkin-high-01')
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
old = RUN / 'delivery/build_delivery_binding_r03.py'
assert sha(old) == 'fe7af7ea233186fa3a1a6becc382b003c0d9b64ea6410cf061a0a15b5bbef27a'
text = old.read_text(encoding='utf-8')
changes = {
    "COLLECTOR=WORK/'collect_reviewed_r07.py'": "COLLECTOR=WORK/'collect_reviewed_r08.py'",
    "COLLECTOR_SHA='ee8419432a9b553c04ba757a2b188c86614ae230d980c5822ac8d8fe17a40a50'": "COLLECTOR_SHA='2848e50ff84671608dfada5dece254ec15e80afe0ae55df5de41cf22abf345e3'",
    "RENDERER=WORK/'render_reviewed_r04.py'": "RENDERER=WORK/'render_reviewed_r05.py'",
    "RENDERER_SHA='888db1128cc0f5dc0ab942e18fb4476e4f0ce79cf1aa2d1e3bd75324952571be'": "RENDERER_SHA='b3e69f6c2cbce03d8e1e2a833f14b31d7acb85c2ee9aae60fa25a1ae2c4641fe'"
}
for before, after in changes.items():
    assert text.count(before) == 1
    text = text.replace(before, after)
names = {'COLLECTOR', 'COLLECTOR_SHA', 'RENDERER', 'RENDERER_SHA'}
def remaining(program):
    tree = ast.parse(program)
    return [ast.dump(node, include_attributes=False) for node in tree.body
            if not (isinstance(node, ast.Assign) and len(node.targets) == 1 and
                    isinstance(node.targets[0], ast.Name) and node.targets[0].id in names)]
assert remaining(old.read_text(encoding='utf-8')) == remaining(text)
for name, expected in [('collect_reviewed_r08.py','2848e50ff84671608dfada5dece254ec15e80afe0ae55df5de41cf22abf345e3'),
                       ('render_reviewed_r05.py','b3e69f6c2cbce03d8e1e2a833f14b31d7acb85c2ee9aae60fa25a1ae2c4641fe')]:
    assert sha(RUN / name) == expected
new = RUN / 'delivery/build_delivery_binding_r04.py'
with new.open('xb') as stream: stream.write(text.encode('utf-8'))
assert sha(old) == 'fe7af7ea233186fa3a1a6becc382b003c0d9b64ea6410cf061a0a15b5bbef27a'
record = {'schema':'spec-agent-root-producer-pointer-audit/1', 'createdUtc':datetime.now(timezone.utc).isoformat(),
          'status':'APPROVED_POINTER_DELTA_CODE_ONLY', 'helper':str(new), 'helperSha256':sha(new),
          'comparedHelper':str(old), 'comparedHelperSha256':sha(old), 'changedConstants':sorted(names),
          'allOtherAstNodesAndFunctionsIdentical':True, 'actualImports':0, 'actualBusinessReads':0,
          'actualBinding':0, 'actualMarkers':0, 'actualConversion':0, 'published':False,
          'inheritance':'r03 independently reviewed exact frozen source13 runtime identity, current full128 freshness remains required'}
target = REPORT / 'independent-audit/binding-producer-pointer-review-r04.json'
with target.open('xb') as stream: stream.write((json.dumps(record,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
print(json.dumps({'helper':str(new),'helperSha256':sha(new),'audit':str(target),'auditSha256':sha(target)},ensure_ascii=False))

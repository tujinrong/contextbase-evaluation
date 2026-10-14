"""Keep the failed first suite immutable; repair two proven technical gaps."""
from pathlib import Path
from datetime import datetime, timezone
import ast
import hashlib
import json

report=Path(__file__).resolve().parents[1]
agent=report.parents[1]
source=agent/'src'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def inventory():
    return {p.relative_to(source).as_posix():sha(p) for p in source.rglob('*')
            if p.is_file() and '__pycache__' not in p.parts and p.suffix not in {'.pyc','.pyo'}}
before=inventory()
renderer=source/'contextbase/ai/rendering.py'
text=renderer.read_text(encoding='utf-8-sig')
oldjs=(report/'delivery/measure_node_rows_r05.js').read_text(encoding='utf-8-sig')
newpath=report/'delivery/measure_node_rows_r06.js'
assert sha(newpath)=='9e83c258eca0b0f0a3f0cba3007e8c64945e920286db9ec39bdcf2563689967e'
newjs=newpath.read_text(encoding='utf-8-sig')
assert text.count(repr(oldjs))==1
text=text.replace(repr(oldjs),repr(newjs))
old='''                                if rendered["securityLevel"] != "strict":
                                    raise ValueError("Mermaid security level changed")
                                canonical_nodes = rendered["vertices"]'''
new='''                                if rendered["securityLevel"] != "strict":
                                    raise ValueError("Mermaid security level changed")
                                record["securityLevel"] = rendered["securityLevel"]
                                canonical_nodes = rendered["vertices"]'''
assert text.count(old)==1
text=text.replace(old,new)
ast.parse(text)
renderer.write_text(text,encoding='utf-8')
test_path=source/'contextbase/tests/test_ai_rendering.py'
tests=test_path.read_text(encoding='utf-8-sig')
old='''        self.assertEqual("strict", result["diagrams"][0].get("securityLevel"), result["diagrams"])
        self.assertEqual("PASS", result["diagrams"][0]["status"])
        self.assertEqual([], result["display"]["blockedRequests"])
        svg = ET.fromstring((self.run_root / "directive/diagram-001.svg").read_text(encoding="utf-8"))
        self.assertFalse(any(key.lower().startswith("on") for element in svg.iter() for key in element.attrib))'''
new='''        self.assertEqual("strict", result["diagrams"][0].get("securityLevel"), result["diagrams"])
        self.assertEqual("ERROR", result["diagrams"][0]["status"])
        self.assertEqual([], result["display"]["blockedRequests"])
        receipt = json.loads((self.run_root / "directive/diagram-001.projection.json").read_text(encoding="utf-8"))
        self.assertTrue(receipt['authorRevisionRequired'])
        self.assertIn('Unsupported node-label markup', receipt['error'])
        self.assertFalse((self.run_root / "directive/diagram-001.png").exists())
        svg = ET.fromstring((self.run_root / "directive/diagram-001.source.svg").read_text(encoding="utf-8"))
        self.assertFalse(any(key.lower().startswith("on") for element in svg.iter() for key in element.attrib))
        self.assertEqual(raw.encode('utf-8'), source.read_bytes())'''
assert tests.count(old)==1
tests=tests.replace(old,new)
ast.parse(tests)
test_path.write_text(tests,encoding='utf-8')
after=inventory()
assert set(before)==set(after)
assert {p for p in before if before[p]!=after[p]}=={'contextbase/ai/rendering.py','contextbase/tests/test_ai_rendering.py'}
receipt=report/'engine/r19-effective-fill-repair-receipt-r02.json'
assert not receipt.exists()
receipt.write_text(json.dumps({'schema':'node-row-measurement-proven-gap-repair/1',
    'createdAt':datetime.now(timezone.utc).isoformat(),'before':before,'after':after,
    'measurementJavaScriptSha256':sha(newpath),
    'originalFailedSuite':'engine/all-ai-r19-root-r01.log',
    'originalFailedSuiteSha256':sha(report/'engine/all-ai-r19-root-r01.log'),
    'evidence':['delivery/node-effective-fill-probe-r05-gap.json','delivery/node-effective-fill-probe-r06.json'],
    'changes':['Reject actual fully transparent text paint in the visible-row measurement.',
               'Retain the already verified strict security level even if a later literal/visibility gate rejects publication.',
               'The hostile unknown-markup test now requires strict rejection, safe source SVG, unchanged canonical bytes, and no final PNG.'],
    'businessSourceOrExpectedAnswersChanged':False,'activeFrozenRuntimesChanged':False,
    'nativeOrFormalApproval':False},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'receiptSha256':sha(receipt),'modified':['rendering.py','test_ai_rendering.py']}))

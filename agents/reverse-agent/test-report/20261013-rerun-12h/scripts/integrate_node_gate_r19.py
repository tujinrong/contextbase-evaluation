"""Integrate only independently probed generic node rendering and row proof code."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json

report = Path(__file__).resolve().parents[1]
agent = report.parents[1]
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
load = lambda p: json.loads(p.read_text(encoding='utf-8-sig'))
previous = load(report/'training-assisted/runtime-code-assisted-10.json')['files']
source = agent/'src'
def inventory():
    return {p.relative_to(source).as_posix():sha(p) for p in source.rglob('*')
            if p.is_file() and '__pycache__' not in p.parts and p.suffix not in {'.pyc','.pyo'}}
before = inventory()
assert before == previous
candidate = report/'delivery/node_label_row_gate_r05.py'
measure = report/'delivery/measure_node_rows_r05.js'
tests = report/'delivery/test_node_label_row_gate_r06.py'
assert sha(candidate)=='5f9d192749643ba16bc5334eccff175616277befdd28c373ae8524f998f51b68'
assert sha(measure)=='06a3257707b1162cc0432ba38afe2aecfa37f8667a16a8233bb0ba9fb183a64e'
module_path = source/'contextbase/ai/node_label_row_gate.py'
test_path = source/'contextbase/tests/test_ai_node_label_rows.py'
assert not module_path.exists() and not test_path.exists()
renderer = source/'contextbase/ai/rendering.py'
text = renderer.read_text(encoding='utf-8-sig')
def replace_once(old, new):
    global text
    assert text.count(old)==1, old[:120]
    text = text.replace(old,new)
replace_once('    validate_semantic_signature, validate_svg_label_rows)\n',
    '    validate_semantic_signature, validate_svg_label_rows)\nfrom .node_label_row_gate import prove_node_rows, bind_svg_node_ids\n')
replace_once('MERMAID_LABEL_WIDTH = 320', 'MERMAID_LABEL_WIDTH = 400')
measure_js = measure.read_text(encoding='utf-8-sig')
replace_once('def _capture_document(page, destination, display):',
    'def _node_label_rows(page):\n    """Measure captured SVG node rows in the inert static browser context."""\n'
    '    return page.locator(\'svg\').evaluate('+repr(measure_js)+')\n\n\n'
    'def _capture_document(page, destination, display):')
old = '''                                rendered = page.evaluate("""async ({id,text,config}) => {
                                    mermaid.initialize(config);
                                    const {svg}=await mermaid.render(id,text);
                                    return {svg,securityLevel:mermaid.mermaidAPI.getConfig().securityLevel};
                                }""", {"id": diagram["id"], "text": diagram["source"], "config": config})'''
new = '''                                rendered = page.evaluate("""async ({id,text,config,flowchart}) => {
                                    mermaid.initialize(config);
                                    const {svg}=await mermaid.render(id,text);
                                    let vertices=[];
                                    if (flowchart) {
                                        const parsed=await mermaid.mermaidAPI.getDiagramFromText(text);
                                        vertices=[...parsed.db.getVertices().values()].map(vertex => ({
                                            id:vertex.id,domId:vertex.domId,text:vertex.text,
                                            labelType:vertex.labelType,icon:vertex.icon,img:vertex.img}));
                                    }
                                    return {svg,vertices,securityLevel:mermaid.mermaidAPI.getConfig().securityLevel};
                                }""", {"id": diagram["id"], "text": diagram["source"], "config": config,
                                    "flowchart": projection.supportedDiagram})'''
replace_once(old,new)
replace_once('                                original_svg = _svg_safe(rendered["svg"])',
    '                                canonical_nodes = rendered["vertices"]\n'
    '                                projection_receipt.update(canonicalNodeLiterals=canonical_nodes,\n'
    '                                    canonicalNodeLiteralsSha256=_sha(json.dumps(canonical_nodes, sort_keys=True, ensure_ascii=False)),\n'
    '                                    nodeLabelWrappingWidth=MERMAID_LABEL_WIDTH,\n'
    '                                    wholeVisibleNodeTokensVerified=False)\n'
    '                                original_svg = _svg_safe(rendered["svg"])')
replace_once('                                    checks = validate_svg_label_rows(diagram["source"], projection, _edge_label_rows(capture))',
    '                                    if projection.supportedDiagram:\n'
    '                                        measurement = _node_label_rows(capture)\n'
    '                                        bound_nodes = bind_svg_node_ids(canonical_nodes, measurement["nodes"], diagram["id"])\n'
    '                                        node_proof = prove_node_rows(bound_nodes, measurement["nodes"], measurement["canvas"])\n'
    '                                        projection_receipt.update(nodeRowMeasurement=measurement, nodeLabelProof=node_proof,\n'
    '                                            wholeVisibleNodeTokensVerified=True, nodeParserApi="mermaidAPI.getDiagramFromText/FlowDB.getVertices")\n'
    '                                    checks = validate_svg_label_rows(diagram["source"], projection, _edge_label_rows(capture))')
module_path.write_bytes(candidate.read_bytes())
test_source = tests.read_text(encoding='utf-8-sig')
assert test_source.count('from node_label_row_gate_r05 import')==2
test_path.write_text(test_source.replace('from node_label_row_gate_r05 import','from contextbase.ai.node_label_row_gate import'),encoding='utf-8')
renderer.write_text(text,encoding='utf-8')
after=inventory()
changed={p for p in before if before[p]!=after[p]}
added=set(after)-set(before)
assert changed=={'contextbase/ai/rendering.py'}
assert added=={'contextbase/ai/node_label_row_gate.py','contextbase/tests/test_ai_node_label_rows.py'}
receipt=report/'engine/r19-integration-receipt.json'
assert not receipt.exists()
receipt.write_text(json.dumps({'schema':'generic-node-row-gate-integration/1','createdAt':datetime.now(timezone.utc).isoformat(),
    'previousRuntimeReceiptSha256':sha(report/'training-assisted/runtime-code-assisted-10.json'),
    'candidateModuleSha256':sha(candidate),'measurementJavaScriptSha256':sha(measure),
    'candidateTestsSha256':sha(tests),'before':before,'after':after,
    'modifiedFiles':sorted(changed),'addedFiles':sorted(added),
    'scope':'generic width400 plus literal/visible-node-row proof; no business prose or expected answers',
    'originalProgramsExecuted':False,'activeFrozenRuntimesChanged':False,
    'originalMarkdownChanged':False,'originalMmdChanged':False,'qualified':False},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'modified':sorted(changed),'added':sorted(added),'receiptSha256':sha(receipt)}))

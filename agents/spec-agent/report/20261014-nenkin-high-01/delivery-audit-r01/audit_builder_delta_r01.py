"""Read-only exporter-code delta audit; does not import or run Artifact Tool."""
import hashlib,json
from pathlib import Path
from datetime import datetime,timezone
R=Path(r'D:\開発\contextbase-evaluation')
O=R/'agents/spec-agent/report/20261014-nenkin-high-01/delivery-audit-r01'
P=R/'agents/spec-agent/.tmp/20261014-nenkin-high-01/delivery/build_xlsx_v2_62_r01.mjs'
OLD=R/'agents/reverse-agent/test-report/20261013-rerun-12h/delivery/build_xlsx_r18.mjs'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(P)=='d70a0eb222b68869e93e8bd33f2b4e415e6553698f75d0931f96c3fa24a8e5c8'
data=json.loads((O/'candidate-preparation.json').read_text(encoding='utf-8'))
changes=[c for c in data['mechanicalCodeChanges'] if c['label'].startswith('builder-')]
assert len(changes)==2
text=P.read_text(encoding='utf-8');restored=text
for c in reversed(changes):
    assert restored.count(c['new'])==1
    restored=restored.replace(c['new'],c['old'],1)
assert restored==OLD.read_text(encoding='utf-8')
invariants=['region.clear({applyTo:\'formats\'});','region.setNumberFormat(\'@\');','sheet.getRange(left+top).values=[[literal(operation.value)]];','sheet.freezePanes.freezeRows(tableSpec.headerRow);',"sheet.images.add({dataUrl:'data:image/png;base64,'","outside(region,'medium',black);","bottom:{style:'double'","outside(range,'double'","header.format.borders={top:{style:'medium'","SpreadsheetFile.exportXlsx(workbook)","--authoring-marker-completed"]
assert all(term in text for term in invariants)
record={'schema':'spec-agent-builder-code-delta-audit/1','createdUtc':datetime.now(timezone.utc).isoformat(),'scope':'CODE_ONLY_NO_ARTIFACT_IMPORT','status':'PASS_LIMITED_GEOMETRY_DELTA_ONLY','builder':str(P),'builderSha256':sha(P),'origin':str(OLD),'originSha256':sha(OLD),'exactDeltaCount':2,'deltas':changes,'inverseRecoversOriginalText':True,'codeLineEndingNormalization':'UTF8 read_text normalizes CRLF to LF; no claim of original byte restoration','publicApiAuthorPreserved':True,'literalAndNeutralFormatAndThreeBordersAndImageAndFreezeControlsPreserved':True,'invariants':invariants,'nodeSyntaxCheck':'PASS previously executed without importing dependency','actualXlsxCreated':False,'actualArtifactToolImported':False,'markerExecuted':False,'providerExecuted':False,'productionInputRead':False,'businessContentAuthored':False,'remaining':['Marker flag acknowledges the coordinator; it is not a cryptographic receipt of the actual marker command.','Actual new-run artifact authoring/readback/printing/original-size native QA remain pending.','Owned sheet and column geometry still require model/real-XLSX correspondence.']}
target=O/'builder-code-delta-independent-r01.json'
with target.open('x',encoding='utf-8') as f:json.dump(record,f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps({'path':str(target),'sha256':sha(target),'status':record['status']},ensure_ascii=False))

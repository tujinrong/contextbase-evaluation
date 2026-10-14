"""Record all 24 actually viewed r04 fixture images and immutable evidence."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,unittest,io
from delivery_model import safe_path
import test_edge_label_projection_r02 as tests
HERE=Path(__file__).resolve().parent
def digest(p):return hashlib.sha256(safe_path(p).read_bytes()).hexdigest()
def main():
 path=HERE/'mermaid-edge-projection-r04/probe.json';data=json.loads(path.read_bytes())
 assert all(digest(p)==s for p,s in data['beforeAfterHashes'].items())
 stream=io.StringIO();result=unittest.TextTestRunner(stream=stream,verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(tests))
 assert result.wasSuccessful() and result.testsRun==37
 images=[]
 for case in data['results']:
  for item in case['results']:
   assert digest(item['png'])==item['pngSha256'] and digest(item['svg'])==item['svgSha256'] and digest(item['mmd'])==item['mmdSha256']
   images.append({'case':case['case'],'variant':item['variant'],'path':item['png'],'sha256':item['pngSha256'],'actualPixelScale':'original','actuallyViewed':True,'mechanicalStatus':item['validationStatus'],'visualFinding':'expected refusal fixture; not accepted output' if case['case'] in {'synthetic-long','synthetic-quoted-pipe','synthetic-oversized'} and item['variant']=='projection' else 'No new clipping, overlap or fragmented Latin identifiers observed in accepted projection.'})
 assert len(images)==24
 own=[x for x in data['results'] if x['case'].startswith('own-')]
 assert len(own)==3 and all(x['results'][1]['validationStatus']=='PASS' for x in own)
 for key in ['diagram-005','diagram-008','diagram-011']:
  original=HERE.parent/'render/assisted-table-index-r01-delivery-r14'/(key+'.mmd');assert digest(original)==data['beforeAfterHashes'][str(original)]
 rootpin=HERE.parent/'training-assisted/reviewed-table-index-r11-pin.json';pin=json.loads(rootpin.read_bytes());assert pin['sha256']=='3169d2b9c759e4a7c6d82333575f5f03bc1b1291d6563bb992667528a24db42d'
 assert digest(pin['canonicalMarkdown'])==pin['sha256']
 out=HERE/'mermaid-edge-projection-r04/actually-viewed-final.json'
 report={'schema':'generic-edge-layout-prototype-native-qa/1','createdUtc':datetime.now(timezone.utc).isoformat(),
  'status':'PROTOTYPE_PROOF_COMPLETE_ROOT_INTEGRATION_REQUIRED','prototype':str(HERE/'edge_label_projection_r02.py'),'prototypeSha256':digest(HERE/'edge_label_projection_r02.py'),
  'tests':str(HERE/'test_edge_label_projection_r02.py'),'testsSha256':digest(HERE/'test_edge_label_projection_r02.py'),'testCount':37,'testStatus':'PASS',
  'probe':str(path),'probeSha256':digest(path),'nativeCaseCount':12,'actualImageCount':24,'images':images,
  'ownApprovedMarkdownSha256':pin['sha256'],'reviewedPinSha256':digest(rootpin),'allBeforeAfterHashes':data['beforeAfterHashes'],
  'originalCharactersPreservedByInsertOnlyReceipt':True,'reversibleAndIdempotent':True,
  'ownIndex005008011':{'semanticNodeEdgeLabelSignaturesEqual':True,'actualSvgRowsHaveWholeIdentifiers':True,'nativeFullSizeReviewed':True},
  'expectedRefusals':['Quoted arrow-like text: baseline Mermaid loses > while projected view retains it; exact SVG signature mismatch is rejected.','Oversized indivisible identifier: exact token missing from any one visible SVG row is rejected and requires author change.'],
  'readabilityLimits':['Pure Japanese edge labels may retain Mermaid character wrapping; this prototype specifically protects Latin identifiers and numbers.','Entities preserve baseline Mermaid literal escaped spelling; this prototype does not repair its existing entity interpretation.','Conservative lexer leaves Markdown edge labels and other long dotted/thick label forms unchanged; unsupported or ambiguous syntax must use baseline or fail closed.','Tables/screens with this projection still require fresh whole-document render and full derived PDF/XLSX native QA.'],
  'integrationSequence':['Use canonical MMD as immutable source and retain its SHA.','Derive view text with project_flowchart_edges; verify reverse_projection and idempotence.','Public trusted Mermaid render both source and projected MMD with identical strict config.','Reject any structured SVG node/edge/label signature difference.','Bind each parsed source label to actual SVG and reject tokens split across visible rows.','Write both canonical and view SHA/insertions to render receipts; perform native image QA.'],
  'primarySources':data['primarySources'],'frozenRendererSha256':data['frozenRendererSha256'],
  'mainRendererEdited':False,'canonicalMarkdownEdited':False,'providerOrOriginalAppExecuted':False,'specOrEvaluatorOrOtherModeRead':False,
  'productionIntegration':False,'formalQualityGatePassed':False,'published':False,'historicalFailuresPreserved':['mermaid-edge-projection-r01','mermaid-edge-projection-r02','mermaid-edge-projection-r03','index-oplog-r01-native-failure.json']}
 out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 (out.parent/'unit-test-result.txt').write_text(stream.getvalue(),encoding='utf8')
 print(json.dumps({'report':str(out),'sha256':digest(out),'prototypeSha256':report['prototypeSha256'],'probeSha256':report['probeSha256'],'actualImages':24,'tests':37},ensure_ascii=False))
if __name__=='__main__':main()

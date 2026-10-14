"""Bind immutable reviewed/native-approved screen drafts for mechanical outputs."""
from pathlib import Path
import json,hashlib
from delivery_model import safe_path,load_bound
HERE=Path(__file__).resolve().parent;REPORT=HERE.parent;AGENT=HERE.parents[2];REPO=HERE.parents[4]
ASSISTED=AGENT/'.tmp/20261013-rerun-12h/training-assisted'
DOCROOT=REPO/'test-project1/spec-analysis/CSharp_ASPNET/20261013-rerun-12h/training-assisted/drafts'
CAP='e76a6c40e8927011fff9145d5f5ab2fa94ad89acefc9a03bbad0cbf09b85a0e7'
CASES=[('registration-basic','revision-registration-basic-r05','assisted-registration-basic-r07-delivery-r18','68fd61d7f911154cfc82489e6272a0b9eeedf33bb0bde4853193d14f385fbf18','ef8fc585211f4e3b9c06859e7aeb89933b80f49187a13bb6e2bbe8cd09b586ee'),('search-detail','revision-pending-r02-4a8437c580b548ac','assisted-search-detail-r04-delivery-r18','457f9c7680fc8c4447bded4bdc01218a25d01b55a4b735e39f50175f446a7c5f','9a49fb5a1d22094db7c57fdaf751807dd2f69c12367973ea839bc5ff9b037696')]
def sha(p):return hashlib.sha256(safe_path(p).read_bytes()).hexdigest()
def main():
 docs=[]
 for key,job,name,native_sha,md_sha in CASES:
  render=REPORT/'render'/name;pp=render/'render-pins.json';pins=json.loads(pp.read_text(encoding='utf8'))
  native=HERE/(name+'-native-qa.json');assert sha(native)==native_sha
  nr=json.loads(native.read_text(encoding='utf8'));assert nr['status']=='PASS_NATIVE_GEOMETRY_ONLY' and nr['documentSha256']==md_sha
  md=safe_path(pins['source']);assert md.is_relative_to(DOCROOT) and sha(md)==md_sha
  assert pins['referenceMode']=='training-assisted' and pins['rendererRuntimeLabel']=='r18'
  draft=ASSISTED/'jobs'/job/'draft-result.json'
  handoff=ASSISTED/'jobs'/(job+'-independent-review')/'review-handoff.json'
  review=handoff.with_name('review-verified.json');h=json.loads(handoff.read_text(encoding='utf8'));r=json.loads(review.read_text(encoding='utf8'))
  assert h['approved'] is True and h['referenceMode']=='training-assisted' and h['documentSha256']==md_sha and h['reviewSha256']==sha(review)
  assert h['snapshot']['manifestSha256']==CAP and r['approved'] is True and not r['findings'] and not r['unresolved']
  doc={'documentId':pins['documentId'],'canonicalDocumentPath':pins['canonicalDocumentPath'],'markdown':str(md),'markdownSha256':md_sha,'renderDirectory':str(render),'renderPinsSha256':sha(pp),'renderManifestSha256':sha(render/'manifest.json'),'draftResult':str(draft),'draftResultSha256':sha(draft),'nativeGeometryReview':str(native),'nativeGeometryReviewSha256':native_sha,'separateApprovedReview':{'handoff':str(handoff),'handoffSha256':sha(handoff),'review':str(review),'reviewSha256':sha(review),'approved':True,'scope':'text-source-and-structure'},'stateProjectionIncluded':False}
  docs.append(doc)
 bound={'schema':'reverse-agent-delivery-binding/1','referenceMode':'training-assisted','permittedMarkdownRoot':str(DOCROOT),'permittedRenderRoot':str(REPORT/'render'),'sourceSnapshotManifestSha256':CAP,'formalQualityGatePassed':False,'documents':docs,'wholeQualityApproved':False,'published':False}
 out=HERE/'binding-assisted-screens-r18-r01.json';assert not out.exists();out.write_text(json.dumps(bound,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 load_bound(out)
 print(json.dumps({'binding':str(out),'sha256':sha(out),'documents':len(docs)},ensure_ascii=False))
if __name__=='__main__':main()

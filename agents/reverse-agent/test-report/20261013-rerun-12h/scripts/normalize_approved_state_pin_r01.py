"""Normalize metadata schemas only; require exact AI HTML and actual zero-finding review."""
from datetime import datetime, timezone
from pathlib import Path
import argparse
import hashlib
import json
from contextbase.ai import capsule

REPORT=Path(__file__).resolve().parents[1]
REPO=REPORT.parents[3]
MODE='training-assisted'
CAP_SHA='e76a6c40e8927011fff9145d5f5ab2fa94ad89acefc9a03bbad0cbf09b85a0e7'

def safe(path):
    path=capsule.safe_path(Path(path))
    if not path.is_relative_to(REPO) or any(p.casefold() in ('evaluator-only','spec-eval') for p in path.parts):
        raise ValueError('Projection metadata path leaves the authorized repository scope')
    return path
def sha(path):return hashlib.sha256(safe(path).read_bytes()).hexdigest()
def load(path):return json.loads(safe(path).read_text(encoding='utf-8-sig'))

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--pin',type=Path,required=True)
    parser.add_argument('--pin-sha256',required=True)
    parser.add_argument('--parent-sha256',required=True)
    parser.add_argument('--document-id',required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    original=safe(args.pin)
    if sha(original)!=args.pin_sha256:raise ValueError('Exact export receipt required')
    value=load(original)
    if (value['schema']!='assisted-state-export-pin/1' or value['mode']!=MODE or
        value['parentDocumentSha256']!=args.parent_sha256 or value['documentId']!=args.document_id or
        value['capsuleManifestSha256']!=CAP_SHA):
        raise ValueError('Export metadata leaves the explicit parent or capsule')
    names={'input-pins.json','input-after.json','projection-verified.json','projection-review-verified.json','projection-result.json'}
    if set(value['files'])!=names:raise ValueError('All five verified projection receipts required')
    for entry in value['files'].values():
        if sha(entry['path'])!=entry['sha256']:raise ValueError('One verified receipt changed')
    files={name:safe(entry['path']) for name,entry in value['files'].items()}
    before,after=load(files['input-pins.json']),load(files['input-after.json'])
    parent=before['parent']
    if (parent['documentId']!=args.document_id or parent['sha256']!=args.parent_sha256 or
        before['documentId']!=args.document_id or before['mode']!=MODE or
        before['capsule']['manifestSha256']!=CAP_SHA or after['status']!='UNCHANGED' or after['pins']!=before):
        raise ValueError('Parent and before/after projection bindings differ')
    canonical=safe(parent['path'])
    if sha(canonical)!=args.parent_sha256:raise ValueError('Canonical parent changed')
    for path,digest in before['pinnedFiles'].items():
        if sha(path)!=digest:raise ValueError('One original input, runtime, helper, or old artifact changed')
    inventory=before['runtimeInventory']
    directory=safe(inventory['directory'])
    actual={p.relative_to(directory).as_posix():sha(p) for p in directory.rglob('*')
        if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc'}
    if actual!=inventory['files']:raise ValueError('Frozen runtime membership or bytes changed')
    projection,review,result=[load(files[name]) for name in
        ('projection-verified.json','projection-review-verified.json','projection-result.json')]
    if (review['approved'] is not True or review['findings'] or review['unresolved'] or
        review['documentId']!=args.document_id or review['parentDocumentSha256']!=args.parent_sha256 or
        review['projectionSha256']!=sha(files['projection-verified.json']) or
        projection['documentId']!=args.document_id or projection['parentDocumentSha256']!=args.parent_sha256 or
        projection['capsuleManifestSha256']!=CAP_SHA or projection['mode']!=MODE or
        result['independentReviewApproved'] is not True or result['projectionMeaningVerified'] is not True):
        raise ValueError('An actual zero-finding independent review of this exact projection is required')
    states={s['id']:s for s in projection['states']}
    if set(states)!={'initial','normal','error','view-edit'} or len(projection['states'])!=4:
        raise ValueError('Exactly four projected modes required')
    if len(value['states'])!=4 or {s['id'] for s in value['states']}!=set(states):
        raise ValueError('The export must bind every mode exactly once')
    html=[]
    for entry in value['states']:
        state=states[entry['id']]
        path=safe(entry['path'])
        if (state['requiresCanonicalRevision'] or state['canonicalRevisionReason'] or
            entry['requiresCanonicalRevision'] or not state['html'] or sha(path)!=entry['sha256'] or
            path.read_bytes()!=state['html'].encode('utf-8')):
            raise ValueError('Only exact nonempty AI HTML without canonical gaps is capturable')
        html.append({'stateId':entry['id'],'path':str(path),'sha256':entry['sha256'],'aiHtmlVerbatim':True})
    output=safe(args.output)
    if not output.is_relative_to(REPORT) or output.exists():raise ValueError('Fresh report metadata output required')
    normalized={'schema':'root-normalized-reviewed-state-export/1','createdAt':datetime.now(timezone.utc).isoformat(),
        'originalPin':str(original),'originalPinSha256':args.pin_sha256,'documentId':args.document_id,
        'canonicalMarkdown':str(canonical),'parentSha256':args.parent_sha256,'mode':MODE,
        'capsuleManifestSha256':CAP_SHA,'projectionFile':str(files['projection-verified.json']),
        'projectionSha256':sha(files['projection-verified.json']),
        'independentReview':str(files['projection-review-verified.json']),
        'independentReviewSha256':sha(files['projection-review-verified.json']),
        'result':str(files['projection-result.json']),'resultSha256':sha(files['projection-result.json']),
        'before':str(files['input-pins.json']),'beforeSha256':sha(files['input-pins.json']),
        'after':str(files['input-after.json']),'afterSha256':sha(files['input-after.json']),
        'independentReviewApproved':True,'findings':[],'unresolved':[],'html':html,
        'businessHtmlChanged':False,'metadataNormalizationOnly':True,'nativeApproval':False,'finalQualified':False}
    output.write_text(json.dumps(normalized,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    if sha(original)!=args.pin_sha256 or sha(canonical)!=args.parent_sha256:raise ValueError('Post-normalization drift')
    print(json.dumps({'documentId':args.document_id,'states':len(html),'pin':str(output),'sha256':sha(output)}))

if __name__=='__main__':main()

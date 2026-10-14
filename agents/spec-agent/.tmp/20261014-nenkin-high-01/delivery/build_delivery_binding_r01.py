"""Metadata-only bridge from approved collector/render records to delivery binding.
Never execute their helpers, reconstruct Markdown, start providers, or publish.
Actual records may be read only after a pinned root selection/grant is supplied.
"""
import argparse,hashlib,json
from pathlib import Path
from publication_bound_r03 import WORK,REPORT,safe,owned,relative,pinned,unique_json,require,hashfile,fresh_json

COLLECTOR=WORK/'collect_reviewed_r07.py'
COLLECTOR_SHA='ee8419432a9b553c04ba757a2b188c86614ae230d980c5822ac8d8fe17a40a50'
RENDERER=WORK/'render_reviewed_r04.py'
RENDERER_SHA='888db1128cc0f5dc0ab942e18fb4476e4f0ce79cf1aa2d1e3bd75324952571be'

def metadata_model(selection,collection,grant,records):
    """Pure schema/identity bridge. records contain already hash-checked JSON."""
    require(selection.get('schema')=='spec-agent-delivery-binding-selection/1','binding selection schema')
    require(grant.get('schema')=='spec-agent-delivery-binding-grant/1' and grant.get('allowBinding') is True,'root binding grant')
    require(grant.get('selectionSha256')==selection.get('_selectionSha256'),'grant binds exact selection')
    require(collection.get('schema')=='spec-agent-text-reviewed-collection/1' and collection.get('inputBeforeAfterUnchanged') is True and collection.get('bodyTransformationPerformed') is False and collection.get('semanticProseAssembledByPython') is False,'immutable reviewed collection required')
    capsule=collection.get('capsule',{});require(capsule.get('mode')=='source-only' and capsule.get('manifestSha256')==grant.get('sourceSnapshotManifestSha256'),'source-only dynamic sourcecap')
    require(grant.get('collectionSha256')==selection['collection']['sha256'],'approved collection bytes')
    root=safe(collection['outputRoot']);require(root.is_relative_to(WORK/'collections'),'reviewed collection root must be owned collections')
    renderroot=safe(selection['permittedRenderRoot']);require(renderroot.is_relative_to(WORK/'renders'),'new owned render root required')
    byid={}
    for doc in collection['documents']:
        require(doc['documentId'] not in byid,'duplicate collected document');byid[doc['documentId']]=doc
    rows=selection.get('documents');require(isinstance(rows,list) and rows,'explicit nonempty selected render metadata')
    ids=[row.get('documentId') for row in rows];require(all(isinstance(i,str) and i for i in ids) and len(ids)==len(set(ids)),'explicit unique selected document IDs')
    require(set(ids)==set(grant.get('approvedDocumentIds',[])),'root-approved selected ID set')
    require(len(records)==len(rows),'exact selected record count');out=[];paths=set()
    for row,bundle in zip(rows,records):
        require(row['documentId'] in byid,'render selection not in reviewed collection');doc=byid[row['documentId']]
        require(doc.get('reportOnly') is False and doc.get('kind')!='analysis-report','report-only documents excluded')
        require(doc.get('independentReviewApproved') is True and doc.get('structureStatus')=='STRUCTURE_VALID','review/structure not complete')
        cp=relative(doc['path']);require(cp.suffix=='.md' and cp.as_posix().casefold() not in paths,'unique canonical MD path');paths.add(cp.as_posix().casefold())
        md=safe(doc['canonicalMarkdown']);require(md==root/cp,'canonical collection path mismatch')
        render=safe(row['renderDirectory']);require(render.is_relative_to(renderroot),'render outside explicit root')
        pins,manifest=bundle['pins'],bundle['manifest']
        require(pins.get('schema')=='spec-agent-render-pins/1' and pins.get('documentId')==doc['documentId'] and pins.get('canonicalDocumentPath')==doc['path'],'render pin identity')
        require(pins.get('collectorDocument')==doc and pins.get('collectionSha256')==selection['collection']['sha256'] and pins.get('source')==str(md),'render belongs to exact collected document')
        require(pins.get('helper')==str(RENDERER) and pins.get('helperSha256')==RENDERER_SHA,'audited render helper identity')
        require(pins.get('sourceSnapshotManifestSha256')==capsule['manifestSha256'] and pins.get('referenceMode')=='source-only','render mode/capsule mismatch')
        require(pins.get('renderManifestSha256')==row['renderManifestSha256'] and manifest.get('canonicalHtmlCopyIsByteIdentical') is True,'enriched manifest binding')
        require(pins.get('canonicalHtmlFilename')==cp.stem+'.html' and manifest.get('canonicalHtmlFilename')==cp.stem+'.html','original canonical HTML stem')
        for value in (pins,manifest):
            require(value.get('sourceSha256')==doc['sha256'] and value.get('originalModified') is False,'source text drift')
            require(value.get('structure',{}).get('status')=='PASS' and not value['structure'].get('findings'),'typed structure errors')
            require(value.get('display',{}).get('status')=='PASS' and not value['display'].get('blockedRequests') and not value['display'].get('errors'),'incomplete display')
            require(not value.get('safety',{}).get('removed') and value['safety'].get('inputJavaScriptEnabled') is False,'changed or active source rendering')
        out.append({'documentId':doc['documentId'],'canonicalDocumentPath':doc['path'],'markdown':str(md),'markdownSha256':doc['sha256'],'renderDirectory':str(render),'renderPinsSha256':row['renderPinsSha256'],'renderManifestSha256':row['renderManifestSha256'],'sourceSnapshotManifestSha256':capsule['manifestSha256'],'reviewEvidence':{'collectionSha256':selection['collection']['sha256'],'sourcePinSha256':doc['sourcePinSha256'],'independentReviewSha256':doc['independentReviewSha256'],'scope':'TEXT_REVIEW_ONLY'},'visualApproval':'NOT_GRANTED_BY_BINDING','formalPercentage':None})
    return {'schema':'reverse-agent-delivery-binding/1','permittedMarkdownRoot':str(root),'permittedRenderRoot':str(renderroot),'sourceSnapshotManifestSha256':capsule['manifestSha256'],'referenceMode':'source-only','documents':out,'bodyTransformationPerformed':False,'bindingApprovalScope':'METADATA_CONNECTION_ONLY','published':False}

def build(selection_path,selection_sha,grant_path,grant_sha,output,receipt_path):
    selection_file=pinned({'path':str(selection_path),'sha256':selection_sha});grant_file=pinned({'path':str(grant_path),'sha256':grant_sha})
    selection=unique_json(selection_file.read_bytes());selection['_selectionSha256']=selection_sha;grant=unique_json(grant_file.read_bytes())
    require(hashfile(COLLECTOR)==COLLECTOR_SHA and hashfile(RENDERER)==RENDERER_SHA,'audited metadata producer code changed')
    collection_file=pinned(selection['collection']);require(collection_file.is_relative_to(REPORT),'collection evidence must stay in REPORT')
    collection=unique_json(collection_file.read_bytes());records=[];inputs={str(selection_file):selection_sha,str(grant_file):grant_sha,str(collection_file):selection['collection']['sha256'],str(COLLECTOR):COLLECTOR_SHA,str(RENDERER):RENDERER_SHA}
    for row in selection['documents']:
        directory=safe(row['renderDirectory']);require(directory.is_relative_to(WORK/'renders'),'new owned rendered assets only')
        pins_path=pinned({'path':str(directory/'render-pins.json'),'sha256':row['renderPinsSha256']});manifest_path=pinned({'path':str(directory/'manifest.json'),'sha256':row['renderManifestSha256']})
        pins=unique_json(pins_path.read_bytes());manifest=unique_json(manifest_path.read_bytes());records.append({'pins':pins,'manifest':manifest})
        inputs[str(pins_path)]=row['renderPinsSha256'];inputs[str(manifest_path)]=row['renderManifestSha256']
    binding=metadata_model(selection,collection,grant,records)
    for doc,bundle in zip(binding['documents'],records):
        require(hashfile(Path(doc['markdown']))==doc['markdownSha256'],'reviewed MD bytes drift');inputs[doc['markdown']]=doc['markdownSha256']
        directory=Path(doc['renderDirectory']);pins=bundle['pins'];manifest=bundle['manifest']
        seen=set()
        for artifact in manifest['artifacts']:
            name=artifact['path'];require(relative(name).name==name and name not in seen,'one unique render artifact filename');seen.add(name)
            path=safe(directory/name);require(path.is_relative_to(directory) and hashfile(path)==artifact['sha256'],'render artifact drift');inputs[str(path)]=artifact['sha256']
        canonical=safe(directory/pins['canonicalHtmlFilename']);require(hashfile(canonical)==pins['canonicalHtmlSha256'] and canonical.read_bytes()==safe(directory/'document.html').read_bytes(),'canonical HTML exact copy')
    for path,digest in inputs.items():require(hashfile(Path(path))==digest,'input changed before binding write')
    output=owned(output);receipt_path=owned(receipt_path);require(output!=receipt_path and not output.exists() and not receipt_path.exists(),'fresh separate binding/receipt')
    require(all(output!=Path(p) and receipt_path!=Path(p) for p in inputs),'output overwrites pinned input')
    fresh_json(output,binding)
    for path,digest in inputs.items():require(hashfile(Path(path))==digest,'input changed after binding write')
    result={'schema':'spec-agent-delivery-binding-build/1','bindingPath':str(output),'bindingSha256':hashfile(output),'selectedDocumentIds':[d['documentId'] for d in binding['documents']],'sourceSnapshotManifestSha256':binding['sourceSnapshotManifestSha256'],'inputPins':inputs,'inputBeforeAfterUnchanged':True,'bodyReadForShaOnly':True,'businessTextRewritten':False,'actualPdfOrXlsxCreated':False,'nativeApproval':False,'formalPercentage':None,'published':False}
    fresh_json(receipt_path,result);return result

def main():
    p=argparse.ArgumentParser();p.add_argument('--selection',type=Path,required=True);p.add_argument('--selection-sha256',required=True);p.add_argument('--grant',type=Path,required=True);p.add_argument('--grant-sha256',required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--receipt',type=Path,required=True)
    a=p.parse_args();print(json.dumps(build(a.selection,a.selection_sha256,a.grant,a.grant_sha256,a.output,a.receipt),ensure_ascii=False))
if __name__=='__main__':main()

"""Metadata-only bridge from approved collector/render records to delivery binding.
Never execute their helpers, reconstruct Markdown, start providers, or publish.
Actual records may be read only after a pinned root selection/grant is supplied.
"""
import argparse,hashlib,json,re
import publication_bound_r03 as guard_module
from pathlib import Path
from publication_bound_r03 import WORK,REPORT,safe,owned,relative,pinned,unique_json,require,hashfile,fresh_json,descriptor_shape

COLLECTOR=WORK/'collect_reviewed_r09.py'
COLLECTOR_SHA='3788d437323b5db059a3afd908d7ba0dbd3b1dcd3ec7395502fe77e95c3392bc'
RENDERER=WORK/'render_reviewed_r05.py'
RENDERER_SHA='b3e69f6c2cbce03d8e1e2a833f14b31d7acb85c2ee9aae60fa25a1ae2c4641fe'

GUARD=WORK/'delivery/publication_bound_r03.py'
GUARD_SHA='8be4c01b30a73eade999d78a039ba46911167882140f37c028c051716fc7fa6f'

# Exact audited collector7/guard3 frozen code identity; not a business input root.
FROZEN_RUNTIME_ROOT=Path(r'D:\\開発\\contextbase-evaluation\\agents\\reverse-agent\\.tmp\\20261013-rerun-12h\\source-only\\runtime-code\\source-13\\src')
FROZEN_RUNTIME_RECEIPT=Path(r'D:\\開発\\contextbase-evaluation\\agents\\reverse-agent\\test-report\\20261013-rerun-12h\\source-pilot\\runtime-code-source-13.json')
FROZEN_RUNTIME_RECEIPT_SHA='5c3eeafb764afb64e3ef80fb422e4f68a9c41b98f000d13a8d57a505d947cc79'
FROZEN_RUNTIME_FILES_SHA='07cc2d4ed07018b06be89a3f3df1083fc13e8368137ae9b3c8e0344bb9be66f0'
FROZEN_RUNTIME_IMPORTS={'contextbase': 'contextbase/__init__.py', 'contextbase.__main__': 'contextbase/__main__.py', 'contextbase.ai': 'contextbase/ai/__init__.py', 'contextbase.ai.__main__': 'contextbase/ai/__main__.py', 'contextbase.ai.workflow': 'contextbase/ai/workflow.py', 'contextbase.ai.provider': 'contextbase/ai/provider.py', 'contextbase.ai.prompts': 'contextbase/ai/prompts.py', 'contextbase.ai.schemas': 'contextbase/ai/schemas.py', 'contextbase.ai.validation': 'contextbase/ai/validation.py', 'contextbase.ai.iteration': 'contextbase/ai/iteration.py', 'contextbase.ai.document_contract': 'contextbase/ai/document_contract.py', 'docsite': 'docsite/__init__.py', 'specgen': 'specgen/__init__.py'}
FROZEN_RUNTIME_CRITICAL=('contextbase.ai.capsule','contextbase.ai.workflow','contextbase.ai.provider','contextbase.ai.prompts','contextbase.ai.schemas','contextbase.ai.validation','contextbase.ai.plan_review')

def canonical_metadata_sha(value):
    return hashlib.sha256(json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode('utf-8')).hexdigest()

def digest(value):
    require(isinstance(value,str) and re.fullmatch('[0-9a-f]{64}',value) is not None,'exact lower SHA256 required')
    return value

def approved_ids(values):
    require(isinstance(values,list) and values and all(isinstance(v,str) and v for v in values) and len(values)==len(set(values)),'nonempty unique approved ID list required')
    return set(values)

def metadata_model(selection,collection,grant,records):
    """Pure schema/identity bridge. records contain already hash-checked JSON."""
    require(selection.get('schema')=='spec-agent-delivery-binding-selection/1','binding selection schema')
    require(grant.get('schema')=='spec-agent-delivery-binding-grant/1' and grant.get('allowBinding') is True,'root binding grant')
    require(digest(grant.get('selectionSha256'))==digest(selection.get('_selectionSha256')),'grant binds exact selection')
    descriptor_shape(selection.get('collection'))
    require(collection.get('schema')=='spec-agent-text-reviewed-collection/1' and collection.get('inputBeforeAfterUnchanged') is True and collection.get('bodyTransformationPerformed') is False and collection.get('semanticProseAssembledByPython') is False,'immutable reviewed collection required')
    capsule=collection.get('capsule',{});require(capsule.get('mode')=='source-only' and digest(capsule.get('manifestSha256'))==digest(grant.get('sourceSnapshotManifestSha256')),'source-only dynamic sourcecap')
    runtime=collection.get('runtimeProvenance',{});require(digest(runtime.get('receiptSha256'))==digest(grant.get('runtimeReceiptSha256'))==FROZEN_RUNTIME_RECEIPT_SHA,'exact source13 runtime receipt required')
    runtime_root=safe(runtime['runtimeRoot']);require(runtime_root==safe(grant['permittedRuntimeRoot'])==safe(FROZEN_RUNTIME_ROOT),'exact audited source13 frozen root required')
    files=runtime.get('runtimeFiles');require(isinstance(files,dict) and type(runtime.get('runtimeFileCount')) is int and runtime['runtimeFileCount']==len(files)==128,'exact source13 full128 metadata required')
    for name,value in files.items():relative(name);digest(value)
    require(canonical_metadata_sha(files)==FROZEN_RUNTIME_FILES_SHA,'source13 full128 inventory identity mismatch')
    loaded=runtime.get('loadedImports');require(isinstance(loaded,dict) and set(loaded)==set(FROZEN_RUNTIME_IMPORTS),'exact thirteen frozen receipt import identities required')
    for name,rel in FROZEN_RUNTIME_IMPORTS.items():
        require(loaded[name]=={'path':str(runtime_root/rel),'sha256':files[rel]},'frozen receipt loaded module metadata differs')
    critical=runtime.get('criticalModules');require(isinstance(critical,dict) and set(critical)==set(FROZEN_RUNTIME_CRITICAL),'exact seven frozen critical module identities required')
    for name in FROZEN_RUNTIME_CRITICAL:
        rel=name.replace('.','/')+'.py';require(critical[name]=={'path':str(runtime_root/rel),'sha256':files[rel]},'frozen critical loaded module metadata differs')
    expected_renderer=runtime_root/'contextbase/ai/rendering.py';renderer_sha=digest(files.get('contextbase/ai/rendering.py'))
    require(digest(grant.get('collectionSha256'))==digest(selection['collection']['sha256']),'approved collection bytes')
    require(safe(selection['collection']['path']).is_relative_to(REPORT),'collection evidence belongs to this REPORT')
    root=safe(collection['outputRoot']);require(root.is_relative_to(WORK/'collections'),'reviewed collection root must be owned collections')
    renderroot=safe(selection['permittedRenderRoot']);require(renderroot.is_relative_to(WORK/'renders'),'new owned render root required')
    byid={}
    for doc in collection['documents']:
        require(doc['documentId'] not in byid,'duplicate collected document');byid[doc['documentId']]=doc
    rows=selection.get('documents');require(isinstance(rows,list) and rows,'explicit nonempty selected render metadata')
    ids=[row.get('documentId') for row in rows];require(all(isinstance(i,str) and i for i in ids) and len(ids)==len(set(ids)),'explicit unique selected document IDs')
    require(set(ids)==approved_ids(grant.get('approvedDocumentIds')),'root-approved selected ID set')
    require(len(records)==len(rows),'exact selected record count');out=[];paths=set();renderdirs=set()
    for row,bundle in zip(rows,records):
        require(row['documentId'] in byid,'render selection not in reviewed collection');doc=byid[row['documentId']]
        require(doc.get('reportOnly') is False and doc.get('kind')!='analysis-report','report-only documents excluded')
        require(doc.get('independentReviewApproved') is True and doc.get('structureStatus')=='STRUCTURE_VALID','review/structure not complete')
        for field in ('sha256','sourcePinSha256','draftResultSha256','independentReviewSha256','analysisHandoffSha256'):digest(doc.get(field))
        for field in ('renderPinsSha256','renderManifestSha256'):digest(row.get(field))
        cp=relative(doc['path']);require(cp.suffix=='.md' and cp.as_posix().casefold() not in paths,'unique canonical MD path');paths.add(cp.as_posix().casefold())
        md=safe(doc['canonicalMarkdown']);require(md==root/cp,'canonical collection path mismatch')
        render=safe(row['renderDirectory']);require(render!=renderroot and render.is_relative_to(renderroot),'render outside explicit root')
        require(str(render).casefold() not in renderdirs,'each document needs its own render directory');renderdirs.add(str(render).casefold())
        pins,manifest=bundle['pins'],bundle['manifest']
        require(pins.get('schema')=='spec-agent-render-pins/1' and pins.get('documentId')==doc['documentId'] and pins.get('canonicalDocumentPath')==doc['path'],'render pin identity')
        require(pins.get('collectorDocument')==doc and pins.get('collectionSha256')==selection['collection']['sha256'] and pins.get('source')==str(md),'render belongs to exact collected document')
        require(pins.get('helper')==str(RENDERER) and pins.get('helperSha256')==RENDERER_SHA,'audited render helper identity')
        require(pins.get('collection')==selection['collection']['path'],'exact collection evidence path')
        require(pins.get('renderer')==str(expected_renderer) and digest(pins.get('rendererSha256'))==renderer_sha,'renderer must match root-approved full runtime metadata')
        require(pins.get('sourceSnapshotManifestSha256')==capsule['manifestSha256'] and pins.get('referenceMode')=='source-only','render mode/capsule mismatch')
        require(pins.get('renderManifestSha256')==row['renderManifestSha256'] and manifest.get('canonicalHtmlCopyIsByteIdentical') is True,'enriched manifest binding')
        require(pins.get('canonicalHtmlFilename')==cp.stem+'.html' and manifest.get('canonicalHtmlFilename')==cp.stem+'.html','original canonical HTML stem')
        canonical_sha=digest(pins.get('canonicalHtmlSha256'));original_manifest_sha=digest(pins.get('originalRendererManifestSha256'))
        require(digest(manifest.get('originalRendererManifestSha256'))==original_manifest_sha,'original renderer manifest exact pin')
        artifacts=manifest.get('artifacts');require(isinstance(artifacts,list) and artifacts,'full native artifact metadata required')
        artifact_map={}
        for artifact in artifacts:
            name=artifact.get('path');require(relative(name).name==name and name.casefold() not in artifact_map,'unique one-level artifact filename required')
            artifact_map[name.casefold()]=digest(artifact.get('sha256'))
        require(artifact_map.get('document.html')==canonical_sha and artifact_map.get((cp.stem+'.html').casefold())==canonical_sha,'canonical and source HTML artifact bytes must be identical')
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
    require(safe(guard_module.__file__)==GUARD and hashfile(GUARD)==GUARD_SHA,'reviewed guard module path/bytes changed')
    require(hashfile(COLLECTOR)==COLLECTOR_SHA and hashfile(RENDERER)==RENDERER_SHA,'audited metadata producer code changed')
    require(hashfile(FROZEN_RUNTIME_RECEIPT)==FROZEN_RUNTIME_RECEIPT_SHA,'audited technical runtime receipt bytes changed')
    collection_file=pinned(selection['collection']);require(collection_file.is_relative_to(REPORT),'collection evidence must stay in REPORT')
    collection=unique_json(collection_file.read_bytes());records=[];inputs={str(selection_file):selection_sha,str(grant_file):grant_sha,str(collection_file):selection['collection']['sha256'],str(COLLECTOR):COLLECTOR_SHA,str(RENDERER):RENDERER_SHA,str(GUARD):GUARD_SHA,str(safe(__file__)):hashfile(Path(__file__)),str(FROZEN_RUNTIME_RECEIPT):FROZEN_RUNTIME_RECEIPT_SHA}
    for row in selection['documents']:
        directory=safe(row['renderDirectory']);require(directory.is_relative_to(WORK/'renders'),'new owned rendered assets only')
        pins_path=pinned({'path':str(directory/'render-pins.json'),'sha256':row['renderPinsSha256']});manifest_path=pinned({'path':str(directory/'manifest.json'),'sha256':row['renderManifestSha256']})
        pins=unique_json(pins_path.read_bytes());manifest=unique_json(manifest_path.read_bytes());records.append({'pins':pins,'manifest':manifest})
        inputs[str(pins_path)]=row['renderPinsSha256'];inputs[str(manifest_path)]=row['renderManifestSha256']
    binding=metadata_model(selection,collection,grant,records)
    for doc,bundle in zip(binding['documents'],records):
        require(hashfile(Path(doc['markdown']))==doc['markdownSha256'],'reviewed MD bytes drift');inputs[doc['markdown']]=doc['markdownSha256']
        directory=Path(doc['renderDirectory']);pins=bundle['pins'];manifest=bundle['manifest']
        inputs[str(safe(pins['renderer']))]=pins['rendererSha256'];require(hashfile(Path(pins['renderer']))==pins['rendererSha256'],'approved frozen renderer bytes drift')
        original_manifest=pinned({'path':str(directory/'renderer-original-manifest.json'),'sha256':pins['originalRendererManifestSha256']});inputs[str(original_manifest)]=pins['originalRendererManifestSha256']
        seen=set()
        for artifact in manifest['artifacts']:
            name=artifact['path'];require(relative(name).name==name and name not in seen,'one unique render artifact filename');seen.add(name)
            path=safe(directory/name);require(path.is_relative_to(directory) and hashfile(path)==artifact['sha256'],'render artifact drift');inputs[str(path)]=artifact['sha256']
        canonical=safe(directory/pins['canonicalHtmlFilename']);require(hashfile(canonical)==pins['canonicalHtmlSha256'] and canonical.read_bytes()==safe(directory/'document.html').read_bytes(),'canonical HTML exact copy')
    for path,digest in inputs.items():require(hashfile(Path(path))==digest,'input changed before binding write')
    output=owned(output);receipt_path=owned(receipt_path);require(output!=receipt_path and not output.exists() and not receipt_path.exists(),'fresh separate binding/receipt')
    require(all(output!=Path(p) and receipt_path!=Path(p) for p in inputs),'output overwrites pinned input')
    forbidden=[safe(binding['permittedMarkdownRoot']),safe(binding['permittedRenderRoot']),safe(collection['runtimeProvenance']['runtimeRoot'])]
    require(all(not candidate.is_relative_to(root) for candidate in (output,receipt_path) for root in forbidden),'binding metadata must not enter canonical/render/runtime roots')
    fresh_json(output,binding)
    for path,digest in inputs.items():require(hashfile(Path(path))==digest,'input changed after binding write')
    result={'schema':'spec-agent-delivery-binding-build/1','bindingPath':str(output),'bindingSha256':hashfile(output),'selectedDocumentIds':[d['documentId'] for d in binding['documents']],'sourceSnapshotManifestSha256':binding['sourceSnapshotManifestSha256'],'inputPins':inputs,'inputBeforeAfterUnchanged':True,'bodyReadForShaOnly':True,'businessTextRewritten':False,'actualPdfOrXlsxCreated':False,'nativeApproval':False,'formalPercentage':None,'published':False}
    fresh_json(receipt_path,result);return result

def main():
    p=argparse.ArgumentParser();p.add_argument('--selection',type=Path,required=True);p.add_argument('--selection-sha256',required=True);p.add_argument('--grant',type=Path,required=True);p.add_argument('--grant-sha256',required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--receipt',type=Path,required=True)
    a=p.parse_args();print(json.dumps(build(a.selection,a.selection_sha256,a.grant,a.grant_sha256,a.output,a.receipt),ensure_ascii=False))
if __name__=='__main__':main()

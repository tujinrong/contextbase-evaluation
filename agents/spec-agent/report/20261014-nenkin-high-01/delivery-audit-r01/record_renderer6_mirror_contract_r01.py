"""Renderer source contract only; no renderer import, execution, or output access."""
import ast,hashlib,json
from pathlib import Path
from datetime import datetime,timezone
A=Path(r'D:\開発\contextbase-evaluation\agents\spec-agent\report\20261014-nenkin-high-01\delivery-audit-r01')
W=Path(r'D:\開発\contextbase-evaluation\agents\spec-agent\.tmp\20261014-nenkin-high-01')
p=W/'render_reviewed_r06.py';expected='eada05d737ed3bbf9bf0173681eb117024c9a1fa49d778040de51bdd43b40b02'
def sha(raw):return hashlib.sha256(raw).hexdigest()
raw=p.read_bytes();assert sha(raw)==expected;text=raw.decode('utf-8');tree=ast.parse(text)
functions={n.name:ast.get_source_segment(text,n) for n in tree.body if isinstance(n,ast.FunctionDef)}
prepare=functions['prepare_citation_mirror'];verify=functions['verify_citation_mirror'];main=functions['main'];inv=functions['mirror_inventory']
checks={
 'owner-sha-ID-NUL-collection-NUL-render-NUL-canonicalpath':"document['documentId'] + '\\0' + collection_sha + '\\0' + str(output) + '\\0' + path.as_posix()" in prepare,
 'owner-root-mirror-fixed-template':"RUN / 'render-citation-roots' / key" in prepare and "owner / 'root'" in prepare and "location = 'md/' + path.as_posix()" in prepare,
 'fresh-single-document-owner':"not owner.exists() and not root.exists()" in prepare,
 'original-source-bytehash-before-copy':"hashlib.sha256(source_bytes).hexdigest() == document['sha256']" in prepare,
 'copy-entire-original-source-bytes':"fresh(mirror, source_bytes)" in prepare,
 'copy-inverse-byte-and-exclusive-inventory':"mirror.read_bytes() == source_bytes" in prepare and 'mirror_inventory(root, location) == expected' in prepare,
 'inventory-only-approved-file-and-ancestor-dirs':"name in expected_dirs" in inv and "name == final_markdown_location" in inv and "set(files) == {final_markdown_location}" in inv,
 'verify-original-and-mirror-full-byte-equality':"original.read_bytes() == mirror.read_bytes()" in verify,
 'render-input-source-is-mirror-and-assetroot-is-mirrorroot':'rendering.render_document(mirror_source, output' in main and 'asset_root=mirror_root' in main,
 'raw-renderer-manifest-source-mirror-and-sha-original':"result['source'] == str(mirror_source)" in main and "result['sourceSha256'] == document['sha256']" in main,
 'mirror-verification-before-after-render-and-before-finalpins':main.count('verify_citation_mirror(mirror_mapping)')==3,
 'mapping-added-enriched-manifest-and-pins':"result['citationMirror'] = mirror_mapping" in main and "'citationMirror': mirror_mapping" in main,
 'mapping-beforeafter-flag-final-true':"mirror_mapping['beforeAfterByteEqualityVerified'] = True" in main,
 'pins-original-source-and-renderermirror-source-separate':"'source': str(source)" in main and "'rendererSource': str(mirror_source)" in main,
}
assert all(checks.values())
assert sha(p.read_bytes())==expected
record={'schema':'spec-agent-renderer6-mirror-code-contract-audit/1','createdUtc':datetime.now(timezone.utc).isoformat(),
 'scope':'RENDERER_SOURCE_CODE_SCHEMA_ONLY','status':'CONTRACT_IDENTIFIED_BINDING7_PROBES_PENDING',
 'renderer':{'path':str(p),'sha256':expected},'schema':'spec-agent-render-citation-mirror/1',
 'mappingFields':['owner','root','mirrorFile','mirrorSha256','originalSource','originalSourceSha256','canonicalDocumentPath','finalMarkdownLocation','finalFolderPrefixes','inventory','scope','businessTextRewritten','additionalSourceOrAssetReadsAuthorized','beforeAfterByteEqualityVerified'],
 'ownerKeyAlgorithm':'SHA256(UTF8(documentId + NUL + collectionSha256 + NUL + str(safe(renderOutput)) + NUL + canonicalDocumentPathPOSIX))',
 'ownerRootTemplate':'WORK/render-citation-roots/<ownerKey>/root',
 'mirrorTemplate':'<ownerRoot>/md/<unchanged canonicalDocumentPath>',
 'finalFolderPrefixes':['md','html','PDF','Excel'],
 'expectedInventory':'Exactly one md/<canonicalDocumentPath>→originalMarkdownSHA, plus only that path ancestor directories.',
 'sourcePathContract':{'pinsSource':'Original collection canonical Markdown','pinsRendererSource':'Mirror file',
     'untouchedRendererManifestSource':'Mirror file','enrichedManifestSource':'Mirror file',
     'everySourceSha':'Original collected Markdown SHA','originalAndMirrorBytes':'Entire raw bytes identical, including BOM if present'},
 'staticSourceChecks':checks,'staticCheckCount':len(checks),'sourceHelperBytesBeforeAfterUnchanged':True,
 'binding7Focus':['Recalculate owner key from selected ID/collectionSHA/renderdirectory/canonical path.',
    'Require owner/root/mirror exact template and pins/enriched manifest citationMirror equality.',
    'Bind original manifest source to mirror and original source to selected canonical collectionMD.',
    'Recheck entire original/mirror raw byte equality, only-file inventory and allowed ancestor dirs before/after binding write.'],
 'limitations':['Renderer verify_citation_mirror() itself does not recompute ownerKey or require owner/root template; binding7 should connect those metadata identities.',
    'No actual citation mirror or collected document exists/read status was inspected.',
    'No producer helper import, browser, frozen renderer, runtime, source capsule, provider, or authoring was executed.'],
 'producerImported':False,'producerExecuted':False,'actualInputRead':False,'actualOldOutputRead':False,'actualCapsuleRead':False,
 'actualCollectionRead':False,'actualRenderRecordsRead':False,'actualMarkdownRead':False,'actualPNGRead':False,'actualHTMLRead':False,
 'actualJobRead':False,'providerExecuted':False,'authoringExecuted':False,'markerExecuted':False,
 'semanticApproval':False,'formalQualityAssessed':False,'stateApproval':False,'wholeApproval':False,'adoption':False,'published':False,
 'reviewer':'/root/delivery_tools/registration_pdf_qa'}
target=A/'renderer6-mirror-contract-independent-code-r01.json'
with target.open('x',encoding='utf-8') as h:json.dump(record,h,ensure_ascii=False,indent=2);h.write('\n')
print(json.dumps({'path':str(target),'sha256':sha(target.read_bytes()),'staticCheckCount':len(checks)},ensure_ascii=False))

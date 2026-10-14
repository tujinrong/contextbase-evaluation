"""Offline views of pinned reviewed Markdown; canonical copies add no business content."""
from pathlib import Path
from datetime import datetime, timezone
import argparse, hashlib, importlib.util, json, sys
sys.dont_write_bytecode = True
RUN = Path(r'D:/開発/contextbase-evaluation/agents/spec-agent/.tmp/20261014-nenkin-high-01')
HELPER = RUN / 'review_plan_with_scope_r02.py'
HELPER_SHA = '52fb03f78b07ab9136881ece1ed76ac29a35ade053c77af9f8596d4300e0d98e'

def initial_safe(value):
    path = Path(value).absolute()
    for node in (path, *path.parents):
        if node.is_symlink() or (node.exists() and getattr(node.lstat(), 'st_file_attributes', 0) & 0x400):
            raise ValueError('Linked path refused before read/write')
    return path.resolve()

if hashlib.sha256(initial_safe(HELPER).read_bytes()).hexdigest() != HELPER_SHA:
    raise ValueError('Audited fixed provenance helper changed')
spec = importlib.util.spec_from_file_location('fixed_spec_scope_renderer', initial_safe(HELPER))
guard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(guard)
safe, sha, load, require = guard.safe, guard.sha, guard.load, guard.require

def inside(value, root):
    value, root = safe(value), safe(root)
    require(value != root and value.is_relative_to(root), 'Path must be within the explicit permitted root')
    return value

def fresh(path, data):
    path = safe(path)
    with path.open('xb') as stream:
        stream.write(data)

def json_bytes(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode('utf-8')

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--collection', required=True)
    parser.add_argument('--collection-sha256', required=True)
    parser.add_argument('--document-id', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--mermaid-package', required=True)
    parser.add_argument('--chromium-executable')
    args = parser.parse_args()
    runtime = guard.bootstrap()
    collection = inside(args.collection, guard.REPORT)
    require(sha(collection) == args.collection_sha256, 'Collection evidence bytes changed')
    collected = load(collection)
    require(collected['schema'] == 'spec-agent-text-reviewed-collection/1' and
            collected['inputBeforeAfterUnchanged'] is True and
            collected['bodyTransformationPerformed'] is False and
            collected['capsule']['manifestSha256'] == guard.SNAPSHOT_SHA and
            collected['capsule']['mode'] == 'source-only', 'Unexpected collection provenance')
    matched = [doc for doc in collected['documents'] if doc['documentId'] == args.document_id]
    require(len(matched) == 1, 'Exactly one selected document required')
    document = matched[0]
    require(document['independentReviewApproved'] is True and document['structureStatus'] == 'STRUCTURE_VALID',
            'Reviewed structure-valid document required')
    source = inside(document['canonicalMarkdown'], RUN / 'collections')
    output = inside(args.output, RUN / 'renders')
    require(not output.exists(), 'Fresh render output required')
    require(sha(source) == document['sha256'], 'Reviewed Markdown changed')
    mermaid = safe(args.mermaid_package)
    require(not mermaid.is_relative_to(guard.SNAPSHOT) and mermaid.is_dir(), 'Trusted separate Mermaid package required')
    executable = safe(args.chromium_executable) if args.chromium_executable else None
    from contextbase.ai import rendering, capsule
    from contextbase.ai.validation import validate_document
    renderer_file = safe(rendering.__file__)
    expected_renderer = safe(guard.RUNTIME / 'contextbase/ai/rendering.py')
    require(renderer_file == expected_renderer and
            sha(renderer_file) == runtime['runtimeFiles']['contextbase/ai/rendering.py'],
            'Loaded renderer is not the exact frozen module')
    require(not validate_document(source.read_text(encoding='utf-8'), document['path'],
                                  expected_document_id=document['documentId'], expected_kind=document['kind']),
            'Current typed document structure invalid')
    snapshot_before = capsule.verification_state(guard.SNAPSHOT)
    require(snapshot_before == collected['capsule'], 'Collection source capsule changed')
    result = rendering.render_document(source, output, mermaid_package=mermaid,
                                       chromium_executable=executable, document_path=document['path'],
                                       asset_root=source.parent)
    raw_manifest = safe(output / 'manifest.json').read_bytes()
    fresh(output / 'renderer-original-manifest.json', raw_manifest)
    stem = Path(document['path']).stem
    canonical = safe(output / (stem + '.html'))
    html_bytes = safe(output / 'document.html').read_bytes()
    fresh(canonical, html_bytes)
    result['artifacts'].append({'path': canonical.name, 'sha256': hashlib.sha256(html_bytes).hexdigest(),
                                'bytes': len(html_bytes)})
    result['canonicalHtmlFilename'] = canonical.name
    result['canonicalHtmlCopyIsByteIdentical'] = True
    result['originalRendererManifestSha256'] = hashlib.sha256(raw_manifest).hexdigest()
    result['manifestEnrichmentScope'] = 'Canonical filename and original renderer manifest pin only'
    manifest_path = safe(output / 'manifest.json')
    # Only renderer metadata is enriched. Preserve the original manifest bytes separately.
    with manifest_path.open('wb') as stream:
        stream.write(json_bytes(result))
    require(sha(source) == document['sha256'] and sha(collection) == args.collection_sha256 and
            guard.bootstrap() == runtime and capsule.verification_state(guard.SNAPSHOT) == snapshot_before,
            'Rendering input/runtime changed')
    pins = {'schema': 'spec-agent-render-pins/1', 'createdAt': datetime.now(timezone.utc).isoformat(),
            'documentId': document['documentId'], 'canonicalDocumentPath': document['path'],
            'source': str(source), 'sourceSha256': document['sha256'],
            'sourceSnapshotManifestSha256': guard.SNAPSHOT_SHA, 'referenceMode': 'source-only',
            'canonicalHtmlFilename': canonical.name, 'canonicalHtmlSha256': sha(canonical),
            'renderManifestSha256': sha(manifest_path), 'originalRendererManifestSha256': hashlib.sha256(raw_manifest).hexdigest(),
            'structure': result['structure'], 'display': result['display'], 'safety': result['safety'],
            'originalModified': result['originalModified'], 'collection': str(collection),
            'collectionSha256': args.collection_sha256, 'collectorDocument': document,
            'renderer': str(safe(rendering.__file__)), 'rendererSha256': sha(rendering.__file__),
            'helper': str(safe(__file__)), 'helperSha256': sha(__file__),
            'semanticApproval': 'TEXT_REVIEW_ONLY', 'visualFidelityVerified': False,
            'formalPercentage': None, 'originalApplicationExecuted': False, 'published': False}
    fresh(output / 'render-pins.json', json_bytes(pins))
    print(json.dumps({'documentId': document['documentId'], 'structure': result['structure']['status'],
                      'display': result['display']['status'], 'diagrams': len(result['diagrams']),
                      'layouts': len(result['layouts']), 'pinsSha256': sha(output / 'render-pins.json'),
                      'originalModified': result['originalModified']}, ensure_ascii=False))
    require(result['structure']['status'] == 'PASS' and result['display']['status'] == 'PASS' and
            not result['safety']['removed'] and not result['originalModified'], 'Derived render requires correction')

if __name__ == '__main__':
    main()

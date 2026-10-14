"""Prepare byte-preserving citation-root renderer wrapper; execute no render."""
import ast
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

WORK = Path(r'D:\開発\contextbase-evaluation\agents\spec-agent\.tmp\20261014-nenkin-high-01')
REPORT = Path(r'D:\開発\contextbase-evaluation\agents\spec-agent\report\20261014-nenkin-high-01')
BASE = WORK / 'render_reviewed_r05.py'
BASE_SHA = 'b3e69f6c2cbce03d8e1e2a833f14b31d7acb85c2ee9aae60fa25a1ae2c4641fe'
COLLECTOR = WORK / 'collect_reviewed_r10.py'
COLLECTOR_SHA = '173ce515ad44fc4a8b9e3198305cdb6552c3f6a9bdbff8de199824df5e952540'
TARGET = WORK / 'render_reviewed_r06.py'

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

assert sha(BASE) == BASE_SHA and sha(COLLECTOR) == COLLECTOR_SHA
text = BASE.read_bytes().decode('utf-8')
constants = '''
COLLECTOR = RUN / 'collect_reviewed_r10.py'
COLLECTOR_SHA = '173ce515ad44fc4a8b9e3198305cdb6552c3f6a9bdbff8de199824df5e952540'
FINAL_FOLDER_PREFIXES = ('md', 'html', 'PDF', 'Excel')
'''
needle = "HELPER_SHA = '9d5ec80c5fd3efe2044302104a64ff928777fd98d3cdd0e0c8ef0ff301ee5802'\n"
assert text.count(needle) == 1
text = text.replace(needle, needle + constants)
functions = '''
def citation_relative_path(value):
    from pathlib import PurePosixPath
    require(isinstance(value, str) and value and not any(ord(c) < 32 or ord(c) == 127 for c in value) and
            not any(c in value for c in '\\\\:<>"|?*'), 'Invalid canonical citation path')
    path = PurePosixPath(value)
    require(not path.is_absolute() and path.suffix == '.md' and path.as_posix() == value and
            all(part not in {'', '.', '..'} and not part.endswith((' ', '.')) for part in value.split('/')),
            'Citation path must be unchanged canonical relative Markdown')
    devices = {'con', 'prn', 'aux', 'nul', *['com' + str(n) for n in range(1, 10)], *['lpt' + str(n) for n in range(1, 10)]}
    require(not any(part.split('.')[0].casefold() in devices for part in path.parts),
            'Windows reserved citation segment')
    return path

def mirror_inventory(root, final_markdown_location):
    relative = citation_relative_path(final_markdown_location)
    expected_dirs = {p.as_posix() for p in relative.parents if p.as_posix() != '.'}
    files = {}
    def walk(directory):
        for entry in safe(directory).iterdir():
            entry = safe(entry)
            require(entry.is_relative_to(root) and entry != root, 'Citation mirror entry escaped root')
            name = entry.relative_to(root).as_posix()
            if entry.is_dir():
                require(name in expected_dirs, 'Unexpected directory in single-document citation mirror')
                walk(entry)
            else:
                require(entry.is_file() and name == final_markdown_location and name not in files,
                        'Citation mirror must contain only the exact approved Markdown file')
                files[name] = sha(entry)
    walk(safe(root))
    require(set(files) == {final_markdown_location}, 'Citation mirror document missing')
    return files

def prepare_citation_mirror(source, document, collection_sha, output):
    source = inside(source, RUN / 'collections')
    path = citation_relative_path(document['path'])
    require(sha(source) == document['sha256'] and isinstance(document['documentId'], str) and document['documentId'],
            'Citation mirror source must be the exact approved document')
    output = inside(output, RUN / 'renders')
    key = hashlib.sha256((document['documentId'] + '\\0' + collection_sha + '\\0' + str(output) + '\\0' + path.as_posix()).encode('utf-8')).hexdigest()
    owner = inside(RUN / 'render-citation-roots' / key, RUN / 'render-citation-roots')
    root = inside(owner / 'root', owner)
    require(not owner.exists() and not root.exists(), 'Fresh owned single-document citation mirror required')
    location = 'md/' + path.as_posix()
    mirror = inside(root / location, root)
    require(not output.is_relative_to(root) and not root.is_relative_to(output), 'Render output overlaps citation mirror')
    root.mkdir(parents=True, exist_ok=False)
    mirror.parent.mkdir(parents=True, exist_ok=True)
    source_bytes = safe(source).read_bytes()
    require(hashlib.sha256(source_bytes).hexdigest() == document['sha256'], 'Original source drift before mirror copy')
    fresh(mirror, source_bytes)
    expected = {location: document['sha256']}
    require(mirror.read_bytes() == source_bytes and mirror_inventory(root, location) == expected and
            sha(source) == document['sha256'], 'Citation mirror copy or original source changed')
    return {'schema': 'spec-agent-render-citation-mirror/1', 'owner': str(owner),
            'root': str(root), 'mirrorFile': str(mirror), 'mirrorSha256': document['sha256'],
            'originalSource': str(source), 'originalSourceSha256': document['sha256'],
            'canonicalDocumentPath': document['path'], 'finalMarkdownLocation': location,
            'finalFolderPrefixes': list(FINAL_FOLDER_PREFIXES), 'inventory': expected,
            'scope': 'ONE_BYTE_IDENTICAL_APPROVED_MARKDOWN_NO_OTHER_ARTIFACTS',
            'businessTextRewritten': False, 'additionalSourceOrAssetReadsAuthorized': False}

def verify_citation_mirror(mapping):
    root = inside(mapping['root'], RUN / 'render-citation-roots')
    original = inside(mapping['originalSource'], RUN / 'collections')
    mirror = inside(mapping['mirrorFile'], root)
    require(mapping['schema'] == 'spec-agent-render-citation-mirror/1' and
            mapping['finalFolderPrefixes'] == list(FINAL_FOLDER_PREFIXES) and
            mirror == safe(root / mapping['finalMarkdownLocation']) and
            mapping['finalMarkdownLocation'] == 'md/' + citation_relative_path(mapping['canonicalDocumentPath']).as_posix() and
            mapping['inventory'] == {mapping['finalMarkdownLocation']: mapping['mirrorSha256']} and
            mapping['mirrorSha256'] == mapping['originalSourceSha256'], 'Citation mirror mapping changed')
    require(sha(original) == mapping['originalSourceSha256'] and sha(mirror) == mapping['mirrorSha256'] and
            original.read_bytes() == mirror.read_bytes() and
            mirror_inventory(root, mapping['finalMarkdownLocation']) == mapping['inventory'],
            'Citation mirror/source byte equality or exclusive inventory changed')

'''
needle = 'def main():\n'
assert text.count(needle) == 1
text = text.replace(needle, functions + needle)
needle = "    matched = [doc for doc in collected['documents'] if doc['documentId'] == args.document_id]\n"
insert = '''    require(sha(COLLECTOR) == COLLECTOR_SHA and
            collected['pinnedInputs'].get(str(safe(COLLECTOR))) == COLLECTOR_SHA and
            collected['runtimeProvenance'] == runtime,
            'Collection must use the exact current collector and frozen runtime')
'''
assert text.count(needle) == 1
text = text.replace(needle, insert + needle)
needle = '''    result = rendering.render_document(source, output, mermaid_package=mermaid,
                                       chromium_executable=executable, document_path=document['path'],
                                       asset_root=source.parent)
'''
replacement = '''    mirror_mapping = prepare_citation_mirror(source, document, args.collection_sha256, output)
    verify_citation_mirror(mirror_mapping)
    mirror_source, mirror_root = safe(mirror_mapping['mirrorFile']), safe(mirror_mapping['root'])
    result = rendering.render_document(mirror_source, output, mermaid_package=mermaid,
                                       chromium_executable=executable, document_path=document['path'],
                                       asset_root=mirror_root)
    verify_citation_mirror(mirror_mapping)
    require(result['source'] == str(mirror_source) and result['sourceSha256'] == document['sha256'],
            'Frozen renderer actual mirror source provenance differs')
'''
assert text.count(needle) == 1
text = text.replace(needle, replacement)
needle = "    result['manifestEnrichmentScope'] = 'Canonical filename and original renderer manifest pin only'\n"
replacement = "    mirror_mapping['beforeAfterByteEqualityVerified'] = True\n    result['citationMirror'] = mirror_mapping\n    result['manifestEnrichmentScope'] = 'Canonical filename, untouched original manifest pin and explicit byte-identical citation mirror mapping only'\n"
assert text.count(needle) == 1
text = text.replace(needle, replacement)
needle = "            guard.bootstrap() == runtime and capsule.verification_state(guard.SNAPSHOT) == snapshot_before,\n"
replacement = "            guard.bootstrap() == runtime and capsule.verification_state(guard.SNAPSHOT) == snapshot_before and\n            sha(COLLECTOR) == COLLECTOR_SHA,\n"
assert text.count(needle) == 1
text = text.replace(needle, replacement)
needle = "    pins = {'schema': 'spec-agent-render-pins/1', 'createdAt': datetime.now(timezone.utc).isoformat(),\n"
assert text.count(needle) == 1
text = text.replace(needle, "    verify_citation_mirror(mirror_mapping)\n" + needle)
needle = "            'source': str(source), 'sourceSha256': document['sha256'],\n"
replacement = needle + "            'rendererSource': str(mirror_source), 'rendererSourceSha256': document['sha256'],\n            'citationMirror': mirror_mapping,\n"
assert text.count(needle) == 1
text = text.replace(needle, replacement)
ast.parse(text)
assert not TARGET.exists() and sha(BASE) == BASE_SHA and sha(COLLECTOR) == COLLECTOR_SHA
with TARGET.open('xb') as stream:
    stream.write(text.encode('utf-8'))
assert sha(BASE) == BASE_SHA and sha(COLLECTOR) == COLLECTOR_SHA
result = {
    'schema': 'spec-agent-render-citation-wrapper-preparation/1',
    'createdUtc': datetime.now(timezone.utc).isoformat(),
    'status': 'CODE_PREPARED_SYNTHETIC_AND_INDEPENDENT_AUDIT_PENDING',
    'base': {'path': str(BASE), 'sha256': BASE_SHA, 'unchanged': True},
    'candidate': {'path': str(TARGET), 'sha256': sha(TARGET)},
    'collector': {'path': str(COLLECTOR), 'sha256': COLLECTOR_SHA, 'unchanged': True},
    'scope': 'Fresh exact-one-byte-identical-MD mirror at final md location inside a four-format citation root; original source and actual renderer mirror source both explicit; no frozen renderer mutation.',
    'actualDocumentsOrSourceOrAuthorRecordsRead': False,
    'actualMirrorCreated': False, 'actualRendererOrBrowserOrProviderOrMarkerExecuted': False,
    'actualNativeQualification': False, 'frozenCoreModified': False, 'published': False,
    'script': {'path': str(Path(__file__)), 'sha256': sha(Path(__file__))}
}
receipt = REPORT / 'independent-audit/render-citation-r06-preparation-r01.json'
with receipt.open('x', encoding='utf-8', newline='\n') as stream:
    json.dump(result, stream, ensure_ascii=False, indent=2)
    stream.write('\n')
print(json.dumps({'candidate': str(TARGET), 'sha256': sha(TARGET), 'receipt': str(receipt), 'receiptSha256': sha(receipt)}, ensure_ascii=False))

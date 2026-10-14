"""AST-isolated renderer mirror probes using owned synthetic Markdown only."""
import ast
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

WORK = Path(r'D:\開発\contextbase-evaluation\agents\spec-agent\.tmp\20261014-nenkin-high-01')
REPORT = Path(r'D:\開発\contextbase-evaluation\agents\spec-agent\report\20261014-nenkin-high-01')
CANDIDATE = WORK / 'render_reviewed_r06.py'
CANDIDATE_SHA = 'eada05d737ed3bbf9bf0173681eb117024c9a1fa49d778040de51bdd43b40b02'
BASE = WORK / 'render_reviewed_r05.py'
BASE_SHA = 'b3e69f6c2cbce03d8e1e2a833f14b31d7acb85c2ee9aae60fa25a1ae2c4641fe'
TOY = REPORT / 'render-citation-r06-toy-r01'

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def require(value, message):
    if not value:
        raise ValueError(message)

def safe(value):
    path = Path(value).absolute()
    for node in (path, *path.parents):
        if node.exists():
            require(not node.is_symlink() and not (getattr(node.lstat(), 'st_file_attributes', 0) & 0x400), 'Toy reparse refused')
    return path.resolve()

assert sha(CANDIDATE) == CANDIDATE_SHA and sha(BASE) == BASE_SHA and not TOY.exists()
tree = ast.parse(CANDIDATE.read_text(encoding='utf-8-sig'))
names = {'inside', 'fresh', 'citation_relative_path', 'mirror_inventory', 'prepare_citation_mirror', 'verify_citation_mirror'}
selected = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in names]
assert {node.name for node in selected} == names
namespace = {'Path': Path, 'hashlib': hashlib, 'RUN': TOY, 'safe': safe, 'sha': sha, 'require': require,
             'FINAL_FOLDER_PREFIXES': ('md', 'html', 'PDF', 'Excel')}
exec(compile(ast.Module(body=selected, type_ignores=[]), '<actual-candidate-functions-only>', 'exec'), namespace)
TOY.mkdir()
tests = []

def positive(name, action):
    action()
    tests.append({'name': name, 'passed': True})

def negative(name, action):
    try:
        action()
    except ValueError as error:
        tests.append({'name': name, 'passed': True, 'typedRejection': str(error)})
    else:
        raise AssertionError('Expected candidate refusal: ' + name)

for index, spelling in enumerate(('basic/ログイン.md', 'tables/SPACE NAME.md', 'index.md')):
    payload = b'\xef\xbb\xbf' + ('# Synthetic fixture only\r\n日本語と空白 ' + str(index) + '\r\n[fixture](../detailed/example.md)\r\n').encode('utf-8')
    source = TOY / 'collections' / str(index) / spelling
    source.parent.mkdir(parents=True)
    source.write_bytes(payload)
    document = {'documentId': 'SYNTHETIC-' + str(index), 'path': spelling, 'sha256': sha(source)}
    output = TOY / 'renders' / str(index)
    mapping = namespace['prepare_citation_mirror'](source, document, 'a' * 64, output)
    def check_copy():
        assert Path(mapping['mirrorFile']).read_bytes() == payload == source.read_bytes()
        assert mapping['finalMarkdownLocation'] == 'md/' + spelling
        assert mapping['inventory'] == {'md/' + spelling: sha(source)}
        namespace['verify_citation_mirror'](mapping)
    positive('exact BOM CRLF Unicode and final md citation origin ' + str(index), check_copy)
    negative('same owned citation mirror cannot be reused ' + str(index),
             lambda: namespace['prepare_citation_mirror'](source, document, 'a' * 64, output))
    bad = dict(mapping, originalSource=str(TOY / 'unowned-source.md'))
    negative('original source outside collections refused ' + str(index), lambda: namespace['verify_citation_mirror'](bad))
    bad = dict(mapping, root=str(TOY / 'outside-mirror'))
    negative('mirror root outside owned citation roots refused ' + str(index), lambda: namespace['verify_citation_mirror'](bad))
    mirror = Path(mapping['mirrorFile'])
    mirror.write_bytes(payload + b'changed')
    negative('mirror byte drift refused ' + str(index), lambda: namespace['verify_citation_mirror'](mapping))
    mirror.write_bytes(payload)
    extra = Path(mapping['root']) / 'extra.png'
    extra.write_bytes(b'synthetic-only')
    negative('additional mirror asset refused before it can be used ' + str(index), lambda: namespace['verify_citation_mirror'](mapping))
    extra.unlink()
    source.write_bytes(payload + b'changed')
    negative('original canonical source drift refused ' + str(index), lambda: namespace['verify_citation_mirror'](mapping))
    source.write_bytes(payload)
    namespace['verify_citation_mirror'](mapping)

for spelling in ('../escape.md', '/absolute.md', 'C:/escape.md', 'a//x.md', 'a/./x.md', 'a/../x.md',
                 'a/NUL.md', 'a/com9.md', 'a/file .md/leaf.md', 'a/file./leaf.md', 'a/leaf.MD', 'a/leaf.md:ads', 'a/leaf?x.md', 'a/leaf\x00.md'):
    if spelling == 'a/file .md/leaf.md':
        positive('valid internal filename space is retained', lambda: namespace['citation_relative_path'](spelling))
    else:
        negative('invalid canonical citation spelling ' + repr(spelling), lambda value=spelling: namespace['citation_relative_path'](value))

source = TOY / 'collections' / '0' / 'basic/ログイン.md'
document = {'documentId': 'OUTSIDE', 'path': 'basic/ログイン.md', 'sha256': sha(source)}
negative('render output outside owned renders refused', lambda: namespace['prepare_citation_mirror'](source, document, 'a' * 64, TOY / 'outside-output'))
negative('copy source SHA mismatch refused', lambda: namespace['prepare_citation_mirror'](source, dict(document, sha256='b' * 64), 'a' * 64, TOY / 'renders' / 'wrong-sha'))
assert sha(CANDIDATE) == CANDIDATE_SHA and sha(BASE) == BASE_SHA
report = {
    'schema': 'spec-agent-render-citation-synthetic-probes/1',
    'createdUtc': datetime.now(timezone.utc).isoformat(),
    'status': 'AST_ISOLATED_SYNTHETIC_MIRROR_ONLY_PASS',
    'candidate': {'path': str(CANDIDATE), 'sha256': CANDIDATE_SHA},
    'base': {'path': str(BASE), 'sha256': BASE_SHA, 'unchanged': True},
    'testCount': len(tests), 'passedCount': len(tests), 'tests': tests,
    'actualCandidateFunctionsAstExtracted': sorted(names),
    'toyRoot': str(TOY), 'fixtureCount': 3,
    'scopeLimitations': {
        'guardSafeAndHashAreOwnedToyFunctions': True, 'realReparseCreationTested': False,
        'realApprovedDocumentsOrCollectionRead': False, 'frozenRendererImportedOrRun': False,
        'wrapperModuleImported': False, 'actualMirrorCreatedForRun': False,
        'actualBrowserProviderMarkersExecuted': False, 'nativeQualification': False,
        'wholeRuntimeSourceGuardsExecuted': False, 'atomicOrRaceFreeProof': False
    },
    'script': {'path': str(Path(__file__)), 'sha256': sha(Path(__file__))}
}
target = REPORT / 'independent-audit/render-citation-r06-synthetic-probes-r01.json'
with target.open('x', encoding='utf-8', newline='\n') as stream:
    json.dump(report, stream, ensure_ascii=False, indent=2)
    stream.write('\n')
print(json.dumps({'audit': str(target), 'sha256': sha(target), 'count': len(tests)}, ensure_ascii=False))

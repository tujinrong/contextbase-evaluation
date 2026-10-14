"""Create fresh pinned technical helper code; never synthesize manuscript or business HTML."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import py_compile

parser = argparse.ArgumentParser()
parser.add_argument('--document', required=True, type=Path)
parser.add_argument('--draft-result', required=True, type=Path)
parser.add_argument('--review-handoff', required=True, type=Path)
parser.add_argument('--runtime-receipt', required=True, type=Path)
parser.add_argument('--output', required=True, type=Path)
parser.add_argument('--pin-report', required=True, type=Path)
args = parser.parse_args()
report = Path(__file__).resolve().parent
repo = report.parents[4]
base = repo / 'agents/reverse-agent/.tmp/20261013-rerun-12h/source-only'
draft_root = repo / 'test-project1/spec-analysis/CSharp_ASPNET/20261013-rerun-12h/source-only/drafts'
document = args.document.resolve()
relative = document.relative_to(draft_root).as_posix()
role = 'basic' if relative.startswith('search-basic-') else 'detail' if relative.startswith('search-detail-') else None
expected_suffix = '基本設計書/01_学生検索画面.md' if role == 'basic' else '詳細仕様書/CSharp_ASPNET/01_学生検索画面.md'
if role is None or '/'.join(relative.split('/')[1:]) != expected_suffix:
    raise ValueError('fresh helper builder accepts the exact canonical source-only search names')
draft_bytes = args.draft_result.read_bytes()
draft = json.loads(draft_bytes)
document_sha = hashlib.sha256(document.read_bytes()).hexdigest()
review_handoff_bytes = args.review_handoff.read_bytes()
review_handoff = json.loads(review_handoff_bytes)
verified_path = args.review_handoff.parent / 'review-verified.json'
verified_bytes = verified_path.read_bytes()
verified = json.loads(verified_bytes)
cap_sha = '2f64e2211b1fcd7850203927fc75b5a7f2ce37457cc2afe88c8065d9f931273b'
if (draft['contentSha256'] != document_sha or review_handoff['documentSha256'] != document_sha or
    Path(review_handoff['documentFile']).resolve() != document or review_handoff['snapshot']['manifestSha256'] != cap_sha or
    review_handoff.get('referenceMode') != 'source-only' or review_handoff.get('approved') is not True or
    verified.get('approved') is not True or verified.get('findings') != [] or
    hashlib.sha256(verified_bytes).hexdigest() != review_handoff['reviewSha256']):
    raise ValueError('fresh helper parent must have exact approved source-only review')
receipt_bytes = args.runtime_receipt.read_bytes()
receipt_sha = hashlib.sha256(receipt_bytes).hexdigest()
if args.runtime_receipt.resolve() != report / 'runtime-code-source-07.json' or receipt_sha != '0b2f2aff745a7e32394ecc5cde4c1a849ad2d5a32c7fa4339af2e7cdecd48906':
    raise ValueError('future projection helper must use the approved source07 freeze')
base_helper = report / 'prepare_state_projection_detail07_v5.py'
base_bytes = base_helper.read_bytes()
if hashlib.sha256(base_bytes).hexdigest() != '6fb6aaabaea7822aa6e74a7847c1d175f7d0b949f4df32b68f9b21b1c868237e':
    raise ValueError('independently reviewed v5 technical base differs')
code = base_bytes.decode('utf-8')
def replace_once(old, new, count=1):
    global code
    if code.count(old) != count:
        raise ValueError('technical helper replacement shape differs: ' + old[:45])
    code = code.replace(old, new)
replace_once('search-detail-07/詳細仕様書/CSharp_ASPNET/01_学生検索画面.md', relative)
replace_once('jobs/search-detail-07-review/review-handoff.json', args.review_handoff.resolve().relative_to(base).as_posix())
replace_once('jobs/search-detail-07-review/review-verified.json', verified_path.resolve().relative_to(base).as_posix())
replace_once('85cddae02cf89e6e92d84ecc7709a118f298ca114bf104115f1be8ae47d62b82', document_sha)
replace_once('08ef7ff07480f3568988b56511d3a9a09769b83635d98af430662bac6b682f0a', hashlib.sha256(review_handoff_bytes).hexdigest())
replace_once('b392b1a459cf13286c7e546ca3d4722b9dfcf70752a9508c0d2836ae5aae79ab', hashlib.sha256(verified_bytes).hexdigest())
replace_once('runtime-code-source-06.json', 'runtime-code-source-07.json')
replace_once('ba00e60167417923a2630677374b67963ae09155aa647d0a7dfc02ac9d380c8f', receipt_sha)
replace_once('runtime-code/source-06/src', 'runtime-code/source-07/src')
code = code.replace('detail07', document.parent.parent.name if role == 'basic' else relative.split('/')[0])
if role == 'basic':
    replace_once('{"詳細仕様書/CSharp_ASPNET/01_学生検索画面.md"}', '{"基本設計書/01_学生検索画面.md"}')
    replace_once('startswith("search-detail-")', 'startswith("search-basic-")')
replace_once('import hashlib\n', 'import hashlib\nimport importlib\nimport importlib.util\n')
replace_once('hashlib.sha256(p.read_bytes()).hexdigest()', 'hashlib.sha256(capsule.safe_path(p).read_bytes()).hexdigest()', 2)
replace_once('capsule.sha256((original_root / entry["path"]).read_bytes())',
             'capsule.sha256(capsule.safe_path(original_root / entry["path"]).read_bytes())', 2)
import_guard = '''critical_module_names = ("contextbase.ai.capsule", "contextbase.ai.workflow", "contextbase.ai.provider", "contextbase.ai.prompts", "contextbase.ai.schemas", "contextbase.ai.validation")
def runtime_import_pin():
    loaded = {name: str(capsule.safe_path(Path(importlib.import_module(name).__file__))) for name in critical_module_names}
    resolved = {name: str(capsule.safe_path(Path(importlib.util.find_spec(name).origin))) for name in freeze["imports"]}
    expected = {}
    for name in critical_module_names:
        relative_module = "/".join(name.split(".")) + ".py"
        if relative_module not in freeze["files"]:
            raise ValueError("critical module absent from complete frozen receipt")
        exact = str(capsule.safe_path(runtime / relative_module))
        if name in freeze["imports"] and freeze["imports"][name] != exact:
            raise ValueError("critical import receipt differs from exact inventoried file")
        expected[name] = exact
    if resolved != freeze["imports"] or loaded != expected:
        raise ValueError("actual critical/all resolved imports differ from exact frozen files")
    return {"actualCriticalImports": loaded, "allResolvedFrozenImports": resolved, "expectedCriticalImports": expected}
runtime_imports_before = runtime_import_pin()
'''
replace_once('drafts = []\n', import_guard + 'drafts = []\n')
replace_once('job.mkdir(parents=True)\n', '''if capsule.sha256(capsule.material_path(args.snapshot, "manifest.json").read_bytes()) != "2f64e2211b1fcd7850203927fc75b5a7f2ce37457cc2afe88c8065d9f931273b" or capsule.verification_state(args.snapshot) != state:
    raise ValueError("fixed capsule changed before projection AI input")
job.mkdir(parents=True)
''')
replace_once('workflow._same_snapshot(args.snapshot, state)\n', '''workflow._same_snapshot(args.snapshot, state)
if capsule.sha256(capsule.material_path(args.snapshot, "manifest.json").read_bytes()) != "2f64e2211b1fcd7850203927fc75b5a7f2ce37457cc2afe88c8065d9f931273b" or capsule.verification_state(args.snapshot) != state:
    raise ValueError("fixed capsule changed after projection AI response")
if runtime_import_pin() != runtime_imports_before:
    raise ValueError("actual frozen imports changed during projection")
''')
replace_once('"approvedCanonicalReview": approved_review_pin,', '"approvedCanonicalReview": approved_review_pin, "runtimeImportPin": runtime_imports_before,', 2)
with args.output.open('x', encoding='utf-8', newline='\n') as stream:
    stream.write(code)
py_compile.compile(str(args.output), doraise=True)
pin = {'classification': 'FRESH_CODE_ONLY_PROJECTION_HELPER_PARENT_RUNTIME_PIN_NOT_PROVIDER_EXECUTION',
       'createdAt': datetime.now(timezone.utc).isoformat(), 'helperFile': str(args.output.resolve()),
       'helperSha256': hashlib.sha256(args.output.read_bytes()).hexdigest(),
       'baseHelperSha256': hashlib.sha256(base_bytes).hexdigest(), 'documentFile': str(document),
       'documentSha256': document_sha, 'draftResultSha256': hashlib.sha256(draft_bytes).hexdigest(),
       'reviewHandoffSha256': hashlib.sha256(review_handoff_bytes).hexdigest(),
       'verifiedReviewSha256': hashlib.sha256(verified_bytes).hexdigest(), 'snapshotManifestSha256': cap_sha,
       'runtimeReceiptSha256': receipt_sha, 'compiled': True, 'providerExecuted': False,
       'nativeApproval': False, 'semanticProseAssembledByPython': False}
with args.pin_report.open('x', encoding='utf-8', newline='\n') as stream:
    json.dump(pin, stream, ensure_ascii=False, indent=2)
    stream.write('\n')
print(json.dumps(pin, ensure_ascii=False))

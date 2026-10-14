"""Independent candidate geometry only; frozen renderer and immutable AI MD."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, importlib.util, json, os, sys, subprocess, time, faulthandler

HERE = Path(__file__).resolve().parent
AGENT = Path(r'D:\開発\contextbase-evaluation\agents\reverse-agent')
REPO = AGENT.parents[1]
REPORT = AGENT / 'test-report/20261013-rerun-12h'
AUTHOR = AGENT / '.tmp/20261013-rerun-12h/training-assisted'
RECEIPT = REPORT / 'training-assisted/runtime-code-assisted-10.json'
RECEIPT_SHA = '54e693b2382e1520710d192e8a8b0b6b6eb97bbae1e70c1dbc36ff1e36f279be'
FROZEN = AUTHOR / 'runtime-code/assisted-10/src'
CAP = AUTHOR / 'snapshot/manifest.json'
CAP_SHA = 'e76a6c40e8927011fff9145d5f5ab2fa94ad89acefc9a03bbad0cbf09b85a0e7'
ROOT = REPO / 'test-project1/spec-analysis/CSharp_ASPNET/20261013-rerun-12h/training-assisted/drafts/revision-search-basic-r07'
RELATIVE = '基本設計書/01_学生検索画面.md'
SOURCE = ROOT / RELATIVE
SOURCE_SHA = 'c954ae728a0a51040c2ab99dc0d20fc4416955483a158269e5014df7bd9e122b'
DRAFT = AUTHOR / 'jobs/revision-search-basic-r07/draft-result.json'
DRAFT_SHA = '2516ab6967ae2bb9498c410be725983c1a24eeb401c147882866501eb4ceb52e'
ID = 'CSHARP_ASPNET-BAS-STU-01'
DEST = HERE / 'render-r18'
DEADLINE = datetime.fromisoformat('2026-10-13T20:15:58+00:00')

def safe(p):
    p = Path(os.path.abspath(p))
    for q in (p, *p.parents):
        if q.is_symlink() or (q.exists() and getattr(q.lstat(), 'st_file_attributes', 0) & 0x400):
            raise ValueError('Linked path rejected')
    return p

def sha(p): return hashlib.sha256(safe(p).read_bytes()).hexdigest()
def inventory(root):
    root = safe(root)
    result = {}
    def visit(directory):
        for p in sorted(safe(directory).iterdir()):
            p = safe(p)
            if p.name == '__pycache__' or p.suffix in {'.pyc', '.pyo'}: continue
            if p.is_dir(): visit(p)
            elif p.is_file(): result[p.relative_to(root).as_posix()] = sha(p)
            else: raise ValueError('Unexpected frozen runtime entry')
    visit(root)
    return result

def stage(name): print(json.dumps({'stage': name, 'utc': datetime.now(timezone.utc).isoformat()}), flush=True)

def worker():
    faulthandler.enable(); faulthandler.dump_traceback_later(90, repeat=True)
    assert datetime.now(timezone.utc) < DEADLINE
    stage('fixed-input-and-frozen-runtime-check')
    before = {str(p): sha(p) for p in [SOURCE, DRAFT, CAP, RECEIPT, Path(__file__)]}
    assert before[str(SOURCE)] == SOURCE_SHA and before[str(DRAFT)] == DRAFT_SHA
    assert before[str(CAP)] == CAP_SHA and before[str(RECEIPT)] == RECEIPT_SHA
    receipt = json.loads(safe(RECEIPT).read_text(encoding='utf-8'))
    assert safe(receipt['destination']) == safe(FROZEN)
    assert receipt['fileCount'] == 126 and inventory(FROZEN) == receipt['files']
    draft = json.loads(safe(DRAFT).read_text(encoding='utf-8'))
    assert draft['contentSha256'] == SOURCE_SHA and draft['path'] == RELATIVE and draft['documentId'] == ID
    assert draft['referenceMode'] == 'training-assisted' and draft['aiAuthored'] is True
    assert draft['snapshot']['manifestSha256'] == CAP_SHA
    sys.path.insert(0, str(FROZEN))
    from contextbase.ai.rendering import render_document
    resolved = {}
    assert len(receipt['imports']) == 13
    for name, path in receipt['imports'].items():
        expected = safe(path); spec = importlib.util.find_spec(name)
        assert spec and safe(spec.origin) == expected and expected.is_relative_to(safe(FROZEN))
        rel = expected.relative_to(safe(FROZEN)).as_posix()
        assert sha(expected) == receipt['files'][rel]
        resolved[name] = {'path': str(expected), 'sha256': sha(expected)}
    loaded = {}
    for name, pin in receipt['renderImports'].items():
        module = sys.modules[name]; expected = safe(pin['path'])
        assert safe(module.__file__) == expected and safe(module.__spec__.origin) == expected
        assert safe(importlib.util.find_spec(name).origin) == expected and sha(expected) == pin['sha256']
        loaded[name] = {'path': str(expected), 'sha256': pin['sha256']}
    assert not safe(DEST).exists()
    stage('trusted-static-render-start')
    result = render_document(SOURCE, DEST, document_path=RELATIVE, asset_root=ROOT,
        mermaid_package=Path(os.environ['CONTEXTBASE_MERMAID_PACKAGE']),
        chromium_executable=Path(os.environ['CONTEXTBASE_CHROMIUM_EXE']))
    stage('render-complete-input-and-runtime-after-check')
    assert inventory(FROZEN) == receipt['files'] and all(sha(p) == h for p, h in before.items())
    for name, pin in resolved.items():
        assert safe(importlib.util.find_spec(name).origin) == safe(pin['path']) and sha(pin['path']) == pin['sha256']
    for name, pin in loaded.items():
        assert safe(sys.modules[name].__file__) == safe(pin['path']) and sha(pin['path']) == pin['sha256']
    canonical = DEST / (SOURCE.stem + '.html')
    canonical.write_bytes((DEST / 'document.html').read_bytes())
    result.update({'documentId': ID, 'canonicalDocumentPath': RELATIVE,
        'canonicalHtmlFilename': canonical.name, 'canonicalHtmlSha256': sha(canonical),
        'sourceSnapshotManifestSha256': CAP_SHA, 'draftResultSha256': DRAFT_SHA,
        'referenceMode': 'training-assisted', 'rendererRuntimeReceipt': str(RECEIPT),
        'rendererRuntimeReceiptSha256': RECEIPT_SHA, 'rendererRuntimeFileCount': 126,
        'rendererRuntimeLabel': 'r18', 'frozenRenderImports': loaded, 'frozenResolvedImports': resolved,
        'inputBeforeAfterUnchanged': True, 'inputPins': before, 'originalApplicationExecuted': False,
        'visualFidelityVerified': False, 'formalRubricEvaluated': False, 'stateProjectionIncluded': False,
        'canonicalIndependentSemanticReviewApprovedHere': False, 'wholeDocumentApproval': False,
        'adoptionApproval': False, 'published': False, 'createdAt': datetime.now(timezone.utc).isoformat()})
    (DEST / 'render-pins.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'destination': str(DEST), 'structure': result['structure']['status'],
        'display': result['display']['status'], 'diagrams': len(result['diagrams']), 'layouts': len(result['layouts']),
        'renderPinsSha256': sha(DEST / 'render-pins.json'),
        'errors': [{'id': d['id'], 'error': d.get('error')} for d in result['diagrams'] if d['status'] != 'PASS']}, ensure_ascii=False), flush=True)

def main():
    if '--worker' in sys.argv: return worker()
    remaining = (DEADLINE - datetime.now(timezone.utc)).total_seconds()
    if remaining <= 0: raise RuntimeError('Deadline reached')
    out = HERE / 'worker.json'; assert not out.exists()
    started = time.monotonic(); timeout = min(240, remaining)
    process = subprocess.Popen([sys.executable, str(Path(__file__).resolve()), '--worker'],
        creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
    stage('owned-worker-' + str(process.pid))
    code = None; status = 'UNKNOWN'
    try:
        code = process.wait(timeout=timeout); status = 'COMPLETE' if code == 0 else 'FAILED'
    except subprocess.TimeoutExpired:
        status = 'TIMED_OUT'
        if process.poll() is None:
            subprocess.run(['taskkill', '/PID', str(process.pid), '/T', '/F'], capture_output=True, timeout=20)
        process.wait(timeout=15)
    out.write_text(json.dumps({'status': status, 'ownedWorkerPid': process.pid, 'exitCode': code,
        'elapsedSeconds': round(time.monotonic() - started, 3), 'timeoutSeconds': timeout,
        'scope': 'IMMUTABLE_CANDIDATE_STATIC_GEOMETRY_ONLY', 'applicationExecuted': False,
        'providerExecuted': False, 'published': False}, indent=2) + '\n', encoding='utf-8')
    return 0 if status == 'COMPLETE' else 1

if __name__ == '__main__': sys.exit(main() or 0)
